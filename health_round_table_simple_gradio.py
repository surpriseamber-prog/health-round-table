import gradio as gr
import requests
import os

API_KEY = "939d10536ea749c2ac9f1ae783335eaa.L8GP6pNpV7FVESvej9RAoDTT"
BASE_URL = "https://ollama.com"

headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# Avatar image paths (served from static folder)
AVATARS = {
    "synthesizer": "avatars/avatar_synthesizer.jpg",
    "dr_heart": "avatars/avatar_dr_heart.jpg",
    "nutri": "avatars/avatar_nutri.jpg",
    "longevity": "avatars/avatar_longevity.jpg",
    "holistics": "avatars/avatar_holistics.jpg",
    "medi_suppi": "avatars/avatar_medi_suppi.jpg"
}

def avatar_html(key, label, emoji):
    """Build an HTML snippet with avatar image + agent label."""
    path = AVATARS[key]
    return f'''<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
    <img src="/static/{path}" width="48" height="48" style="border-radius:50%;object-fit:cover;">
    <span style="font-size:1.1em;font-weight:600;">{label}</span>
    <span style="font-size:1.2em;">{emoji}</span>
</div>'''

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

    # Dr. Heart
    dr_heart_system = f"""You are Dr. Heart, a board-certified cardiologist. Focus on BP, cholesterol, circulation.{context}
IMPORTANT: Give practical, actionable advice. Use bullet points. Keep responses focused."""
    try:
        dr_heart_response = chat(model_choice, dr_heart_system, f"Analyze: {case}")
    except Exception as e:
        dr_heart_response = f"Error: {str(e)}"

    # Nutri
    nutri_system = f"""You are Nutri, a functional medicine nutritionist. Build on Dr. Heart's foundation.{context}
IMPORTANT: Give practical, actionable advice. Use bullet points. Keep responses focused."""
    try:
        nutri_response = chat(model_choice, nutri_system, f"React to Dr. Heart and add nutrition perspective:\n=== DR. HEART ===\n{dr_heart_response}\n=== END ===\nCase: {case}")
    except Exception as e:
        nutri_response = f"Error: {str(e)}"

    # Longevity
    longevity_system = f"""You are Longevity, a longevity researcher. Add anti-aging perspective.{context}
IMPORTANT: Give practical, actionable advice. Use bullet points. Keep responses focused."""
    try:
        longevity_response = chat(model_choice, longevity_system, f"Build on Dr. Heart and Nutri:\n=== DR. HEART ===\n{dr_heart_response}\n=== NUTRI ===\n{nutri_response}\n=== END ===\nCase: {case}")
    except Exception as e:
        longevity_response = f"Error: {str(e)}"

    # Holistics
    holistics_system = f"""You are Holistics, an integrative medicine practitioner. Add holistic and mind-body perspective.{context}
IMPORTANT: Give practical, actionable advice. Use bullet points. Keep responses focused."""
    try:
        holistics_response = chat(model_choice, holistics_system, f"Build on all previous:\n=== DR. HEART ===\n{dr_heart_response}\n=== NUTRI ===\n{nutri_response}\n=== LONGEVITY ===\n{longevity_response}\n=== END ===\nCase: {case}")
    except Exception as e:
        holistics_response = f"Error: {str(e)}"

    # Synthesizer
    synthesizer_system = f"""You are the Synthesizer, a medical professor. Create consensus recommendations.{context}
IMPORTANT: Give exactly 3 clear numbered recommendations (1. 2. 3.) that integrate all specialist input."""
    try:
        synthesizer_response = chat(model_choice, synthesizer_system, f"Create consensus:\n=== DR. HEART ===\n{dr_heart_response}\n=== NUTRI ===\n{nutri_response}\n=== LONGEVITY ===\n{longevity_response}\n=== HOLISTICS ===\n{holistics_response}\n=== END ===")
    except Exception as e:
        synthesizer_response = f"Error: {str(e)}"

    # Medi/Suppi
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

    return "", synthesizer_response, dr_heart_response, nutri_response, longevity_response, holistics_response, medi_response

def clear_all():
    return [None, None, None, None, None, None, None, None, None, None, None, None, None]

def build_ui():
    with gr.Blocks(title="Health Round Table") as demo:
        gr.Markdown("# Health Round Table\n*Not medical advice — for educational debate only*")

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
            start_btn = gr.Button("Start Round Table", variant="primary")
            clear_btn = gr.Button("Clear")

        loading_status = gr.HTML(
            "<div style='padding:10px;color:#f97316;font-weight:bold;'>Processing... 6 agents are thinking (1-3 minutes)...</div>",
            visible=True
        )

        # TLDR Summary
        with gr.Accordion("💡 TLDR — Key Recommendations", open=True):
            tldr_output = gr.Markdown("*Run a case to see recommendations*")

        # Dr. Heart
        with gr.Accordion("Dr. Heart (Cardiology)", open=False):
            gr.HTML(avatar_html("dr_heart", "Dr. Heart", "❤️"))
            dr_heart_output = gr.Markdown("*Waiting for Dr. Heart...*")

        # Nutri
        with gr.Accordion("Nutri (Functional Nutrition)", open=False):
            gr.HTML(avatar_html("nutri", "Nutri", "🍔"))
            nutri_output = gr.Markdown("*Waiting for Nutri...*")

        # Longevity
        with gr.Accordion("Longevity (Anti-Aging Research)", open=False):
            gr.HTML(avatar_html("longevity", "Longevity", "⏳"))
            longevity_output = gr.Markdown("*Waiting for Longevity...*")

        # Holistics
        with gr.Accordion("Holistics (Integrative Medicine)", open=False):
            gr.HTML(avatar_html("holistics", "Holistics", "🌿"))
            holistics_output = gr.Markdown("*Waiting for Holistics...*")

        # Medi/Suppi
        with gr.Accordion("Medi/Suppi (Drug + Supplement Safety)", open=False):
            gr.HTML(avatar_html("medi_suppi", "Medi/Suppi", "💊"))
            medi_output = gr.Markdown("*Waiting for Medi/Suppi...*")

        gr.Markdown("*Each specialist reads all previous analyses. Medi/Suppi checks your supplements for interactions.*")

        start_btn.click(
            fn=run_round_table,
            inputs=[case_input, goals_input, constraints_input, model_choice, supplements_input],
            outputs=[loading_status, tldr_output, dr_heart_output, nutri_output, longevity_output, holistics_output, medi_output]
        )

        clear_btn.click(fn=clear_all, inputs=[], outputs=[case_input, goals_input, constraints_input, model_choice, supplements_input, loading_status, tldr_output, dr_heart_output, nutri_output, longevity_output, holistics_output, medi_output])

    return demo

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 7861))
    print(f"Starting Health Round Table on port {port}...")
    demo = build_ui()
    demo.launch(server_name="0.0.0.0", server_port=port)
