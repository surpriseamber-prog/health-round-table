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
    result = []
    result.append({"role": "assistant", "content": "Starting Health Round Table... Dr. Heart is analyzing the case."})
    dr_heart_system = f"""You are Dr. Heart, a board-certified cardiologist. Focus on BP, cholesterol, circulation.{context}
IMPORTANT: Give practical, actionable advice."""
    try:
        dr_heart_response = chat(model_choice, dr_heart_system, f"Analyze: {case}")
        result.append({"role": "assistant", "content": f"**Dr. Heart:**\n{dr_heart_response}"})
    except Exception as e:
        result.append({"role": "assistant", "content": f"Dr. Heart error: {str(e)}"})
        return result
    result.append({"role": "assistant", "content": "Nutri is reviewing Dr. Heart's analysis..."})
    nutri_system = f"""You are Nutri, a functional medicine nutritionist. Build on Dr. Heart's foundation.{context}"""
    try:
        nutri_response = chat(model_choice, nutri_system, f"React to Dr. Heart and add nutrition perspective:\n=== DR. HEART ===\n{dr_heart_response}\n=== END ===\nCase: {case}")
        result.append({"role": "assistant", "content": f"**Nutri:**\n{nutri_response}"})
    except Exception as e:
        result.append({"role": "assistant", "content": f"Nutri error: {str(e)}"})
        return result
    result.append({"role": "assistant", "content": "Longevity is building on previous analyses..."})
    longevity_system = f"""You are Longevity, a longevity researcher. Add anti-aging perspective.{context}"""
    try:
        longevity_response = chat(model_choice, longevity_system, f"Build on Dr. Heart and Nutri:\n=== DR. HEART ===\n{dr_heart_response}\n=== NUTRI ===\n{nutri_response}\n=== END ===\nCase: {case}")
        result.append({"role": "assistant", "content": f"**Longevity:**\n{longevity_response}"})
    except Exception as e:
        result.append({"role": "assistant", "content": f"Longevity error: {str(e)}"})
        return result
    result.append({"role": "assistant", "content": "Holistics is adding integrative perspective..."})
    holistics_system = f"""You are Holistics, integrative medicine practitioner.{context}"""
    try:
        holistics_response = chat(model_choice, holistics_system, f"Build on all previous:\n=== DR. HEART ===\n{dr_heart_response}\n=== NUTRI ===\n{nutri_response}\n=== LONGEVITY ===\n{longevity_response}\n=== END ===\nCase: {case}")
        result.append({"role": "assistant", "content": f"**Holistics:**\n{holistics_response}"})
    except Exception as e:
        result.append({"role": "assistant", "content": f"Holistics error: {str(e)}"})
        return result
    result.append({"role": "assistant", "content": "Synthesizer is building consensus..."})
    synthesizer_system = f"""You are the Synthesizer, medical professor. Create consensus.{context}
IMPORTANT: Give clear numbered recommendations."""
    try:
        synthesizer_response = chat(model_choice, synthesizer_system, f"Create consensus:\n=== DR. HEART ===\n{dr_heart_response}\n=== NUTRI ===\n{nutri_response}\n=== LONGEVITY ===\n{longevity_response}\n=== HOLISTICS ===\n{holistics_response}\n=== END ===")
        result.append({"role": "assistant", "content": f"**Synthesizer:**\n{synthesizer_response}"})
    except Exception as e:
        result.append({"role": "assistant", "content": f"Synthesizer error: {str(e)}"})
        return result
    result.append({"role": "assistant", "content": "✅ Round Table Complete!"})
    return result

with gr.Blocks(title="Health Round Table") as demo:
    gr.Markdown("# Health Round Table\n*Not medical advice - for educational debate only*")
    with gr.Row():
        with gr.Column(scale=3):
            case_input = gr.Textbox(label="Patient Case", placeholder="42yo male, BP 145/95, fatigue...", lines=6)
        with gr.Column(scale=1):
            goals_input = gr.Textbox(label="Goals", placeholder="Lower BP, more energy...", lines=2)
            constraints_input = gr.Textbox(label="Constraints", placeholder="No pharma, vegetarian...", lines=2)
            model_choice = gr.Dropdown(choices=[("Mistral Large", "mistral-large-3:675b"), ("Qwen3", "qwen3-vl:235b-instruct"), ("DeepSeek", "deepseek-v3.2")], value="mistral-large-3:675b", label="Model")
    start_btn = gr.Button("Start Round Table", variant="primary")
    output = gr.Chatbot(label="Discussion", height=500)
    clear_btn = gr.Button("Clear")
    start_btn.click(fn=run_round_table, inputs=[case_input, goals_input, constraints_input, model_choice], outputs=output)
    clear_btn.click(fn=lambda: [None, None], outputs=[output, case_input])
    gr.Markdown("Each specialist reads previous analyses before responding - true collaborative debate.")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7861)
