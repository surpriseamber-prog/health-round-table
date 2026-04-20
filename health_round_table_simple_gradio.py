import gradio as gr
import urllib.request
import urllib.error
import time
import hashlib
import sqlite3
import json
import os
from datetime import datetime

API_KEY = os.environ.get("OLLAMA_API_KEY", "")
LOCAL_URL = "http://localhost:11434"
CLOUD_URL = "https://api.ollama.com"

# Local models known to be installed
LOCAL_MODELS = {"qwen2.5:7b"}
CLOUD_MODELS = {"deepseek-v3.2", "qwen3-vl:235b-instruct", "gemma3:27b", "minimax-m2.7"}

def get_base_url(model=None):
    """Route to local if available and running, otherwise cloud."""
    def local_up():
        try:
            req = urllib.request.Request(f"{LOCAL_URL}/api/tags", method="GET")
            r = urllib.request.urlopen(req, timeout=3)
            return r.status == 200
        except:
            return False
    if model in LOCAL_MODELS:
        if local_up():
            return LOCAL_URL
    if model in CLOUD_MODELS or model is None:
        return CLOUD_URL
    if local_up():
        return LOCAL_URL
    return CLOUD_URL

BASE_URL = CLOUD_URL  # default; overridden at runtime

if not API_KEY:
    raise ValueError("OLLAMA_API_KEY environment variable is not set")
headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (compatible; HealthRoundTable/1.0)"}


AVATARS = {
    "synthesizer": "https://raw.githubusercontent.com/surpriseamber-prog/health-round-table/main/static/avatars/avatar_synthesizer.jpg",
    "dr_heart": "https://raw.githubusercontent.com/surpriseamber-prog/health-round-table/main/static/avatars/avatar_dr_heart.jpg",
    "nutri": "https://raw.githubusercontent.com/surpriseamber-prog/health-round-table/main/static/avatars/avatar_nutri.jpg",
    "longevity": "https://raw.githubusercontent.com/surpriseamber-prog/health-round-table/main/static/avatars/avatar_longevity.jpg",
    "holistics": "https://raw.githubusercontent.com/surpriseamber-prog/health-round-table/main/static/avatars/avatar_holistics.jpg",
    "medi_suppi": "https://raw.githubusercontent.com/surpriseamber-prog/health-round-table/main/static/avatars/avatar_medi_suppi.jpg",
}

AGENTS = {
    "synthesizer": {"name": "Synthesizer", "emoji": "💡", "system": "You are the Synthesizer, a medical professor. You give exactly 3 numbered, bold recommendations. Always remind patients to consult their doctor."},
    "dr_heart": {"name": "Dr. Heart", "emoji": "❤️", "system": "You are Dr. Heart, a cardiologist. Focus on blood pressure, cholesterol, circulation. Give bullet points."},
    "nutri": {"name": "Nutri", "emoji": "🥑", "system": "You are Nutri, a functional nutritionist. Build on what the previous specialists said. Give bullet points."},
    "longevity": {"name": "Longevity", "emoji": "⏳", "system": "You are Longevity, an anti-aging researcher. Build on what previous specialists said. Give bullet points."},
    "holistics": {"name": "Holistics", "emoji": "🌿", "system": "You are Holistics, an integrative medicine specialist. Build on what previous specialists said. Give bullet points."},
    "medi_suppi": {"name": "Medi/Suppi", "emoji": "💊", "system": "You are Medi/Suppi, a pharmacology and supplement safety specialist. Give 3 sections: 1. CONCERNS 2. WATCH LIST 3. GENERAL GUIDANCE. Always remind: 'Consult your doctor or pharmacist.'"},
}

def avatar_img(key, size=40):
    url = AVATARS.get(key, AVATARS["synthesizer"])
    return f'<img src="{url}" width="{size}" height="{size}" style="border-radius:50%;vertical-align:middle;margin-right:4px;" />'

def init_db():
    conn = sqlite3.connect("debates.db")
    conn.execute("""CREATE TABLE IF NOT EXISTS debates (
        id TEXT PRIMARY KEY,
        case_info TEXT,
        goals TEXT,
        constraints TEXT,
        model TEXT,
        supplements TEXT,
        results TEXT,
        timestamp TEXT,
        views INTEGER DEFAULT 0,
        feedback TEXT DEFAULT '{}'
    )""")
    conn.commit()
    conn.close()

def save_feedback(did, agent, rating):
    conn = sqlite3.connect("debates.db")
    cur = conn.execute("SELECT feedback FROM debates WHERE id=?", (did,))
    row = cur.fetchone()
    fb = json.loads(row[0]) if row and row[0] else {}
    fb[agent] = rating
    conn.execute("UPDATE debates SET feedback=? WHERE id=?", (json.dumps(fb), did))
    conn.commit()
    conn.close()

def get_feedback(did):
    conn = sqlite3.connect("debates.db")
    cur = conn.execute("SELECT feedback FROM debates WHERE id=?", (did,))
    row = cur.fetchone()
    conn.close()
    return json.loads(row[0]) if row and row[0] else {}

def make_id():
    return hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]

def save_debate(case_info, goals, constraints, model, supplements, results):
    did = make_id()
    conn = sqlite3.connect("debates.db")
    conn.execute("""INSERT INTO debates (id,case_info,goals,constraints,model,supplements,results,timestamp)
        VALUES (?,?,?,?,?,?,?,?)""",
        (did, case_info, goals, constraints, model, supplements, json.dumps(results), datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()
    return did

def load_debate(did):
    conn = sqlite3.connect("debates.db")
    cur = conn.execute("SELECT * FROM debates WHERE id=?", (did,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "case": row[1], "goals": row[2], "constraints": row[3], "model": row[4],
            "supplements": row[5], "results": json.loads(row[6]), "timestamp": row[7], "views": row[8], "feedback": json.loads(row[9])}

def inc_views(did):
    conn = sqlite3.connect("debates.db")
    conn.execute("UPDATE debates SET views=views+1 WHERE id=?", (did,))
    conn.commit()
    conn.close()

def recent_debates():
    conn = sqlite3.connect("debates.db")
    cur = conn.execute("SELECT id,case_info,timestamp,views FROM debates ORDER BY rowid DESC LIMIT 10")
    rows = cur.fetchall()
    conn.close()
    return [(r[0], {"case": r[1], "timestamp": r[2], "views": r[3]}) for r in rows]

def feed_html():
    debates = recent_debates()
    if not debates:
        return "<em>No debates yet — run a case above!</em>"
    html = "<h3>📖 Recent Debates</h3><table><tr><th>ID</th><th>Case</th><th>Date</th><th>Views</th></tr>"
    for did, d in debates:
        prev = (d["case"][:45] + "...") if len(d["case"]) > 45 else d["case"]
        prev = prev.replace("\n", " ")
        html += f"<tr><td><code>{did}</code></td><td>{prev}</td><td>{d['timestamp']}</td><td>{d['views']}</td></tr>"
    html += "</table>"
    return html

def chat(model, system, messages, timeout=60):
    base = get_base_url(model)
    payload = {"model": model, "messages": [{"role": "system", "content": system}] + messages, "stream": False}
    data = json.dumps(payload).encode()
    if base == LOCAL_URL:
        headers = {"Content-Type": "application/json"}
    else:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    req = urllib.request.Request(f"{base}/api/chat", data=data, headers=headers, method="POST")
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(r.read())["message"]["content"]
    except urllib.error.HTTPError as e:
        raise Exception(f"API Error {e.code}: {e.read()}")
    except urllib.error.URLError as e:
        raise Exception(f"Network Error: {e.reason}")

def run_debate(case, goals, constraints, model_choice, supplements, guest):
    guest_block = f"\n\nOTHER AI PERSPECTIVES:\n{guest}" if guest and guest.strip() else ""
    ctx = (f"\n\nPATIENT GOALS:\n{goals}" if goals else "") + (f"\n\nIMPORTANT CONSTRAINTS:\n{constraints}" if constraints else "") + guest_block

    def ask(sys, prompt):
        try:
            return chat(model_choice, sys, [{"role": "user", "content": prompt}])
        except Exception as e:
            return f"Error: {e}"

    dr = ask(f"You are Dr. Heart, cardiologist. Focus on BP, cholesterol, circulation.{ctx}\nBullet points.", f"Analyze: {case}")
    yield {"dr_heart": dr}
    nu = ask(f"You are Nutri, functional nutritionist. Build on Dr. Heart's foundation.{ctx}\nBullet points.", f"React:\n=== DR. HEART ===\n{dr}\nCase: {case}")
    yield {"dr_heart": dr, "nutri": nu}
    lo = ask(f"You are Longevity, anti-aging researcher.{ctx}\nBullet points.", f"Build:\n=== DR. HEART ===\n{dr}\n=== NUTRI ===\n{nu}\nCase: {case}")
    yield {"dr_heart": dr, "nutri": nu, "longevity": lo}
    ho = ask(f"You are Holistics, integrative medicine.{ctx}\nBullet points.", f"Build:\n=== DR. HEART ===\n{dr}\n=== NUTRI ===\n{nu}\n=== LONGEVITY ===\n{lo}\nCase: {case}")
    yield {"dr_heart": dr, "nutri": nu, "longevity": lo, "holistics": ho}
    sy = ask(f"You are the Synthesizer, medical professor. Give exactly 3 numbered recommendations.{ctx}",
            f"Consensus:\n=== DR. HEART ===\n{dr}\n=== NUTRI ===\n{nu}\n=== LONGEVITY ===\n{lo}\n=== HOLISTICS ===\n{ho}")
    yield {"dr_heart": dr, "nutri": nu, "longevity": lo, "holistics": ho, "synthesizer": sy}
    if supplements and supplements.strip():
        me = ask("You are Medi/Suppi, pharmacology safety specialist.\n1. CONCERNS 2. WATCH LIST 3. GENERAL GUIDANCE\n'Always consult your doctor or pharmacist.'",
                f"Supplements: {supplements}\nCase: {case}\nGoals: {goals}\nConstraints: {constraints}")
    else:
        me = "No supplements listed."
    yield {"dr_heart": dr, "nutri": nu, "longevity": lo, "holistics": ho, "synthesizer": sy, "medi_suppi": me}
    results = {"synthesizer": sy, "dr_heart": dr, "nutri": nu, "longevity": lo, "holistics": ho, "medi_suppi": me}
    did = save_debate(case, goals, constraints, model_choice, supplements, results)
    return results, did, f"https://health-round-table.com/?id={did}"

def chat_agent(agent_key, message, history, model):
    agent = AGENTS[agent_key]
    if not message or not message.strip():
        return history
    messages = [{"role": "user", "content": m[0]} for m in history] + [{"role": "user", "content": message}]
    try:
        response = chat(model, agent["system"], messages, timeout=90)
    except Exception as e:
        response = f"⚠️ {str(e)}"
    history.append((message, response))
    return history

init_db()

with gr.Blocks(title="Health Round Table") as demo:
    gr.Markdown("# Health Round Table\n*Not medical advice — for educational debate only*")

    with gr.Tabs():
        with gr.TabItem("About"):
            gr.Markdown(""""## What is Health Round Table?
A multi-agent AI system where **6 specialist agents** debate your case from different angles — then a Synthesizer delivers a final verdict.
### The Agents
| Agent | Specialty | Emoji |
|---|---|---|
| **Dr. Heart** | Cardiology | ❤️ |
| **Nutri** | Functional Nutrition | 🥑 |
| **Longevity** | Anti-Aging Research | ⏳ |
| **Holistics** | Integrative Medicine | 🌿 |
| **Medi/Suppi** | Drug + Supplement Safety | 💊 |
| **Synthesizer** | Medical Professor | 💡 |
### How It Works
1. Submit your case with age, sex, weight, height, BPM, symptoms, exercise level
2. Each agent reads all previous analyses — they build on each other
3. Medi/Suppi checks your supplements for interactions
4. Synthesizer gives 3 numbered recommendations
### Warnings
⚠️ **Not medical advice.** Always consult your doctor.
""")

        with gr.TabItem("Group Debate"):
            with gr.Row():
                with gr.Column(scale=3):
                    case_input = gr.Textbox(label="Patient Case", placeholder="Age: 42\nM/F: F\nWeight: 150 lbs\nHeight: 5'4\"\nBPM: 95\nSymptoms: swollen feet (edema) for 2 weeks, occasional shortness of breath\nExercise level: sedentary, 1 day a week, none\n\nAdditional Details:", lines=8)
                    guest_input = gr.Textbox(label="Guest Perspectives (paste what other AIs said)", placeholder="Paste any external AI analysis here...", lines=3)
                with gr.Column(scale=1):
                    goals_input = gr.Textbox(label="Patient Goals", placeholder="e.g. avoid medication, lose 20 lbs...", lines=3)
                    constraints_input = gr.Textbox(label="Constraints / Allergies", placeholder="e.g. on metformin, allergic to penicillin...", lines=3)
                    supplements_input = gr.Textbox(label="Supplements / Medications", placeholder="e.g. magnesium 400mg, fish oil...", lines=3)
                    model_choice = gr.Dropdown(["qwen2.5:7b", "deepseek-v3.2", "qwen3-vl:235b-instruct", "gemma3:27b", "minimax-m2.7"], value="deepseek-v3.2", label="AI Model")
                    start_btn = gr.Button("Start Round Table", variant="primary")

            with gr.Accordion("TLDR — Key Recommendations", open=True):
                tldr_output = gr.Markdown("*Results appear here*")

            with gr.Accordion("❤️ Dr. Heart", open=False):
                gr.HTML('<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">' + avatar_img("dr_heart") + '<b>Dr. Heart</b> — Cardiology</div>')
                dr_out = gr.Markdown("*Waiting*")

            with gr.Accordion("🥑 Nutri", open=False):
                gr.HTML('<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">' + avatar_img("nutri") + '<b>Nutri</b> — Functional Nutrition</div>')
                nu_out = gr.Markdown("*Waiting*")

            with gr.Accordion("⏳ Longevity", open=False):
                gr.HTML('<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">' + avatar_img("longevity") + '<b>Longevity</b> — Anti-Aging Research</div>')
                lo_out = gr.Markdown("*Waiting*")

            with gr.Accordion("🌿 Holistics", open=False):
                gr.HTML('<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">' + avatar_img("holistics") + '<b>Holistics</b> — Integrative Medicine</div>')
                ho_out = gr.Markdown("*Waiting*")

            with gr.Accordion("💊 Medi/Suppi", open=False):
                gr.HTML('<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">' + avatar_img("medi_suppi") + '<b>Medi/Suppi</b> — Drug + Supplement Safety</div>')
                me_out = gr.Markdown("*Waiting*")

            gr.Markdown("*Each specialist reads all previous analyses.*")

            gr.Markdown("---")
            gr.Markdown("### Load a Saved Debate")
            with gr.Row():
                did_input = gr.Textbox(label="Debate ID", placeholder="Paste ID here", lines=1)
                load_btn = gr.Button("Load")
            did_info = gr.Markdown("*Paste a debate ID above to load it*")

            feed_out = gr.HTML()
            demo.load(fn=lambda: [feed_html()], inputs=[], outputs=[feed_out])

            def on_start(case, goals, constraints, model, supplements, guest):
                yield ["*Working...*"] * 6 + ["", "⏳ Dr. Heart analyzing...", feed_html()]
                for partial in run_debate(case, goals, constraints, model, supplements, guest):
                    dr = partial.get("dr_heart", "*Waiting*")
                    nu = partial.get("nutri", "*Waiting*")
                    lo = partial.get("longevity", "*Waiting*")
                    ho = partial.get("holistics", "*Waiting*")
                    sy = partial.get("synthesizer", "*Working...*")
                    me = partial.get("medi_suppi", "*Waiting*")
                    cnt = sum(1 for x in [nu, lo, ho, sy, me] if x not in ("*Waiting*", "*Working...*"))
                    loading = f"⏳ Running specialists... ({cnt+1}/6)"
                    yield [sy, dr, nu, lo, ho, me, "", loading, feed_html()]
                results, did, url = partial if isinstance(partial, tuple) else (None, None, None)
                share = f"**Saved!** [Open debate]({url}) | ID: `{did}`"
                yield [sy, dr, nu, lo, ho, me, share, "", feed_html()]

            def on_load(did_raw):
                did = did_raw.strip() if did_raw else ""
                if not did:
                    return ["*Paste a debate ID above*", "", "", "", "", "", "", "", feed_html()]
                d = load_debate(did)
                if not d:
                    return ["⚠️ Not found.", "", "", "", "", "", "", "", feed_html()]
                inc_views(did)
                r = d["results"]
                info = f"**Case:** {d['case']}\n**Goals:** {d['goals']}\n**Constraints:** {d['constraints']}\n**Ran:** {d['timestamp']} | Views: {d['views']+1}\n\n**Share:** [Open debate](https://health-round-table.com/?id={did})"
                return [info, r["synthesizer"], r["dr_heart"], r["nutri"], r["longevity"], r["holistics"], r["medi_suppi"], "", ""]

            start_btn.click(
                fn=on_start,
                inputs=[case_input, goals_input, constraints_input, model_choice, supplements_input, guest_input],
                outputs=[tldr_output, dr_out, nu_out, lo_out, ho_out, me_out, did_info, gr.HTML(), feed_out]
            )
            load_btn.click(fn=on_load, inputs=[did_input],
                          outputs=[did_info, tldr_output, dr_out, nu_out, lo_out, ho_out, me_out, gr.HTML(), feed_out])

        with gr.TabItem("Chat Individually"):
            gr.Markdown("### Chat one-on-one with any agent.")
            with gr.Tabs():
                for agent_key, agent in AGENTS.items():
                    with gr.TabItem(f"{agent['emoji']} {agent['name']}"):
                        gr.HTML(f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">{avatar_img(agent_key, 48)}<span style="font-size:1.2em;"><b>{agent["name"]}</b> {agent["emoji"]}</span></div>')
                        chatbot = gr.Chatbot(label=agent["name"], height=300)
                        msg = gr.Textbox(label=f"Message {agent['name']}", placeholder="Type a message...", lines=2)
                        with gr.Row():
                            send_btn = gr.Button("Send")
                            clear_btn = gr.Button("Clear")
                        model_sel = gr.Dropdown(["qwen2.5:7b", "deepseek-v3.2", "qwen3-vl:235b-instruct", "gemma3:27b", "minimax-m2.7"], value="qwen2.5:7b", label="Model")
                        def send_message(msg, history, model):
                            if not msg or not msg.strip():
                                return "", history
                            try:
                                response = chat(model, agent["system"], [{"role": "user", "content": m[0]} for m in history] + [{"role": "user", "content": msg}])
                            except Exception as e:
                                response = f"⚠️ {str(e)}"
                            history.append({"role": "user", "content": msg})
                            history.append({"role": "assistant", "content": response})
                            return "", history
                        send_btn.click(fn=send_message, inputs=[msg, chatbot, model_sel], outputs=[msg, chatbot])
                        msg.submit(fn=send_message, inputs=[msg, chatbot, model_sel], outputs=[msg, chatbot])
                        clear_btn.click(fn=lambda: ("", []), outputs=[msg, chatbot])

demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)))
