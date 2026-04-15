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

def get_recent_debates(limit=20):
    """Return list of (debate_id, case_preview, timestamp, views) sorted newest first."""
    items = []
    for did, d in debates_db.items():
        case_preview = (d["case"][:80] + "...") if len(d["case"]) > 80 else d["case"]
        case_preview = case_preview.replace("\n", " ")
        items.append((did, case_preview, d["timestamp"], d["views"]))
    items.sort(key=lambda x: x[3], reverse=True)  # sort by views
    return items[:limit]

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
    """Build markdown table of recent debates."""
    debates = get_recent_debates()
    if not debates:
        return "*No debates yet. Be the first to submit a case!*"
    
    lines = ["## Recent Health Debates\n"]
    lines.append("| Case | Date | Views | Link |")
    lines.append("|------|------|-------|------|")
    for did, case_preview, timestamp, views in debates:
        link = f"[View Debate →](/?id={did})"
        lines.append(f"| {case_preview} | {timestamp} | {views} | {link} |")
    return "\n".join(lines)

def view_debate(debate_id):
    """Display a saved debate by ID."""
    d = get_debate(debate_id)
    if not d:
        return "⚠️ Debate not found. It may have been cleared on the last Render sleep. Please run a new case.", "", "", "", "", "", ""
    r = d["results"]
    share_url = f"https://health-round-table.onrender.com/?id={debate_id}"
    header = f"""### 🔗 [Share this debate]({share_url})\n**Case:** {d['case']}\n**Goals:** {d['goals']}\n**Constraints:** {d['constraints']}\n**Model:** {d['model']}\n**Ran:** {d['timestamp']} | **Views:** {d['views']+1}"""
    return header, r["synthesizer"], r["dr_heart"], r["nutri"], r["longevity"], r["holistics"], r["medi_suppi"]

def build_ui():
    with gr.Blocks(title="Health Round Table") as demo:
        gr.Markdown("# 🌵 Health Round Table\n*Not medical advice — for educational debate only*")

        with gr.Tabs():
            # --- Submit Tab ---
            with gr.TabItem("📝 Submit a Case"):
                gr.Markdown("### Submit a health case for the Round Table debate")
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

                loading_status = gr.HTML("<div style='padding:10px;color:#f97316;font-weight:bold;'>Processing... 6 agents are thinking (1-3 minutes)...</div>", visible=False)

                share_output = gr.HTML(visible=False)
                gr.Markdown("*Each specialist reads all previous analyses. Medi/Suppi checks your supplements for interactions.*")

            # --- Recent Debates Tab ---
            with gr.TabItem("📖 Recent Debates"):
                gr.Markdown("### Community Debates\n*Click any debate to view the full discussion*")
                feed_display = gr.HTML()
                demo.load(fn=build_feed_list, inputs=[], outputs=[feed_display])

                gr.Markdown("---")
                gr.Markdown("### View a Debate")
                debate_id_input = gr.Textbox(label="Debate ID", placeholder="Enter debate ID (or use link from feed above)", lines=1)
                view_btn = gr.Button("🔍 Load Debate")
                debate_output = gr.HTML()

            # --- About Tab ---
            with gr.TabItem("ℹ️ About"):
                gr.Markdown("""## 🌵 Health Round Table

A multi-agent AI debate platform where 6 specialized health agents analyze your case together — each reading and building on the others.

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
4. Share the debate link with anyone

*⚠️ Not medical advice. Always consult a healthcare provider.*""")

        # --- Accordion sections (shared across submit + view) ---
        with gr.Accordion("💡 TLDR — Key Recommendations", open=True, visible=False) as tldr_accord:
            tldr_output = gr.Markdown()

        with gr.Accordion("❤️ Dr. Heart (Cardiology)", open=False, visible=False) as dr_heart_accord:
            dr_heart_html = gr.HTML()
            dr_heart_output = gr.Markdown()

        with gr.Accordion("🥑 Nutri (Functional Nutrition)", open=False, visible=False) as nutri_accord:
            nutri_html = gr.HTML()
            nutri_output = gr.Markdown()

        with gr.Accordion("⏳ Longevity (Anti-Aging Research)", open=False, visible=False) as longevity_accord:
            longevity_html = gr.HTML()
            longevity_output = gr.Markdown()

        with gr.Accordion("🌿 Holistics (Integrative Medicine)", open=False, visible=False) as holistics_accord:
            holistics_html = gr.HTML()
            holistics_output = gr.Markdown()

        with gr.Accordion("💊 Medi/Suppi (Drug + Supplement Safety)", open=False, visible=False) as medi_accord:
            medi_html = gr.HTML()
            medi_output = gr.Markdown()

        def show_results(debate_id, results):
            r = results
            share_url = f"https://health-round-table.onrender.com/?id={debate_id}"
            return [
                gr.update(visible=True),
                f"### 🔗 [Share this debate]({share_url})",
                gr.update(visible=True),
                gr.update(visible=True),
                avatar_html("synthesizer", "Synthesizer", "💡"),
                r["synthesizer"],
                gr.update(visible=True),
                gr.update(visible=True),
                avatar_html("dr_heart", "Dr. Heart", "❤️"),
                r["dr_heart"],
                gr.update(visible=True),
                gr.update(visible=True),
                avatar_html("nutri", "Nutri", "🥑"),
                r["nutri"],
                gr.update(visible=True),
                gr.update(visible=True),
                avatar_html("longevity", "Longevity", "⏳"),
                r["longevity"],
                gr.update(visible=True),
                gr.update(visible=True),
                avatar_html("holistics", "Holistics", "🌿"),
                r["holistics"],
                gr.update(visible=True),
                gr.update(visible=True),
                avatar_html("medi_suppi", "Medi/Suppi", "💊"),
                r["medi_suppi"],
            ]

        # Output mapping: [share, share_html, tldr_visible, tldr_accord, tldr_html, tldr_md, dh_visible, dh_accord, dh_html, dh_md, ...]
        all_outputs = [
            share_output,
            tldr_output, tldr_accord, tldr_output,
            dr_heart_output, dr_heart_accord, dr_heart_html, dr_heart_output,
            nutri_output, nutri_accord, nutri_html, nutri_output,
            longevity_output, longevity_accord, longevity_html, longevity_output,
            holistics_output, holistics_accord, holistics_html, holistics_output,
            medi_output, medi_accord, medi_html, medi_output,
        ]

        # Actually map correctly - let's be explicit
        outputs = [
            share_output,
            tldr_output, tldr_accord,
            dr_heart_output, dr_heart_accord,
            nutri_output, nutri_accord,
            longevity_output, longevity_accord,
            holistics_output, holistics_accord,
            medi_output, medi_accord,
        ]

        def run_and_show(case, goals, constraints, model_choice, supplements):
            debate_id, results = run_round_table(case, goals, constraints, model_choice, supplements)
            yield [gr.update(visible=True)] + [None] * 12
            r = results
            share_url = f"https://health-round-table.onrender.com/?id={debate_id}"
            yield [
                f"### 🔗 [Share this debate]({share_url})",
                gr.update(visible=True),
                avatar_html("synthesizer", "Synthesizer", "💡") + r["synthesizer"],
                gr.update(visible=True),
                avatar_html("dr_heart", "Dr. Heart", "❤️") + r["dr_heart"],
                gr.update(visible=True),
                avatar_html("nutri", "Nutri", "🥑") + r["nutri"],
                gr.update(visible=True),
                avatar_html("longevity", "Longevity", "⏳") + r["longevity"],
                gr.update(visible=True),
                avatar_html("holistics", "Holistics", "🌿") + r["holistics"],
                gr.update(visible=True),
                avatar_html("medi_suppi", "Medi/Suppi", "💊") + r["medi_suppi"],
            ]

        start_btn.click(
            fn=run_and_show,
            inputs=[case_input, goals_input, constraints_input, model_choice, supplements_input],
            outputs=outputs
        )

        clear_btn.click(
            fn=lambda: [None] * 13,
            inputs=[],
            outputs=[case_input, goals_input, constraints_input, model_choice, supplements_input, loading_status, share_output, tldr_output, tldr_accord, dr_heart_output, dr_heart_accord, nutri_output, nutri_accord, longevity_output, longevity_accord, holistics_output, holistics_accord, medi_output, medi_accord]
        )

    return demo

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 7861))
    print(f"Starting Health Round Table on port {port}...")
    demo = build_ui()
    demo.launch(server_name="0.0.0.0", server_port=port)
