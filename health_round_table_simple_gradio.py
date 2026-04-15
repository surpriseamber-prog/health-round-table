import gradio as gr
import requests
import time
import hashlib
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

# --- Storage ---
debates_db = {}

def make_id():
    return hashlib.md5(str(time.time()).encode()).hexdigest()[:8]

def save_debate(case, goals, constraints, model, supplements, results):
    did = make_id()
    debates_db[did] = {
        "case": case, "goals": goals, "constraints": constraints,
        "model": model, "supplements": supplements, "results": results,
        "timestamp": datetime.now().strftime("%b %d, %Y %I:%M %p"), "views": 0
    }
    return did

def get_debate(did):
    d = debates_db.get(did)
    if d:
        d["views"] += 1
    return d

def get_recent():
    return sorted([(k, v) for k, v in debates_db.items()], key=lambda x: x[1]["views"], reverse=True)[:10]

def build_feed():
    debates = get_recent()
    if not debates:
        return "*No debates saved yet — submit a case above!*"
    lines = ["### 📖 Recent Debates\n", "| ID | Case Preview | Date | Views |", "|----|------|------|-------|"]
    for did, d in debates:
        prev = (d["case"][:55]+"...") if len(d["case"])>55 else d["case"]
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

# --- UI ---
with gr.Blocks(title="Health Round Table") as demo:
    gr.Markdown("# 🌵 Health Round Table\n*Not medical advice — for educational debate only*")

    with gr.Row():
        with gr.Column(scale=3):
            case_input = gr.Textbox(label="Patient Case", placeholder="42yo female, swollen feet, weight 180lbs...", lines=5)
        with gr.Column(scale=1):
            goals_input = gr.Textbox(label="Goals", placeholder="Lower BP, more energy...", lines=2)
            constraints_input = gr.Textbox(label="Constraints", placeholder="No pharma, vegetarian...", lines=2)
            model_choice = gr.Dropdown(
                choices=["mistral-large-3:675b", "qwen3-vl:235b-instruct", "deepseek-v3.2"],
                value="mistral-large-3:675b", label="Model"
            )
            supplements_input = gr.Textbox(label="Supplements + Medications", placeholder="List vitamins, supplements, Rx meds...", lines=2)

    with gr.Row():
        start_btn = gr.Button("🚀 Start Round Table", variant="primary")
        clear_btn = gr.Button("Clear")

    loading_status = gr.HTML("<div style='padding:10px;color:#f97316;font-weight:bold;'>⏳ Processing... 6 agents thinking (1-3 min)...</div>", visible=False)
    share_output = gr.Markdown(visible=False)

    with gr.Accordion("💡 TLDR — Key Recommendations", open=True):
        tldr_output = gr.Markdown("*Run a case to see recommendations*")

    with gr.Accordion("Dr. Heart (Cardiology)", open=False):
        gr.HTML(avatar_html("dr_heart", "Dr. Heart", "❤️"))
        dr_heart_output = gr.Markdown("*Waiting for Dr. Heart...*")

    with gr.Accordion("Nutri (Functional Nutrition)", open=False):
        gr.HTML(avatar_html("nutri", "Nutri", "🥑"))
        nutri_output = gr.Markdown("*Waiting for Nutri...*")

    with gr.Accordion("Longevity (Anti-Aging Research)", open=False):
        gr.HTML(avatar_html("longevity", "Longevity", "⏳"))
        longevity_output = gr.Markdown("*Waiting for Longevity...*")

    with gr.Accordion("Holistics (Integrative Medicine)", open=False):
        gr.HTML(avatar_html("holistics", "Holistics", "🌿"))
        holistics_output = gr.Markdown("*Waiting for Holistics...*")

    with gr.Accordion("Medi/Suppi (Drug + Supplement Safety)", open=False):
        gr.HTML(avatar_html("medi_suppi", "Medi/Suppi", "💊"))
        medi_output = gr.Markdown("*Waiting for Medi/Suppi...*")

    gr.Markdown("*Each specialist reads all previous analyses.*")

    # Recent Debates
    feed_display = gr.Markdown()
    demo.load(fn=build_feed, inputs=[], outputs=[feed_display])

    # Load Saved Debate
    gr.Markdown("---")
    gr.Markdown("### 🔍 Load a Saved Debate")
    with gr.Row():
        debate_id_input = gr.Textbox(label="Debate ID", placeholder="Paste debate ID here", lines=1)
        load_btn = gr.Button("Load")
    debate_case_info = gr.Markdown("*Paste an ID and click Load to view a saved debate*")

    # ---- Output component lists ----
    # For start_btn: [loading, share, tldr, dr_heart, nutri, longevity, holistics, medi, feed]
    start_outputs = [loading_status, share_output, tldr_output, dr_heart_output, nutri_output, longevity_output, holistics_output, medi_output, feed_display]
    # For load_btn: [debate_case_info, tldr, dr_heart, nutri, longevity, holistics, medi, feed]
    load_outputs = [debate_case_info, tldr_output, dr_heart_output, nutri_output, longevity_output, holistics_output, medi_output, feed_display]
    # For clear_btn: [case, goals, constraints, supplements, model, loading, share, tldr, dr_heart, nutri, longevity, holistics, medi, feed]
    clear_outputs = [case_input, goals_input, constraints_input, supplements_input, model_choice, loading_status, share_output, tldr_output, dr_heart_output, nutri_output, longevity_output, holistics_output, medi_output, feed_display]

    def on_start(case, goals, constraints, model, supplements):
        # Step 1: show loading
        yield [True, False, "", "", "", "", "", "", ""]
        # Step 2: run and show results
        try:
            results, did, share_url = run_round_table(case, goals, constraints, model, supplements)
            share_link = f"**✅ Saved!** [Open this debate]({share_url}) | ID: `{did}`"
            yield [
                False,                          # hide loading
                share_link,                     # share_output (Markdown)
                results["synthesizer"],         # tldr_output
                results["dr_heart"],            # dr_heart_output
                results["nutri"],               # nutri_output
                results["longevity"],           # longevity_output
                results["holistics"],           # holistics_output
                results["medi_suppi"],          # medi_output
                build_feed(),                    # feed_display
            ]
        except Exception as e:
            yield [
                False,
                f"**Error:** {str(e)[:200]}",
                "Error",
                "Error",
                "Error",
                "Error",
                "Error",
                "Error",
                build_feed(),
            ]

    def on_clear():
        return ["", "", "", "", "", False, False, "*Run a case to see recommendations*", "*Waiting for Dr. Heart...*", "*Waiting for Nutri...*", "*Waiting for Longevity...*", "*Waiting for Holistics...*", "*Waiting for Medi/Suppi...*", build_feed()]

    def on_load(debate_id):
        d = get_debate(debate_id.strip())
        if not d:
            return ["⚠️ Debate not found. It may have been cleared after Render sleep.", "", "", "", "", "", "", build_feed()]
        r = d["results"]
        info = f"**Case:** {d['case']}\n**Goals:** {d['goals']}\n**Constraints:** {d['constraints']}\n**Ran:** {d['timestamp']} | **Views:** {d['views']}"
        return [info, r["synthesizer"], r["dr_heart"], r["nutri"], r["longevity"], r["holistics"], r["medi_suppi"], ""]

    start_btn.click(fn=on_start, inputs=[case_input, goals_input, constraints_input, model_choice, supplements_input], outputs=start_outputs)
    clear_btn.click(fn=on_clear, inputs=[], outputs=clear_outputs)
    load_btn.click(fn=on_load, inputs=[debate_id_input], outputs=load_outputs)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 7861))
    print(f"Starting Health Round Table on port {port}...")
    demo.launch(server_name="0.0.0.0", server_port=port)
