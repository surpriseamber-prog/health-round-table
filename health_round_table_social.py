import gradio as gr
import requests
import uuid
import time
import hashlib
from datetime import datetime

API_KEY = "939d10536ea749c2ac9f1ae783335eaa.L8GP6pNpV7FVESvej9RAoDTT"
BASE_URL = "https://ollama.com"
headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# Avatar URLs
AVATARS = {
    "synthesizer": "https://raw.githubusercontent.com/surpriseamber-prog/health-round-table/main/static/avatars/avatar_synthesizer.jpg",
    "dr_heart": "https://raw.githubusercontent.com/surpriseamber-prog/health-round-table/main/static/avatars/avatar_dr_heart.jpg",
    "nutri": "https://raw.githubusercontent.com/surpriseamber-prog/health-round-table/main/static/avatars/avatar_nutri.jpg",
    "longevity": "https://raw.githubusercontent.com/surpriseamber-prog/health-round-table/main/static/avatars/avatar_longevity.jpg",
    "holistics": "https://raw.githubusercontent.com/surpriseamber-prog/health-round-table/main/static/avatars/avatar_holistics.jpg",
    "medi_suppi": "https://raw.githubusercontent.com/surpriseamber-prog/health-round-table/main/static/avatars/avatar_medi_suppi.jpg",
}

def avatar_html(key, label, emoji, size=48):
    url = AVATARS[key]
    return f'''<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
    <img src="{url}" width="{size}" height="{size}" style="border-radius:50%;object-fit:cover;">
    <span style="font-size:1.1em;font-weight:600;">{label}</span>
    <span style="font-size:1.2em;">{emoji}</span>
</div>'''

# --- Debate Storage (in-memory, resets on Render sleep) ---
debates_db = {}  # debate_id -> {case, goals, constraints, model, supplements, results, timestamp, views}

def make_debate_id():
    return hashlib.md5(str(time.time()).encode()).hexdigest()[:8]

def save_debate(case, goals, constraints, model, supplements, results):
    debate_id = make_debate_id()
    debates_db[debate_id] = {
        "case": case,
        "goals": goals,
        "constraints": constraints,
        "model": model,
        "supplements": supplements,
        "results": results,
        "timestamp": datetime.now().strftime("%b %d, %Y %I:%M %p"),
        "views": 0,
    }
    return debate_id

def get_debate(debate_id):
    d = debates_db.get(debate_id)
    if d:
        d["views"] += 1
    return d

def get_recent_debates():
    items = []
    for did, d in debates_db.items():
        case_preview = (d["case"][:80] + "...") if len(d["case"]) > 80 else d["case"]
        case_preview = case_preview.replace("\n", " ")
        items.append((did, case_preview, d["timestamp"], d["views"]))
    items.sort(key=lambda x: x[3], reverse=True)
    return items[:20]

# --- API calls ---
def chat(model, system, user_message):
    payload = {"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user_message}], "stream": False}
    response = requests.post(f"{BASE_URL}/api/chat", headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"Error {response.status_code}: {response.text}")
    return response.json()["message"]["content"]

def run_round_table(case, goals, constraints, model_choice, supplements):
    context = ""
    if goals:
        context += f"\n\nPATIENT GOALS:\n{goals}"
    if constraints:
        context += f"\n\nIMPORTANT CONSTRAINTS:\n{constraints}"

    dr_heart_system = f"""You are Dr. Heart, a board-certified cardiologist. Focus on BP, cholesterol, circulation.{context}
IMPORTANT: Give practical, actionable advice. Use bullet points. Keep responses focused."""
    try:
        dr_heart_response = chat(model_choice, dr_heart_system, f"Analyze: {case}")
    except Exception as e:
        dr_heart_response = f"Error: {str(e)}"

    nutri_system = f"""You are Nutri, a functional medicine nutritionist. Build on Dr. Heart's foundation.{context}
IMPORTANT: Give practical, actionable advice. Use bullet points. Keep responses focused."""
    try:
        nutri_response = chat(model_choice, nutri_system, f"React to Dr. Heart and add nutrition perspective:\n=== DR. HEART ===\n{dr_heart_response}\n=== END ===\nCase: {case}")
    except Exception as e:
        nutri_response = f"Error: {str(e)}"

    longevity_system = f"""You are Longevity, a longevity researcher. Add anti-aging perspective.{context}
IMPORTANT: Give practical, actionable advice. Use bullet points. Keep responses focused."""
    try:
        longevity_response = chat(model_choice, longevity_system, f"Build on Dr. Heart and Nutri:\n=== DR. HEART ===\n{dr_heart_response}\n=== NUTRI ===\n{nutri_response}\n=== END ===\nCase: {case}")
    except Exception as e:
        longevity_response = f"Error: {str(e)}"

    holistics_system = f"""You are Holistics, an integrative medicine practitioner. Add holistic and mind-body perspective.{context}
IMPORTANT: Give practical, actionable advice. Use bullet points. Keep responses focused."""
    try:
        holistics_response = chat(model_choice, holistics_system, f"Build on all previous:\n=== DR. HEART ===\n{dr_heart_response}\n=== NUTRI ===\n{nutri_response}\n=== LONGEVITY ===\n{longevity_response}\n=== END ===\nCase: {case}")
    except Exception as e:
        holistics_response = f"Error: {str(e)}"

    synthesizer_system = f"""You are the Synthesizer, a medical professor. Create consensus recommendations.{context}
IMPORTANT: Give exactly 3 clear numbered recommendations (1. 2. 3.) that integrate all specialist input."""
    try:
        synthesizer_response = chat(model_choice, synthesizer_system, f"Create consensus:\n=== DR. HEART ===\n{dr_heart_response}\n=== NUTRI ===\n{nutri_response}\n=== LONGEVITY ===\n{longevity_response}\n=== HOLISTICS ===\n{holistics_response}\n=== END ===")
    except Exception as e:
        synthesizer_response = f"Error: {str(e)}"

    medi_response = ""
    if supplements and supplements.strip():
        medi_system = """You are Medi/Suppi, a pharmacology and supplement safety specialist. Flag drug and supplement interactions, age-related risks, and potential harms.
IMPORTANT: Not medical advice - educational safety checker only.
Always include: "Always consult your doctor or pharmacist before making changes."
Give: 1. CONCERNS 2. WATCH LIST 3. GENERAL GUIDANCE"""
        medi_prompt = f"""Check for safety concerns:\nSUPPLEMENTS/MEDICATIONS:\n{supplements}\n\nCASE: {case}\nGOALS: {goals}\nCONSTRAINTS: {constraints}"""
        try:
            medi_response = chat(model_choice, medi_system, medi_prompt)
        except Exception as e:
            medi_response = f"Error: {str(e)}"
    else:
        medi_response = "No supplements listed. Enter what you're taking above to get interaction warnings."

    results = {
        "synthesizer": synthesizer_response,
        "dr_heart": dr_heart_response,
        "nutri": nutri_response,
        "longevity": longevity_response,
        "holistics": holistics_response,
        "medi_suppi": medi_response,
    }
    debate_id = save_debate(case, goals, constraints, model_choice, supplements, results)
    return debate_id, results

# --- Gradio UI ---
def build_feed_list():
    debates = get_recent_debates()
    if not debates:
        return "*No debates yet. Be the first to submit a case!*"
    lines = ["| Case Preview | Date | Views | Link |", "|------|------|-------|------|"]
    for did, case_preview, timestamp, views in debates:
        link = f"[View →](/?id={did})"
        lines.append(f"| {case_preview} | {timestamp} | {views} | {link} |")
    return "\n".join(lines)

def build_ui():
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
                            value="mistral-large-3:675b",
                            label="Model"
                        )
                        supplements_input = gr.Textbox(label="Supplements + Medications", placeholder="List vitamins, supplements, Rx meds...", lines=2)

                with gr.Row():
                    start_btn = gr.Button("🚀 Start Round Table", variant="primary")
                    clear_btn = gr.Button("Clear")

                share_output = gr.HTML(visible=False)
                loading_status = gr.HTML("<div style='padding:10px;color:#f97316;font-weight:bold;'>Processing... 6 agents are thinking (1-3 minutes)...</div>", visible=True)

                # Results shown inline after processing
                tldr_label = gr.Markdown("## 💡 Synthesizer — Key Recommendations", visible=False)
                tldr_output = gr.Markdown(visible=False)

                dr_heart_label = gr.Markdown("## ❤️ Dr. Heart — Cardiology", visible=False)
                dr_heart_output = gr.Markdown(visible=False)

                nutri_label = gr.Markdown("## 🥑 Nutri — Functional Nutrition", visible=False)
                nutri_output = gr.Markdown(visible=False)

                longevity_label = gr.Markdown("## ⏳ Longevity — Anti-Aging Research", visible=False)
                longevity_output = gr.Markdown(visible=False)

                holistics_label = gr.Markdown("## 🌿 Holistics — Integrative Medicine", visible=False)
                holistics_output = gr.Markdown(visible=False)

                medi_label = gr.Markdown("## 💊 Medi/Suppi — Drug + Supplement Safety", visible=False)
                medi_output = gr.Markdown(visible=False)

                gr.Markdown("*Each specialist reads all previous analyses. Medi/Suppi checks your supplements for interactions.*")

            # === RECENT DEBATES TAB ===
            with gr.TabItem("📖 Recent Debates"):
                gr.Markdown("### Community Debates\n*Click any link to view that debate*")
                feed_display = gr.HTML()
                demo.load(fn=build_feed_list, inputs=[], outputs=[feed_display])

                gr.Markdown("---")
                gr.Markdown("### Load a Specific Debate by ID")
                debate_id_input = gr.Textbox(label="Debate ID", placeholder="Paste the debate ID here", lines=1)
                view_btn = gr.Button("🔍 Load")
                debate_case_display = gr.Markdown("*No debate loaded*")
                debate_output = gr.Markdown("*No debate loaded*")

            # === ABOUT TAB ===
            with gr.TabItem("ℹ️ About"):
                gr.Markdown("""## 🌵 Health Round Table

A multi-agent AI debate platform where 6 specialized health agents analyze your case together — each building on the others.

**The Agents:**
- ❤️ **Dr. Heart** — Cardiologist (BP, cholesterol, circulation)
- 🥑 **Nutri** — Functional Nutritionist (food as medicine)
- ⏳ **Longevity** — Anti-Aging Researcher
- 🌿 **Holistics** — Integrative Medicine Practitioner
- 💡 **Synthesizer** — Medical Professor (creates consensus)
- 💊 **Medi/Suppi** — Supplement & Drug Safety Checker

**How it works:**
1. Submit a patient case with goals and constraints
2. All 6 agents analyze it, each reading previous agents' responses
3. Get a synthesized consensus with 3 key recommendations
4. Share the debate with anyone via link

*⚠️ Not medical advice. Always consult a healthcare provider.*""")

        def show_results(case, goals, constraints, model_choice, supplements):
            debate_id, results = run_round_table(case, goals, constraints, model_choice, supplements)
            share_url = f"https://health-round-table.onrender.com/?id={debate_id}"
            r = results
            return [
                gr.update(visible=False),  # loading - hide
                f"### 🔗 [Share this debate]({share_url})",
                gr.update(visible=True),
                r["synthesizer"],
                gr.update(visible=True),
                r["dr_heart"],
                gr.update(visible=True),
                r["nutri"],
                gr.update(visible=True),
                r["longevity"],
                gr.update(visible=True),
                r["holistics"],
                gr.update(visible=True),
                r["medi_suppi"],
            ]

        def clear_all_fields():
            return [None, None, None, None, None, None, None, None, None, None, None, None, None]

        start_btn.click(
            fn=show_results,
            inputs=[case_input, goals_input, constraints_input, model_choice, supplements_input],
            outputs=[
                loading_status,
                share_output,
                tldr_label, tldr_output,
                dr_heart_label, dr_heart_output,
                nutri_label, nutri_output,
                longevity_label, longevity_output,
                holistics_label, holistics_output,
                medi_label, medi_output,
            ]
        )

        clear_btn.click(
            fn=clear_all_fields,
            inputs=[],
            outputs=[case_input, goals_input, constraints_input, model_choice, supplements_input, loading_status, share_output, tldr_label, tldr_output, dr_heart_label, dr_heart_output, nutri_label, nutri_output, longevity_label, longevity_output, holistics_label, holistics_output, medi_label, medi_output]
        )

        def load_debate(debate_id):
            d = get_debate(debate_id)
            if not d:
                return ["⚠️ Debate not found.", ""] + [None] * 12
            r = d["results"]
            header = f"**Case:** {d['case']}\n\n**Goals:** {d['goals']}\n\n**Constraints:** {d['constraints']}\n\n**Model:** {d['model']} | **Ran:** {d['timestamp']}"
            return [
                header,
                f"## 💡 Synthesizer\n{r['synthesizer']}",
                f"## ❤️ Dr. Heart\n{r['dr_heart']}",
                f"## 🥑 Nutri\n{r['nutri']}",
                f"## ⏳ Longevity\n{r['longevity']}",
                f"## 🌿 Holistics\n{r['holistics']}",
                f"## 💊 Medi/Suppi\n{r['medi_suppi']}",
            ] + [None] * 6  # pad to match expected outputs

        view_btn.click(
            fn=load_debate,
            inputs=[debate_id_input],
            outputs=[debate_case_display, debate_output, tldr_label, tldr_output, dr_heart_label, dr_heart_output, nutri_label, nutri_output, longevity_label, longevity_output, holistics_label, holistics_output, medi_label, medi_output]
        )

    return demo

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 7861))
    print(f"Starting Health Round Table on port {port}...")
    demo = build_ui()
    demo.launch(server_name="0.0.0.0", server_port=port)
