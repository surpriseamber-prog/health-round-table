import gradio as gr
import requests
import time
import hashlib
import sqlite3
import json
import os
from datetime import datetime

API_KEY = "939d10536ea749c2ac9f1ae783335eaa.L8GP6pNpV7FVESvej9RAoDTT"
BASE_URL = "https://ollama.com"
headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

AVATARS = {
    "synthesizer": "https://raw.githubusercontent.com/surpriseamber-prog/health-round-table/main/static/avatars/avatar_synthesizer.jpg",
    "dr_heart": "https://raw.githubusercontent.com/surpriseamber-prog/health-round-table/main/static/avatars/avatar_dr_heart.jpg",
    "nutri": "https://raw.githubusercontent.com/surpriseamber-prog/health-round-table/main/static/avatars/avatar_nutri.jpg",
    "longevity": "https://raw.githubusercontent.com/surpriseamber-prog/health-round-table/main/static/avatars/avatar_longevity.jpg",
    "holistics": "https://raw.githubusercontent.com/surpriseamber-prog/health-round-table/main/static/avatars/avatar_holistics.jpg",
    "medi_suppi": "https://raw.githubusercontent.com/surpriseamber-prog/health-round-table/main/static/avatars/avatar_medi_suppi.jpg",
}

def avatar_html(key, label, emoji):
    url = AVATARS[key]
    return f'''<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
    <img src="{url}" width="48" height="48" style="border-radius:50%;object-fit:cover;">
    <span style="font-size:1.1em;font-weight:600;">{label}</span>
    <span style="font-size:1.2em;">{emoji}</span>
</div>'''

# --- SQLite Database ---
DB_PATH = os.path.join(os.path.dirname(__file__), "debates.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS debates (
            id TEXT PRIMARY KEY,
            case_text TEXT,
            goals TEXT,
            constraints TEXT,
            model TEXT,
            supplements TEXT,
            results TEXT,
            timestamp TEXT,
            views INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

def make_id():
    return hashlib.md5(str(time.time()).encode()).hexdigest()[:8]

def save_debate(case, goals, constraints, model, supplements, results):
    did = make_id()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO debates (id, case_text, goals, constraints, model, supplements, results, timestamp, views)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
    """, (did, case, goals, constraints, model, supplements, json.dumps(results), datetime.now().strftime("%b %d, %Y %I:%M %p")))
    conn.commit()
    conn.close()
    return did

def get_debate(did):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT * FROM debates WHERE id = ?", (did,)).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0], "case": row[1], "goals": row[2], "constraints": row[3],
        "model": row[4], "supplements": row[5],
        "results": json.loads(row[6]), "timestamp": row[7], "views": row[8]
    }

def increment_views(did):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE debates SET views = views + 1 WHERE id = ?", (did,))
    conn.commit()
    conn.close()

def get_recent():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT * FROM debates ORDER BY views DESC LIMIT 10").fetchall()
    conn.close()
    return [(r[0], {"case": r[1], "goals": r[2], "constraints": r[3], "model": r[4], "supplements": r[5], "results": json.loads(r[6]), "timestamp": r[7], "views": r[8]}) for r in rows]

def build_feed():
    debates = get_recent()
    if not debates:
        return "*No debates yet — run a case above!*"
    lines = ["### 📖 Recent Debates\n", "| ID | Case | Date | Views |", "|----|------|------|-------|"]
    for did, d in debates:
        prev = (d["case"][:50]+"...") if len(d["case"])>50 else d["case"]
        prev = prev.replace("\n"," ")
        lines.append(f"| `{did}` | {prev} | {d['timestamp']} | {d['views']} |")
    return "\n".join(lines)

# --- API ---
def chat(model, system, user_message):
    payload = {"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user_message}], "stream": False}
    r = requests.post(f"{BASE_URL}/api/chat", headers=headers, json=payload)
    if r.status_code != 200:
        raise Exception(f"API Error {r.status_code}")
    return r.json()["message"]["content"]

def run_round_table(case, goals, constraints, model_choice, supplements):
    ctx = ""
    if goals: ctx += f"\n\nPATIENT GOALS:\n{goals}"
    if constraints: ctx += f"\n\nIMPORTANT CONSTRAINTS:\n{constraints}"

    def ask(sys, prompt):
        try: return chat(model_choice, sys, prompt)
        except Exception as e: return f"Error: {e}"

    h = f"You are Dr. Heart, cardiologist. Focus on BP, cholesterol, circulation.{ctx}\nBullet points."
    dr = ask(h, f"Analyze: {case}")

    n = f"You are Nutri, functional nutritionist. Build on Dr. Heart's foundation.{ctx}\nBullet points."
    nu = ask(n, f"React:\n=== DR. HEART ===\n{dr}\nCase: {case}")

    l = f"You are Longevity, anti-aging researcher.{ctx}\nBullet points."
    lo = ask(l, f"Build:\n=== DR. HEART ===\n{dr}\n=== NUTRI ===\n{nu}\nCase: {case}")

    ho_sys = f"You are Holistics, integrative medicine.{ctx}\nBullet points."
    ho = ask(ho_sys, f"Build:\n=== DR. HEART ===\n{dr}\n=== NUTRI ===\n{nu}\n=== LONGEVITY ===\n{lo}\nCase: {case}")

    s = f"You are the Synthesizer, medical professor. Give exactly 3 numbered recommendations.{ctx}"
    sy = ask(s, f"Consensus:\n=== DR. HEART ===\n{dr}\n=== NUTRI ===\n{nu}\n=== LONGEVITY ===\n{lo}\n=== HOLISTICS ===\n{ho}")

    if supplements and supplements.strip():
        m = """You are Medi/Suppi, pharmacology safety specialist.
1. CONCERNS 2. WATCH LIST 3. GENERAL GUIDANCE
"Consult your doctor or pharmacist before making changes.\""""
        me = ask(m, f"Supplements: {supplements}\nCase: {case}\nGoals: {goals}\nConstraints: {constraints}")
    else:
        me = "No supplements listed."

    results = {"synthesizer": sy, "dr_heart": dr, "nutri": nu, "longevity": lo, "holistics": ho, "medi_suppi": me}
    did = save_debate(case, goals, constraints, model_choice, supplements, results)
    share_url = f"https://health-round-table.onrender.com/?id={did}"
    return results, did, share_url

def on_page_load():
    return [build_feed()]

with gr.Blocks(title="Health Round Table") as demo:
    gr.Markdown("# 🌵 Health Round Table\n*Not medical advice — for educational debate only*")

    with gr.Row():
        with gr.Column(scale=3):
            case_input = gr.Textbox(label="Patient Case", placeholder="42yo female, swollen feet...", lines=5)
        with gr.Column(scale=1):
            goals_input = gr.Textbox(label="Goals", placeholder="Lower BP, more energy...", lines=2)
            constraints_input = gr.Textbox(label="Constraints", placeholder="No pharma, vegetarian...", lines=2)
            model_choice = gr.Dropdown(
                choices=["mistral-large-3:675b", "qwen3-vl:235b-instruct", "deepseek-v3.2"],
                value="mistral-large-3:675b", label="Model"
            )
            supplements_input = gr.Textbox(label="Supplements + Medications", placeholder="List vitamins, supplements...", lines=2)

    start_btn = gr.Button("🚀 Start Round Table", variant="primary")

    with gr.Accordion("💡 TLDR — Key Recommendations", open=True):
        tldr_output = gr.Markdown("*Results will appear here*")

    with gr.Accordion("❤️ Dr. Heart", open=False):
        gr.HTML(avatar_html("dr_heart", "Dr. Heart", "❤️"))
        dr_heart_output = gr.Markdown("*Waiting*")

    with gr.Accordion("🥑 Nutri", open=False):
        gr.HTML(avatar_html("nutri", "Nutri", "🥑"))
        nutri_output = gr.Markdown("*Waiting*")

    with gr.Accordion("⏳ Longevity", open=False):
        gr.HTML(avatar_html("longevity", "Longevity", "⏳"))
        longevity_output = gr.Markdown("*Waiting*")

    with gr.Accordion("🌿 Holistics", open=False):
        gr.HTML(avatar_html("holistics", "Holistics", "🌿"))
        holistics_output = gr.Markdown("*Waiting*")

    with gr.Accordion("💊 Medi/Suppi", open=False):
        gr.HTML(avatar_html("medi_suppi", "Medi/Suppi", "💊"))
        medi_output = gr.Markdown("*Waiting*")

    gr.Markdown("*Each specialist reads all previous analyses.*")

    gr.Markdown("---")
    gr.Markdown("### 🔍 Load a Saved Debate")
    with gr.Row():
        debate_id_input = gr.Textbox(label="Debate ID", placeholder="Paste ID here", lines=1)
        load_btn = gr.Button("Load")
    debate_case_info = gr.Markdown("*Paste a debate ID above to load*")

    feed_display = gr.Markdown()
    demo.load(fn=on_page_load, inputs=[], outputs=[feed_display])

    def on_start(case, goals, constraints, model, supplements):
        results, did, share_url = run_round_table(case, goals, constraints, model, supplements)
        share_link = f"**Saved!** [Open debate]({share_url}) | ID: `{did}`"
        return [
            results["synthesizer"],
            results["dr_heart"],
            results["nutri"],
            results["longevity"],
            results["holistics"],
            results["medi_suppi"],
            share_link,
            build_feed(),
        ]

    def on_load(debate_id):
        if not debate_id:
            return ["*Paste a debate ID above to load*"] + [""] * 7
        d = get_debate(debate_id.strip())
        if not d:
            return ["⚠️ Not found.", "", "", "", "", "", "", build_feed()]
        increment_views(d["id"])
        r = d["results"]
        info = f"**Case:** {d['case']}\n**Goals:** {d['goals']}\n**Constraints:** {d['constraints']}\n**Ran:** {d['timestamp']} | Views: {d['views']+1}"
        return [info, r["synthesizer"], r["dr_heart"], r["nutri"], r["longevity"], r["holistics"], r["medi_suppi"], ""]

    start_btn.click(
        fn=on_start,
        inputs=[case_input, goals_input, constraints_input, model_choice, supplements_input],
        outputs=[tldr_output, dr_heart_output, nutri_output, longevity_output, holistics_output, medi_output, debate_case_info, feed_display]
    )

    load_btn.click(
        fn=on_load,
        inputs=[debate_id_input],
        outputs=[debate_case_info, tldr_output, dr_heart_output, nutri_output, longevity_output, holistics_output, medi_output, feed_display]
    )

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 7861))
    demo.launch(server_name="0.0.0.0", server_port=port)
