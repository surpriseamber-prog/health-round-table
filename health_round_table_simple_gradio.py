import gradio as gr
import requests
import time
import hashlib
import sqlite3
import json
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

API_KEY = "939d10536ea749c2ac9f1ae783335eaa.L8GP6pNpV7FVESvej9RAoDTT"
BASE_URL = "https://api.ollama.com"
headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

AVATARS = {
    "synthesizer": "https://raw.githubusercontent.com/surpriseamber-prog/health-round-table/main/static/avatars/avatar_synthesizer.jpg",
    "dr_heart": "https://raw.githubusercontent.com/surpriseamber-prog/health-round-table/main/static/avatars/avatar_dr_heart.jpg",
    "nutri": "https://raw.githubusercontent.com/surpriseamber-prog/health-round-table/main/static/avatars/avatar_nutri.jpg",
    "longevity": "https://raw.githubusercontent.com/surpriseamber-prog/health-round-table/main/static/avatars/avatar_longevity.jpg",
    "holistics": "https://raw.githubusercontent.com/surpriseamber-prog/health-round-table/main/static/avatars/avatar_holistics.jpg",
    "medi_suppi": "https://raw.githubusercontent.com/surpriseamber-prog/health-round-table/main/static/avatars/avatar_medi_suppi.jpg",
}

def avatar_img(key, size=40):
    return f'<img src="{AVATARS[key]}" width="{size}" height="{size}" style="border-radius:50%;object-fit:cover;">'

AGENTS = {
    "synthesizer": {
        "name": "Synthesizer", "emoji": "💡", "avatar": "synthesizer",
        "system": "You are the Synthesizer, a wise medical professor. Create consensus recommendations. Give exactly 3 clear numbered recommendations (1. 2. 3.). Be warm, clear, and practical."
    },
    "dr_heart": {
        "name": "Dr. Heart", "emoji": "❤️", "avatar": "dr_heart",
        "system": "You are Dr. Heart, a board-certified cardiologist. Focus on BP, cholesterol, and circulation. Give practical, actionable advice with bullet points. Be warm but clinical."
    },
    "nutri": {
        "name": "Nutri", "emoji": "🥑", "avatar": "nutri",
        "system": "You are Nutri, a functional medicine nutritionist. Focus on food as medicine. Give practical nutrition advice with bullet points. Be encouraging, not preachy."
    },
    "longevity": {
        "name": "Longevity", "emoji": "⏳", "avatar": "longevity",
        "system": "You are Longevity, an anti-aging researcher. Focus on longevity science, biomarkers, and evidence-based anti-aging strategies. Give bullet point advice. Be energetic and optimistic."
    },
    "holistics": {
        "name": "Holistics", "emoji": "🌿", "avatar": "holistics",
        "system": "You are Holistics, an integrative medicine practitioner. Focus on mind-body connection, stress, sleep, and holistic wellness. Give bullet point advice. Be calm and nurturing."
    },
    "medi_suppi": {
        "name": "Medi/Suppi", "emoji": "💊", "avatar": "medi_suppi",
        "system": "You are Medi/Suppi, a pharmacology and supplement safety specialist. Flag drug and supplement interactions, age-related risks, and potential harms. Always include: 'Consult your doctor or pharmacist before making changes.' Be direct and safety-focused."
    },
}

# --- SQLite ---
DB_PATH = os.path.join(os.path.dirname(__file__), "debates.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS debates (id TEXT PRIMARY KEY, case_text TEXT, goals TEXT, constraints TEXT, model TEXT, supplements TEXT, results TEXT, timestamp TEXT, views INTEGER DEFAULT 0, feedback TEXT DEFAULT '{}')")
    conn.commit()
    conn.close()
init_db()

def save_feedback(did, agent, rating):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT feedback FROM debates WHERE id=?", (did,)).fetchone()
    if not row:
        conn.close()
        return
    fb = json.loads(row[0] or '{}')
    fb[agent] = rating
    conn.execute("UPDATE debates SET feedback=? WHERE id=?", (json.dumps(fb), did))
    conn.commit()
    conn.close()

def get_feedback(did):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT feedback FROM debates WHERE id=?", (did,)).fetchone()
    conn.close()
    return json.loads(row[0] or '{}') if row else {}

def make_id():
    return hashlib.md5(str(time.time()).encode()).hexdigest()[:8]

def save_debate(case, goals, constraints, model, supplements, results):
    did = make_id()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO debates (id,case_text,goals,constraints,model,supplements,results,timestamp,views) VALUES (?,?,?,?,?,?,?,?,0)",
        (did, case, goals, constraints, model, supplements, json.dumps(results), datetime.now().strftime("%b %d, %Y %I:%M %p")))
    conn.commit()
    conn.close()
    return did

def load_debate(did):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT * FROM debates WHERE id=?", (did,)).fetchone()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "case": row[1], "goals": row[2], "constraints": row[3], "model": row[4], "supplements": row[5], "results": json.loads(row[6]), "timestamp": row[7], "views": row[8]}

def inc_views(did):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE debates SET views=views+1 WHERE id=?", (did,))
    conn.commit()
    conn.close()

def recent_debates():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT * FROM debates ORDER BY views DESC LIMIT 10").fetchall()
    conn.close()
    return [(r[0], {"case": r[1], "goals": r[2], "constraints": r[3], "model": r[4], "supplements": r[5], "results": json.loads(r[6]), "timestamp": r[7], "views": r[8]}) for r in rows]

def feed_html():
    debates = recent_debates()
    if not debates:
        return "*No debates yet — run a case above!*"
    html = "<h3>📖 Recent Debates</h3><table><tr><th>ID</th><th>Case</th><th>Date</th><th>Views</th></tr>"
    for did, d in debates:
        prev = (d["case"][:45]+"...") if len(d["case"])>45 else d["case"]
        prev = prev.replace("\n"," ")
        html += f"<tr><td><code>{did}</code></td><td>{prev}</td><td>{d['timestamp']}</td><td>{d['views']}</td></tr>"
    html += "</table>"
    return html

# --- API ---
def chat(model, system, messages):
    payload = {"model": model, "messages": [{"role": "system", "content": system}] + messages, "stream": False}
    r = requests.post(f"{BASE_URL}/api/chat", headers=headers, json=payload)
    if r.status_code != 200:
        raise Exception(f"API Error {r.status_code}: {r.text}")
    return r.json()["message"]["content"]

def run_debate(case, goals, constraints, model_choice, supplements, guest):
    guest_block = f"\n\nOTHER AI PERSPECTIVES (submitted by the patient):\n{guest}" if guest and guest.strip() else ""
    ctx = (f"\n\nPATIENT GOALS:\n{goals}" if goals else "") + (f"\n\nIMPORTANT CONSTRAINTS:\n{constraints}" if constraints else "") + guest_block

    def ask(sys, prompt):
        try:
            return chat(model_choice, sys, [{"role": "user", "content": prompt}])
        except Exception as e:
            return f"Error: {e}"

    # Phase 1: Run 4 agents in parallel
    with ThreadPoolExecutor(max_workers=4) as executor:
        f_dr = executor.submit(ask, f"You are Dr. Heart, cardiologist. Focus on BP, cholesterol, circulation.{ctx}\nBullet points.", f"Analyze: {case}")
        f_nu = executor.submit(ask, f"You are Nutri, functional nutritionist. Build on Dr. Heart's foundation.{ctx}\nBullet points.", f"React:\n=== DR. HEART ===\n{{dr_result}}\nCase: {case}")
        f_lo = executor.submit(ask, f"You are Longevity, anti-aging researcher.{ctx}\nBullet points.", f"Build:\n=== DR. HEART ===\n{{dr_result}}\n=== NUTRI ===\n{{nu_result}}\nCase: {case}")
        f_ho = executor.submit(ask, f"You are Holistics, integrative medicine.{ctx}\nBullet points.", f"Build:\n=== DR. HEART ===\n{{dr_result}}\n=== NUTRI ===\n{{nu_result}}\n=== LONGEVITY ===\n{{lo_result}}\nCase: {case}")

        dr = f_dr.result()
        nu = f_nu.result()
        lo = f_lo.result()
        ho = f_ho.result()

    # Phase 2: Synthesizer needs all previous agents
    sy = ask(f"You are the Synthesizer, medical professor. Give exactly 3 numbered recommendations.{ctx}",
            f"Consensus:\n=== DR. HEART ===\n{dr}\n=== NUTRI ===\n{nu}\n=== LONGEVITY ===\n{lo}\n=== HOLISTICS ===\n{ho}")

    # Phase 3: Medi/Suppi independent
    if supplements and supplements.strip():
        me = ask("You are Medi/Suppi, pharmacology safety specialist.\n1. CONCERNS 2. WATCH LIST 3. GENERAL GUIDANCE\n'Always consult your doctor or pharmacist.'",
                f"Supplements: {supplements}\nCase: {case}\nGoals: {goals}\nConstraints: {constraints}")
    else:
        me = "No supplements listed."

    results = {"synthesizer": sy, "dr_heart": dr, "nutri": nu, "longevity": lo, "holistics": ho, "medi_suppi": me}
    did = save_debate(case, goals, constraints, model_choice, supplements, results)
    return results, did, f"https://health-round-table.onrender.com/?id={did}"

def chat_agent(agent_key, message, history, model):
    agent = AGENTS[agent_key]
    if not message or not message.strip():
        return history
    messages = [{"role": "user", "content": m[0]} for m in history] + [{"role": "user", "content": message}]
    try:
        response = chat(model, agent["system"], messages)
    except Exception as e:
        response = f"Error: {str(e)}"
    history.append((message, response))
    return history

# --- UI ---
with gr.Blocks(title="Health Round Table") as demo:
    gr.Markdown("# 🌵 Health Round Table\n*Not medical advice — for educational debate only*")

    with gr.Tabs():
        # === GROUP DEBATE TAB ===
        with gr.TabItem("🎯 Group Debate"):
            with gr.Row():
                with gr.Column(scale=3):
                    case_input = gr.Textbox(label="Patient Case", placeholder="Age: 42\nM/F: F\nWeight: 150 lbs\nHeight: 5'4\"\nBPM: 95\nSymptoms: swollen feet (edema) for 2 weeks, occasional shortness of breath\nExercise level: sedentary, 1 day a week, none\n\nAdditional Details:", lines=8)
                    guest_input = gr.Textbox(label="🌐 Guest Perspectives (paste what other AIs said — Grok, Claude, etc.)", placeholder="Paste any external AI analysis here...", lines=3)
                with gr.Column(scale=1):
                    goals_input = gr.Textbox(label="Goals", placeholder="Lower BP, more energy...", lines=2)
                    constraints_input = gr.Textbox(label="Constraints", placeholder="No pharma, vegetarian...", lines=2)
                    model_choice = gr.Dropdown(choices=["deepseek-v3.2","qwen3-vl:235b-instruct","gemma3:27b","minimax-m2.7"], value="deepseek-v3.2", label="Model")
                    supplements_input = gr.Textbox(label="Supplements + Medications", placeholder="List vitamins, supplements...", lines=2)

            start_btn = gr.Button("🚀 Start Round Table", variant="primary")
            loading_display = gr.HTML("<p style='color:#aaa;text-align:center;'>⏳ Running 6 specialist agents in parallel...</p>", visible=False)

            with gr.Accordion("💡 TLDR — Key Recommendations", open=True):
                tldr_output = gr.Markdown("*Results appear here*")

            with gr.Accordion("❤️ Dr. Heart", open=False):
                gr.HTML(f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">{avatar_img("dr_heart")}<b>Dr. Heart</b> — Cardiology</div>')
                dr_out = gr.Markdown("*Waiting*")
                with gr.Row():
                    gr.Button("👍", variant="secondary", size="sm").click(fn=lambda did, ag="dr_heart": save_feedback(did, ag, "up") if did else None, inputs=[did_info], outputs=[])
                    gr.Button("👎", variant="secondary", size="sm").click(fn=lambda did, ag="dr_heart": save_feedback(did, ag, "down") if did else None, inputs=[did_info], outputs=[])

            with gr.Accordion("🥑 Nutri", open=False):
                gr.HTML(f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">{avatar_img("nutri")}<b>Nutri</b> — Functional Nutrition</div>')
                nu_out = gr.Markdown("*Waiting*")
                with gr.Row():
                    gr.Button("👍", variant="secondary", size="sm").click(fn=lambda did, ag="nutri": save_feedback(did, ag, "up") if did else None, inputs=[did_info], outputs=[])
                    gr.Button("👎", variant="secondary", size="sm").click(fn=lambda did, ag="nutri": save_feedback(did, ag, "down") if did else None, inputs=[did_info], outputs=[])

            with gr.Accordion("⏳ Longevity", open=False):
                gr.HTML(f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">{avatar_img("longevity")}<b>Longevity</b> — Anti-Aging Research</div>')
                lo_out = gr.Markdown("*Waiting*")
                with gr.Row():
                    gr.Button("👍", variant="secondary", size="sm").click(fn=lambda did, ag="longevity": save_feedback(did, ag, "up") if did else None, inputs=[did_info], outputs=[])
                    gr.Button("👎", variant="secondary", size="sm").click(fn=lambda did, ag="longevity": save_feedback(did, ag, "down") if did else None, inputs=[did_info], outputs=[])

            with gr.Accordion("🌿 Holistics", open=False):
                gr.HTML(f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">{avatar_img("holistics")}<b>Holistics</b> — Integrative Medicine</div>')
                ho_out = gr.Markdown("*Waiting*")
                with gr.Row():
                    gr.Button("👍", variant="secondary", size="sm").click(fn=lambda did, ag="holistics": save_feedback(did, ag, "up") if did else None, inputs=[did_info], outputs=[])
                    gr.Button("👎", variant="secondary", size="sm").click(fn=lambda did, ag="holistics": save_feedback(did, ag, "down") if did else None, inputs=[did_info], outputs=[])

            with gr.Accordion("💊 Medi/Suppi", open=False):
                gr.HTML(f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">{avatar_img("medi_suppi")}<b>Medi/Suppi</b> — Drug + Supplement Safety</div>')
                me_out = gr.Markdown("*Waiting*")
                with gr.Row():
                    gr.Button("👍", variant="secondary", size="sm").click(fn=lambda did, ag="medi_suppi": save_feedback(did, ag, "up") if did else None, inputs=[did_info], outputs=[])
                    gr.Button("👎", variant="secondary", size="sm").click(fn=lambda did, ag="medi_suppi": save_feedback(did, ag, "down") if did else None, inputs=[did_info], outputs=[])

            gr.Markdown("*Each specialist reads all previous analyses.*")

            gr.Markdown("---")
            gr.Markdown("### 🔍 Load a Saved Debate")
            with gr.Row():
                did_input = gr.Textbox(label="Debate ID", placeholder="Paste ID here", lines=1)
                load_btn = gr.Button("Load")
            did_info = gr.Markdown("*Paste a debate ID above to load it*")

            feed_out = gr.HTML()
            demo.load(fn=lambda: [feed_html()], inputs=[], outputs=[feed_out])

            def on_start(case, goals, constraints, model, supplements, guest):
                # Show loading, hide results (9 outputs: tldr, dr, nu, lo, ho, me, share, loading, feed)
                yield ["*Working...*", "*Working...*", "*Working...*", "*Working...*", "*Working...*", "*Working...*", "", "⏳ Running 6 specialists in parallel...", feed_html()]
                results, did, url = run_debate(case, goals, constraints, model, supplements, guest)
                share = f"**Saved!** [Open debate]({url}) | ID: `{did}`"
                yield [results["synthesizer"], results["dr_heart"], results["nutri"], results["longevity"], results["holistics"], results["medi_suppi"], share, "", feed_html()]

            def on_load(did_raw):
                did = did_raw.strip() if did_raw else ""
                if not did:
                    return ["*Paste a debate ID above*", "", "", "", "", "", "", "", feed_html()]
                d = load_debate(did)
                if not d:
                    return ["⚠️ Not found.", "", "", "", "", "", "", "", feed_html()]
                inc_views(did)
                r = d["results"]
                info = f"**Case:** {d['case']}\n**Goals:** {d['goals']}\n**Constraints:** {d['constraints']}\n**Ran:** {d['timestamp']} | Views: {d['views']+1}\n\n**Share:** [Open debate](https://health-round-table.onrender.com/?id={did})"
                return [info, r["synthesizer"], r["dr_heart"], r["nutri"], r["longevity"], r["holistics"], r["medi_suppi"], "", ""]

            start_btn.click(
                fn=on_start,
                inputs=[case_input, goals_input, constraints_input, model_choice, supplements_input, guest_input],
                outputs=[tldr_output, dr_out, nu_out, lo_out, ho_out, me_out, did_info, loading_display, feed_out]
            )
            load_btn.click(fn=on_load, inputs=[did_input],
                          outputs=[did_info, tldr_output, dr_out, nu_out, lo_out, ho_out, me_out, loading_display, feed_out])

        # === INDIVIDUAL CHAT TABS ===
        with gr.TabItem("💬 Chat Individually"):
            gr.Markdown("### Chat one-on-one with any agent. Your conversation is saved for this session.")
            with gr.Tabs():
                for agent_key, agent in AGENTS.items():
                    with gr.TabItem(f"{agent['emoji']} {agent['name']}"):
                        gr.HTML(f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">{avatar_img(agent_key, 48)}<span style="font-size:1.2em;"><b>{agent["name"]}</b> {agent["emoji"]}</span></div>')
                        chatbot = gr.Chatbot(label=agent["name"], height=300)
                        msg = gr.Textbox(label=f"Message {agent['name']}", placeholder=f"Ask {agent['name']} anything...", lines=2)
                        with gr.Row():
                            send_btn = gr.Button(f" Send to {agent['name']}", variant="primary")
                            clear_btn = gr.Button("Clear chat")
                        state = gr.State([])
                        send_btn.click(fn=lambda msg, hist, ag=agent_key, m=model_choice: chat_agent(ag, msg, hist, m),
                                     inputs=[msg, state], outputs=[chatbot, state])
                        clear_btn.click(fn=lambda: [None, ""], inputs=[], outputs=[chatbot, msg])

        # === ABOUT TAB ===
        with gr.TabItem("ℹ️ About"):
            gr.Markdown("""## 🌵 Health Round Table

**Our Mission:** Collective AI intelligence for health — because no single source has all the answers.

Peer review revolutionized science. We believe the same principle can transform health: multiple AI agents, each with different expertise, different training, different blind spots — all working on the same problem. The synthesis of their collective knowledge can surface patterns and solutions no single agent would find alone.

6 specialized AI agents debate your health case together — or chat with them one-on-one.

**Group Debate:** All 6 agents analyze your case, each reading the others' responses.
**Chat Individually:** Go deep with any single agent.

**The Agents:**
- ❤️ **Dr. Heart** — Cardiologist
- 🥑 **Nutri** — Functional Nutritionist
- ⏳ **Longevity** — Anti-Aging Researcher
- 🌿 **Holistics** — Integrative Medicine
- 💡 **Synthesizer** — Consensus Professor
- 💊 **Medi/Suppi** — Supplement Safety

*⚠️ Not medical advice. Always consult a healthcare provider.*
""")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7861))
    demo.launch(server_name="0.0.0.0", server_port=port)
