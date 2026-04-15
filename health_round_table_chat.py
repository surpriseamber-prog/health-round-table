"""
Health Round Table - Chat Interface
Chat with individual agents or run a group round table debate.
"""

import gradio as gr
import requests

API_KEY = "939d10536ea749c2ac9f1ae783335eaa.L8GP6pNpV7FVESvej9RAoDTT"
BASE_URL = "https://ollama.com"

headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# Agent personas
AGENTS = {
    "Dr. Heart": {
        "system": "You are Dr. Heart, a warm, experienced cardiologist in your 50s. You care deeply about your patients. You're direct but kind — you tell people what they need to hear, not what they want to hear. You focus on BP, cholesterol, circulation, and heart health. Always give practical, actionable advice. Keep responses conversational, not clinical. You can be stern when people ignore good health advice.",
        "color": "#e74c3c"
    },
    "Nutri": {
        "system": "You are Nutri, a friendly, practical functional medicine nutritionist. You have a warm, relatable energy — like a supportive friend who happens to be a nutrition expert. You're a mom-energy, real-world focused. You build on what doctors say and add the nutrition layer. You believe food is medicine. Always practical and actionable.",
        "color": "#27ae60"
    },
    "Longevity": {
        "system": "You are Longevity, an enthusiastic longevity researcher in your 30s. You're genuinely excited about anti-aging science and it comes through in everything you say. You simplify complex research into practical takeaways. You believe in optimizing healthspan, not just lifespan. Optimistic but evidence-based.",
        "color": "#9b59b6"
    },
    "Holistics": {
        "system": "You are Holistics, a calm, zen integrative medicine practitioner. You have a relaxed, centered energy — like a thoughtful herbalist and healer. You think about the whole person: body, mind, spirit. You bring in mind-body connections, stress, sleep, and spiritual well-being. You move at a thoughtful pace and speak in a grounding way.",
        "color": "#2ecc71"
    },
    "Medi/Suppi": {
        "system": "You are Medi/Suppi, a sharp, no-nonsense pharmacology and supplement safety specialist. You have a focused, precise energy — you want people safe and informed. You flag risks clearly and speak plainly. You always remind people to check with their doctor. You're the safety guardrail, not the fun one.",
        "color": "#e67e22"
    },
    "Synthesizer": {
        "system": "You are the Synthesizer, a wise medical professor in your 60s. You've seen it all and you synthesize complex inputs into clear, actionable guidance. You're the wise mentor figure — calm, clear, authoritative. You integrate all the specialist perspectives into consensus recommendations. You always give numbered action steps.",
        "color": "#3498db"
    }
}

def chat(model, system, user_message):
    payload = {"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user_message}], "stream": False}
    response = requests.post(f"{BASE_URL}/api/chat", headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"Error {response.status_code}: {response.text}")
    return response.json()["message"]["content"]

def chat_with_agent(agent_name, message, history, model_choice, context):
    """Handle individual agent chat"""
    agent = AGENTS.get(agent_name)
    if not agent:
        return history + [(message, "Unknown agent")]

    prompt = message
    if context and context.strip():
        prompt = f"[CASE CONTEXT]\n{context}\n\n[USER QUESTION]\n{message}"

    try:
        response = chat(model_choice, agent["system"], prompt)
        history.append((message, response))
    except Exception as e:
        history.append((message, f"Error: {str(e)}"))

    return history

def run_round_table_chat(case, goals, constraints, model_choice, history):
    """Run full round table — all 6 agents debate and return complete summary"""
    if not case or case.strip() == "":
        return history + [("Start Round Table", "Please enter a case study first.")], ""

    context = f"Goals: {goals}\nConstraints: {constraints}" if goals or constraints else ""

    # Dr. Heart
    try:
        dr_response = chat(model_choice, AGENTS["Dr. Heart"]["system"], f"Analyze this case:{context}\n\nCase: {case}")
    except:
        dr_response = "Error reaching Dr. Heart."

    # Nutri
    try:
        nutri_response = chat(model_choice, AGENTS["Nutri"]["system"], f"Build on Dr. Heart's analysis and add nutrition perspective:\n=== DR. HEART ===\n{dr_response}\n=== END ===\nCase: {case}\n{context}")
    except:
        nutri_response = "Error reaching Nutri."

    # Longevity
    try:
        long_response = chat(model_choice, AGENTS["Longevity"]["system"], f"Build on Dr. Heart and Nutri:\n=== DR. HEART ===\n{dr_response}\n=== NUTRI ===\n{nutri_response}\n=== END ===\nCase: {case}\n{context}")
    except:
        long_response = "Error reaching Longevity."

    # Holistics
    try:
        hol_response = chat(model_choice, AGENTS["Holistics"]["system"], f"Add integrative/holistic perspective:\n=== DR. HEART ===\n{dr_response}\n=== NUTRI ===\n{nutri_response}\n=== LONGEVITY ===\n{long_response}\n=== END ===\nCase: {case}\n{context}")
    except:
        hol_response = "Error reaching Holistics."

    # Medi/Suppi
    try:
        medi_response = chat(model_choice, AGENTS["Medi/Suppi"]["system"], f"Check for drug/supplement safety concerns:\nCase: {case}\nGoals: {goals}\nConstraints: {constraints}")
    except:
        medi_response = "Error reaching Medi/Suppi."

    # Synthesizer
    try:
        synth_response = chat(model_choice, AGENTS["Synthesizer"]["system"], f"Create final consensus:\n=== DR. HEART ===\n{dr_response}\n=== NUTRI ===\n{nutri_response}\n=== LONGEVITY ===\n{long_response}\n=== HOLISTICS ===\n{hol_response}\n=== MEDI/SUPPI ===\n{medi_response}\n=== END ===")
    except:
        synth_response = "Error reaching Synthesizer."

    # Format as a clean chat summary
    summary = f"""## Round Table Complete

**Case:** {case}

---

**Dr. Heart:** {dr_response}

**Nutri:** {nutri_response}

**Longevity:** {long_response}

**Holistics:** {hol_response}

**Medi/Suppi:** {medi_response}

---

**Synthesizer Consensus:**
{synth_response}

---
*Not medical advice — for educational debate only.*
"""

    history.append(("Run Round Table", f"Running full debate with 6 agents..."))
    return history, summary

def build_ui():
    with gr.Blocks(title="Health Round Table - Chat") as demo:
        gr.Markdown("# Health Round Table - Chat\n*Chat with health specialists or run a full round table debate*")

        with gr.Tab("Individual Agents"):
            with gr.Row():
                with gr.Column(scale=1):
                    agent_selector = gr.Dropdown(
                        choices=list(AGENTS.keys()),
                        value="Dr. Heart",
                        label="Select Agent"
                    )
                    model_choice_chat = gr.Dropdown(
                        choices=["mistral-large-3:675b", "qwen3-vl:235b-instruct", "deepseek-v3.2"],
                        value="mistral-large-3:675b",
                        label="Model"
                    )
                    case_context = gr.Textbox(label="Case Context (optional)", placeholder="Enter case details for more relevant answers...", lines=3)

                with gr.Column(scale=3):
                    gr.ChatInterface(
                        fn=lambda msg, hist, agent_name, model, ctx: chat_with_agent(agent_name, msg, hist, model, ctx),
                        additional_inputs=[agent_selector, model_choice_chat, case_context],
                        title="Chat with Agent"
                    )

        with gr.Tab("Round Table"):
            gr.Markdown("### Run a Full 6-Agent Debate")
            with gr.Row():
                with gr.Column(scale=3):
                    case_input_rt = gr.Textbox(label="Patient Case", placeholder="42yo female, swollen feet, weight 180lbs, fatigue...", lines=4)
                with gr.Column(scale=1):
                    goals_rt = gr.Textbox(label="Goals", placeholder="Lower BP, more energy...", lines=2)
                    constraints_rt = gr.Textbox(label="Constraints", placeholder="No pharma, vegetarian...", lines=2)
                    model_rt = gr.Dropdown(
                        choices=["mistral-large-3:675b", "qwen3-vl:235b-instruct", "deepseek-v3.2"],
                        value="mistral-large-3:675b",
                        label="Model"
                    )

            run_btn = gr.Button("Run Full Round Table Debate", variant="primary")
            debate_output = gr.Markdown("*Results will appear here after the debate*")

            run_btn.click(
                fn=run_round_table_chat,
                inputs=[case_input_rt, goals_rt, constraints_rt, model_rt, gr.State([])],
                outputs=[gr.State([]), debate_output]
            )

        with gr.Tab("About"):
            gr.Markdown("""## Health Round Table Agents

**Dr. Heart** - Cardiology. Warm, direct, caring cardiologist.

**Nutri** - Nutrition. Friendly, practical, food-as-medicine nutritionist.

**Longevity** - Anti-Aging. Enthusiastic researcher, optimizes healthspan.

**Holistics** - Integrative. Zen, whole-person healer.

**Medi/Suppi** - Safety. Sharp pharmacist, flags drug/supplement interactions.

**Synthesizer** - Consensus. Wise professor, integrates all perspectives.

---
*Not medical advice — for educational debate only.*
""")

    return demo

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 7861))
    print("Starting Health Round Table - Chat Interface on port", port)
    demo = build_ui()
    demo.launch(server_name="0.0.0.0", server_port=port)