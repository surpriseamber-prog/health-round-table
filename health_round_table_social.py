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
    return sorted([(k, v) for k, v in debates_db.items()], key=lambda x: x[1]["views"], reverse=True)[:20]

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

    h = f"You are Dr. Heart, cardiologist. Focus on BP, cholesterol, circulation.{ctx}\nGive bullet points."
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
Always include: "Consult your doctor or pharmacist.\""""
        me = ask(m, f"Supplements: {supplements}\nCase: {case}\nGoals: {goals}\nConstraints: {constraints}")
    else:
        me = "No supplements listed."

    results = {"synthesizer": sy, "dr_heart": dr, "nutri": nu, "longevity": lo, "holistics": ho, "medi_suppi": me}
    did = save_debate(case, goals, constraints, model_choice, supplements, results)
    return did, results

def build():
    with gr.Blocks(title="Health Round Table") as demo:
        gr.Markdown("# 🌵 Health Round Table\n*Not medical advice — for educational debate only*")

        with gr.Tabs():
            # === SUBMIT TAB ===
            with gr.TabItem("📝 Submit a Case"):
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

                # Single status output - shows loading then results
                status = gr.HTML("<p style='color:#f97316;'>Ready — enter a case above and click Start</p>")

                # Result outputs - each agent has a label + markdown output
                tldr_lbl = gr.Markdown("## 💡 Synthesizer", visible=False)
                tldr_out = gr.Markdown(visible=False)
                dh_lbl = gr.Markdown("## ❤️ Dr. Heart", visible=False)
                dh_out = gr.Markdown(visible=False)
                nu_lbl = gr.Markdown("## 🥑 Nutri", visible=False)
                nu_out = gr.Markdown(visible=False)
                lo_lbl = gr.Markdown("## ⏳ Longevity", visible=False)
                lo_out = gr.Markdown(visible=False)
                ho_lbl = gr.Markdown("## 🌿 Holistics", visible=False)
                ho_out = gr.Markdown(visible=False)
                me_lbl = gr.Markdown("## 💊 Medi/Suppi", visible=False)
                me_out = gr.Markdown(visible=False)

                gr.Markdown("*Each specialist reads all previous analyses.*")

                def on_start(case, goals, constraints, model, supplements):
                    # Show loading
                    yield [gr.HTML("<p style='color:#f97316;font-weight:bold;'>⏳ Processing... 6 agents are thinking (1-3 minutes)...</p>"),
                           None, None, None, None, None, None, None, None, None, None, None, None, None]
                    did, r = run_round_table(case, goals, constraints, model, supplements)
                    url = f"https://health-round-table.onrender.com/?id={did}"
                    yield [
                        gr.HTML(f"<p style='color:#22c55e;'><b>✅ Done!</b> <a href='{url}' target='_blank'>Share this debate</a></p>"),
                        gr.update(visible=True), r["synthesizer"],
                        gr.update(visible=True), r["dr_heart"],
                        gr.update(visible=True), r["nutri"],
                        gr.update(visible=True), r["longevity"],
                        gr.update(visible=True), r["holistics"],
                        gr.update(visible=True), r["medi_suppi"],
                    ]

                def on_clear():
                    return [gr.HTML("<p style='color:#f97316;'>Ready — enter a case above and click Start</p>"),
                            None, None, None, None, None, None, None, None, None, None, None, None, None]

                start_btn.click(
                    fn=on_start,
                    inputs=[case_input, goals_input, constraints_input, model_choice, supplements_input],
                    outputs=[status, tldr_lbl, tldr_out, dh_lbl, dh_out, nu_lbl, nu_out, lo_lbl, lo_out, ho_lbl, ho_out, me_lbl, me_out]
                )
                clear_btn.click(fn=on_clear, inputs=[], outputs=[status, tldr_lbl, tldr_out, dh_lbl, dh_out, nu_lbl, nu_out, lo_lbl, lo_out, ho_lbl, ho_out, me_lbl, me_out])

            # === RECENT TAB ===
            with gr.TabItem("📖 Recent Debates"):
                gr.Markdown("### Community Debates")
                feed = gr.HTML()
                demo.load(fn=lambda: build_feed(), inputs=[], outputs=[feed])
                with gr.Row():
                    did_input = gr.Textbox(label="Debate ID", placeholder="Paste debate ID", lines=1)
                    view_btn = gr.Button("🔍 Load")
                did_out = gr.Markdown("*Paste a debate ID above to load it*")
                view_btn.click(
                    fn=on_load_did,
                    inputs=[did_input],
                    outputs=[did_out, tldr_lbl, tldr_out, dh_lbl, dh_out, nu_lbl, nu_out, lo_lbl, lo_out, ho_lbl, ho_out, me_lbl, me_out]
                )

            # === ABOUT TAB ===
            with gr.TabItem("ℹ️ About"):
                gr.Markdown("""## 🌵 Health Round Table

6 specialized AI agents debate your health case — each reading and building on the others.

- ❤️ **Dr. Heart** — Cardiology
- 🥑 **Nutri** — Functional Nutrition  
- ⏳ **Longevity** — Anti-Aging Research
- 🌿 **Holistics** — Integrative Medicine
- 💡 **Synthesizer** — Consensus
- 💊 **Medi/Suppi** — Supplement Safety

⚠️ Not medical advice.
""")

    return demo

def on_load_did(did):
    d = get_debate(did)
    if not d:
        return ["⚠️ Debate not found.", None, None, None, None, None, None, None, None, None, None, None, None]
    r = d["results"]
    header = f"**Case:** {d['case']}\n**Goals:** {d['goals']}\n**Constraints:** {d['constraints']}\n**Ran:** {d['timestamp']}"
    return [
        header,
        gr.update(visible=True), r["synthesizer"],
        gr.update(visible=True), r["dr_heart"],
        gr.update(visible=True), r["nutri"],
        gr.update(visible=True), r["longevity"],
        gr.update(visible=True), r["holistics"],
        gr.update(visible=True), r["medi_suppi"],
    ]

def build_feed():
    debates = get_recent()
    if not debates:
        return "*No debates yet. Submit the first case!*"
    rows = ["| Case Preview | Date | Views | Link |", "|------|------|-------|------|"]
    for did, d in debates:
        prev = (d["case"][:70]+"...") if len(d["case"])>70 else d["case"]
        prev = prev.replace("\n"," ")
        rows.append(f"| {prev} | {d['timestamp']} | {d['views']} | [View →](/?id={did}) |")
    return "\n".join(rows)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 7861))
    print(f"Starting on port {port}...")
    build().launch(server_name="0.0.0.0", server_port=port)
