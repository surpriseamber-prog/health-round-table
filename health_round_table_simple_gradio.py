import gradio as gr
import requests

API_KEY = "939d10536ea749c2ac9f1ae783335eaa.L8GP6pNpV7FVESvej9RAoDTT"
BASE_URL = "https://ollama.com"

headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

def chat(model, system, user_message):
    payload = {"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user_message}], "stream": False}
    response = requests.post(f"{BASE_URL}/api/chat", headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"Error {response.status_code}: {response.text}")
    return response.json()["message"]["content"]

def run_round_table(case, goals, constraints, model_choice):
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

    # Return individual responses for Accordion components
    return synthesizer_response, dr_heart_response, nutri_response, longevity_response, holistics_response

def build_ui():
    with gr.Blocks(title="Health Round Table") as demo:
        gr.Markdown("# Health Round Table\n*Not medical advice - for educational debate only*")

        with gr.Row():
            with gr.Column(scale=3):
                case_input = gr.Textbox(label="Patient Case", placeholder="42yo male, BP 145/95, fatigue...", lines=5)
            with gr.Column(scale=1):
                goals_input = gr.Textbox(label="Goals", placeholder="Lower BP, more energy...", lines=2)
                constraints_input = gr.Textbox(label="Constraints", placeholder="No pharma, vegetarian...", lines=2)
                model_choice = gr.Dropdown(
                    choices=["mistral-large-3:675b", "qwen3-vl:235b-instruct", "deepseek-v3.2"],
                    value="mistral-large-3:675b",
                    label="Model"
                )

        start_btn = gr.Button("Start Round Table", variant="primary")
        clear_btn = gr.Button("Clear")

        # TLDR box at top
        tldr_output = gr.Textbox(label="TLDR - Top 3 Recommendations", lines=6, interactive=False, visible=False)

        # Accordion sections for each agent (collapsed by default)
        with gr.Accordion("TLDR - Key Recommendations", open=True) as tldr_accordion:
            tldr_output_internal = gr.Markdown("Run a case to see recommendations here.")

        with gr.Accordion("Dr. Heart (Cardiology)", open=False):
            dr_heart_output = gr.Markdown("*Waiting for Dr. Heart...*")

        with gr.Accordion("Nutri (Functional Nutrition)", open=False):
            nutri_output = gr.Markdown("*Waiting for Nutri...*")

        with gr.Accordion("Longevity (Anti-Aging Research)", open=False):
            longevity_output = gr.Markdown("*Waiting for Longevity...*")

        with gr.Accordion("Holistics (Integrative Medicine)", open=False):
            holistics_output = gr.Markdown("*Waiting for Holistics...*")

        with gr.Accordion("Synthesizer (Consensus)", open=False):
            synthesizer_output = gr.Markdown("*Waiting for Synthesizer...*")

        gr.Markdown("*Each specialist reads all previous analyses before responding. Click headers above to expand/collapse.*")

        def clear_all():
            return [None, None, None, None, None, None, None, None, None, None, None]

        def update_outputs(synth, dr, nutri, long, hol):
            return [
                gr.update(visible=True, value=synth),
                gr.update(visible=True, value=synth),
                gr.update(value=dr),
                gr.update(value=nutri),
                gr.update(value=long),
                gr.update(value=hol)
            ]

        start_btn.click(
            fn=run_round_table,
            inputs=[case_input, goals_input, constraints_input, model_choice],
            outputs=[synthesizer_output, dr_heart_output, nutri_output, longevity_output, holistics_output]
        )
        start_btn.click(fn=lambda: gr.update(visible=True), outputs=[tldr_output])

        clear_btn.click(
            fn=clear_all,
            inputs=[],
            outputs=[case_input, goals_input, constraints_input, model_choice, tldr_output, dr_heart_output, nutri_output, longevity_output, holistics_output, synthesizer_output]
        )

    return demo

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 7861))
    print(f"Starting Health Round Table on port {port}...")
    demo = build_ui()
    demo.launch(server_name="0.0.0.0", server_port=port)