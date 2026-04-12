"""
Health Round Table - Gradio Simple Version (Non-Streaming)
Agents complete sequentially then display all results.
"""

import gradio as gr
import requests

API_KEY = "939d10536ea749c2ac9f1ae783335eaa.L8GP6pNpV7FVESvej9RAoDTT"
BASE_URL = "https://ollama.com"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def chat(model, system, user_message):
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_message}
        ],
        "stream": False
    }
    response = requests.post(f"{BASE_URL}/api/chat", headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"Error {response.status_code}: {response.text}")
    return response.json()["message"]["content"]

def run_round_table(case, goals, constraints, model_choice):
    """Run all agents sequentially, return full discussion"""
    
    context = ""
    if goals:
        context += f"\n\nPATIENT GOALS:\n{goals}"
    if constraints:
        context += f"\n\nIMPORTANT CONSTRAINTS:\n{constraints}"
    
    all_responses = []
    
    # === DR. HEART ===
    all_responses.append(("❤️ Dr. Heart", "Analyzing case from cardiology perspective..."))
    dr_heart_system = f"""You are Dr. Heart, a board-certified cardiologist. Focus on BP, cholesterol, circulation.{context}
IMPORTANT: Give practical, actionable advice."""
    try:
        dr_heart_response = chat(model_choice, dr_heart_system, 
            f"Analyze: {case}")
        all_responses.append(("❤️ Dr. Heart", dr_heart_response))
    except Exception as e:
        all_responses.append(("❤️ Dr. Heart", f"Error: {str(e)}"))
        return all_responses
    
    # === NUTRI ===
    all_responses.append(("🍔 Nutri", "Reviewing Dr. Heart's analysis..."))
    nutri_system = f"""You are Nutri, a functional medicine nutritionist. Build on Dr. Heart's foundation.{context}"""
    try:
        nutri_response = chat(model_choice, nutri_system,
            f"React to Dr. Heart and add nutrition perspective:\n=== DR. HEART ===\n{dr_heart_response}\n=== END ===\nCase: {case}")
        all_responses.append(("🍔 Nutri", nutri_response))
    except Exception as e:
        all_responses.append(("🍔 Nutri", f"Error: {str(e)}"))
        return all_responses
    
    # === LONGEVITY ===
    all_responses.append(("⌛ Longevity", "Building on previous analyses..."))
    longevity_system = f"""You are Longevity, a longevity researcher. Add anti-aging perspective.{context}"""
    try:
        longevity_response = chat(model_choice, longevity_system,
            f"Build on Dr. Heart and Nutri:\n=== DR. HEART ===\n{dr_heart_response}\n=== NUTRI ===\n{nutri_response}\n=== END ===\nCase: {case}")
        all_responses.append(("⌛ Longevity", longevity_response))
    except Exception as e:
        all_responses.append(("⌛ Longevity", f"Error: {str(e)}"))
        return all_responses
    
    # === HOLISTICS ===
    all_responses.append(("🌿 Holistics", "Adding integrative perspective..."))
    holistics_system = f"""You are Holistics, integrative medicine practitioner.{context}"""
    try:
        holistics_response = chat(model_choice, holistics_system,
            f"Build on all previous:\n=== DR. HEART ===\n{dr_heart_response}\n=== NUTRI ===\n{nutri_response}\n=== LONGEVITY ===\n{longevity_response}\n=== END ===\nCase: {case}")
        all_responses.append(("🌿 Holistics", holistics_response))
    except Exception as e:
        all_responses.append(("🌿 Holistics", f"Error: {str(e)}"))
        return all_responses
    
    # === SYNTHESIZER ===
    all_responses.append(("🤝 Synthesizer", "Building consensus..."))
    synthesizer_system = f"""You are the Synthesizer, medical professor. Create consensus.{context}
IMPORTANT: Give clear numbered recommendations."""
    try:
        synthesizer_response = chat(model_choice, synthesizer_system,
            f"Create consensus:\n=== DR. HEART ===\n{dr_heart_response}\n=== NUTRI ===\n{nutri_response}\n=== LONGEVITY ===\n{longevity_response}\n=== HOLISTICS ===\n{holistics_response}\n=== END ===")
        all_responses.append(("🤝 Synthesizer", synthesizer_response))
    except Exception as e:
        all_responses.append(("🤝 Synthesizer", f"Error: {str(e)}"))
        return all_responses
    
    all_responses.append(("✅", "Round Table Complete!"))
    return all_responses

with gr.Blocks(title="Health Round Table") as demo:
    gr.Markdown("# Health Round Table\n*Not medical advice — for educational debate only*")
    
    with gr.Row():
        with gr.Column(scale=3):
            case_input = gr.Textbox(label="Patient Case", placeholder="42yo male, BP 145/95, fatigue...", lines=6)
        with gr.Column(scale=1):
            goals_input = gr.Textbox(label="Goals", placeholder="Lower BP, more energy...", lines=2)
            constraints_input = gr.Textbox(label="Constraints", placeholder="No pharma, vegetarian...", lines=2)
            model_choice = gr.Dropdown(
                choices=[("Mistral Large", "mistral-large-3:675b"), ("Qwen3", "qwen3-vl:235b-instruct"), ("DeepSeek", "deepseek-v3.2")],
                value="mistral-large-3:675b", label="Model")
    
    start_btn = gr.Button("Start Round Table", variant="primary")
    output = gr.Chatbot(label="Discussion", height=500)
    clear_btn = gr.Button("Clear")
    
    start_btn.click(fn=run_round_table, inputs=[case_input, goals_input, constraints_input, model_choice], outputs=output)
    clear_btn.click(fn=lambda: [None, "", "", ""], outputs=[output, case_input, goals_input, constraints_input])
    
    gr.Markdown("Each specialist reads previous analyses before responding — true collaborative debate.")

if __name__ == "__main__":
    print("Starting Health Round Table...")
    demo.launch(server_name="0.0.0.0", server_port=7861, share=True)
