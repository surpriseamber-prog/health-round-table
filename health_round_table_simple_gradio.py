import gradio as gr
import requests
import uuid

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
IMPORTANT: Give practical, actionable advice. Use bullet points. Keep responses focused and readable."""
    try:
        dr_heart_response = chat(model_choice, dr_heart_system, f"Analyze: {case}")
    except Exception as e:
        dr_heart_response = f"Error: {str(e)}"

    # Nutri
    nutri_system = f"""You are Nutri, a functional medicine nutritionist. Build on Dr. Heart's foundation.{context}
IMPORTANT: Give practical, actionable advice. Use bullet points. Keep responses focused and readable."""
    try:
        nutri_response = chat(model_choice, nutri_system, f"React to Dr. Heart and add nutrition perspective:\n=== DR. HEART ===\n{dr_heart_response}\n=== END ===\nCase: {case}")
    except Exception as e:
        nutri_response = f"Error: {str(e)}"

    # Longevity
    longevity_system = f"""You are Longevity, a longevity researcher. Add anti-aging perspective.{context}
IMPORTANT: Give practical, actionable advice. Use bullet points. Keep responses focused and readable."""
    try:
        longevity_response = chat(model_choice, longevity_system, f"Build on Dr. Heart and Nutri:\n=== DR. HEART ===\n{dr_heart_response}\n=== NUTRI ===\n{nutri_response}\n=== END ===\nCase: {case}")
    except Exception as e:
        longevity_response = f"Error: {str(e)}"

    # Holistics
    holistics_system = f"""You are Holistics, an integrative medicine practitioner. Add holistic and mind-body perspective.{context}
IMPORTANT: Give practical, actionable advice. Use bullet points. Keep responses focused and readable."""
    try:
        holistics_response = chat(model_choice, holistics_system, f"Build on all previous:\n=== DR. HEART ===\n{dr_heart_response}\n=== NUTRI ===\n{nutri_response}\n=== LONGEVITY ===\n{longevity_response}\n=== END ===\nCase: {case}")
    except Exception as e:
        holistics_response = f"Error: {str(e)}"

    # Synthesizer
    synthesizer_system = f"""You are the Synthesizer, a medical professor. Create consensus recommendations.{context}
IMPORTANT: Give exactly 3 clear numbered recommendations (1. 2. 3.) that integrate all specialist input. Start with the 3 recommendations as a TLDR, then explain briefly."""
    try:
        synthesizer_response = chat(model_choice, synthesizer_system, f"Create consensus:\n=== DR. HEART ===\n{dr_heart_response}\n=== NUTRI ===\n{nutri_response}\n=== LONGEVITY ===\n{longevity_response}\n=== HOLISTICS ===\n{holistics_response}\n=== END ===")
    except Exception as e:
        synthesizer_response = f"Error: {str(e)}"

    # Build output with TLDR first, then collapsible agent sections
    debate_id = str(uuid.uuid4())[:8]
    share_url = f"https://health-round-table.onrender.com/?debate={debate_id}"

    output = f"""## TLDR — Key Recommendations

{synthesizer_response}

---

## Dr. Heart (Cardiology)
{dr_heart_response}

---

## Nutri (Functional Nutrition)
{nutri_response}

---

## Longevity (Anti-Aging Research)
{longevity_response}

---

## Holistics (Integrative Medicine)
{holistics_response}

---

**Debate ID:** `{debate_id}` | **Share this debate:** Copy the link above

---
*Not medical advice - for educational debate only.*
"""

    return output, share_url

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

        # TLDR + Results output
        output_md = gr.Markdown(label="Discussion Results", visible=False)
        share_box = gr.Textbox(label="Share this debate - copy link below", interactive=False, visible=False, lines=1)

        def clear_all():
            return None, None, None, None, "", "", "", ""

        start_btn.click(fn=lambda: gr.update(visible=True), outputs=[output_md])
        start_btn.click(
            fn=run_round_table,
            inputs=[case_input, goals_input, constraints_input, model_choice],
            outputs=[output_md, share_box]
        )
        start_btn.click(fn=lambda: gr.update(visible=True), outputs=[share_box])

        clear_btn.click(
            fn=clear_all,
            inputs=[],
            outputs=[case_input, goals_input, constraints_input, model_choice, output_md, share_box]
        )
        clear_btn.click(fn=lambda: (gr.update(visible=False), gr.update(visible=False)), outputs=[output_md, share_box])

        gr.Markdown("*Each specialist reads all previous analyses before responding. Click the headers above to expand/collapse each agent's full response.*")

    return demo

if __name__ == "__main__":
    demo = build_ui()
    demo.launch(server_name="0.0.0.0", server_port=7861)