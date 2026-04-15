"""
Health Round Table - Gradio Streaming Version
Agents debate sequentially, each sees previous agents' outputs.
Streaming via Gradio's generator function.
"""

import gradio as gr
import requests
import json

API_KEY = "939d10536ea749c2ac9f1ae783335eaa.L8GP6pNpV7FVESvej9RAoDTT"
BASE_URL = "https://ollama.com"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def chat(model, system, user_message):
    """Make a chat completion request to Ollama Cloud"""
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
    """Generator that yields messages as they arrive - enables streaming in Gradio"""
    
    context = ""
    if goals:
        context += f"\n\nPATIENT GOALS:\n{goals}"
    if constraints:
        context += f"\n\nIMPORTANT CONSTRAINTS:\n{constraints}"
    
    # Track all responses for later agents
    all_responses = {}
    
    # === DR. HEART - First, no previous context ===
    yield {"header": "Dr. Heart", "agent": "dr_heart", "status": "thinking", "message": "Analyzing case from cardiology perspective..."}
    
    dr_heart_system = f"""You are Dr. Heart, a board-certified cardiologist with 20 years of experience.
You specialize in blood pressure, cholesterol, circulation, and heart disease prevention.
You are pragmatic and evidence-based, but open to integrative approaches when appropriate.{context}
IMPORTANT: Give practical, actionable advice. Be specific about dosages and timelines."""
    
    try:
        dr_heart_response = chat(model_choice, dr_heart_system, 
            f"Analyze this case from your cardiology perspective:\n\n{case}\n\nProvide: Your assessment, key concerns, and recommendations.")
        all_responses["dr_heart"] = dr_heart_response
        yield {"header": "Dr. Heart", "agent": "dr_heart", "status": "done", "message": dr_heart_response}
    except Exception as e:
        yield {"header": "Dr. Heart", "agent": "dr_heart", "status": "error", "message": f"Error: {str(e)}"}
        return
    
    # === NUTRI - Second, sees Dr. Heart ===
    yield {"header": "Nutri", "agent": "nutri", "status": "thinking", "message": "Reviewing Dr. Heart's analysis..."}
    
    nutri_system = f"""You are Nutri, a functional medicine nutritionist with expertise in dietary approaches 
to chronic disease. You focus on food as medicine, metabolic health, and evidence-based supplements.{context}
IMPORTANT: Read Dr. Heart's analysis and react to it. Build on his foundation with nutritional insights.
Be specific about foods, supplements, and meal ideas."""
    
    try:
        nutri_response = chat(model_choice, nutri_system,
            f"Analyze this case from your nutrition perspective.\n\nIMPORTANT: First read Dr. Heart's analysis and react to it:\n=== DR. HEART'S ANALYSIS ===\n{dr_heart_response}\n=== END DR. HEART ===\n\nNow provide your nutritional analysis.")
        all_responses["nutri"] = nutri_response
        yield {"header": "Nutri", "agent": "nutri", "status": "done", "message": nutri_response}
    except Exception as e:
        yield {"header": "Nutri", "agent": "nutri", "status": "error", "message": f"Error: {str(e)}"}
        return
    
    # === LONGEVITY - Third, sees Dr. Heart and Nutri ===
    yield {"header": "Longevity", "agent": "longevity", "status": "thinking", "message": "Building on previous analyses..."}
    
    longevity_system = f"""You are Longevity, a longevity researcher specializing in the science of aging.
You stay current on peptides, stem cell research, gene expression, NAD+, rapamycin, and other cutting-edge anti-aging interventions.{context}
IMPORTANT: Read ALL previous specialists' analyses and find connections or tensions between their perspectives.
Be specific about what to try first."""
    
    try:
        longevity_response = chat(model_choice, longevity_system,
            f"Analyze this case from your anti-aging/longevity perspective.\n\nIMPORTANT: First read what the other specialists said:\n=== DR. HEART'S ANALYSIS ===\n{dr_heart_response}\n=== END DR. HEART ===\n\n=== NUTRI'S ANALYSIS ===\n{nutri_response}\n=== END NUTRI ===\n\nNow provide your longevity-focused analysis.")
        all_responses["longevity"] = longevity_response
        yield {"header": "Longevity", "agent": "longevity", "status": "done", "message": longevity_response}
    except Exception as e:
        yield {"header": "Longevity", "agent": "longevity", "status": "error", "message": f"Error: {str(e)}"}
        return
    
    # === HOLISTICS - Fourth, sees all three ===
    yield {"header": "Holistics", "agent": "holistics", "status": "thinking", "message": "Adding integrative perspective..."}
    
    holistics_system = f"""You are Holistics, a holistic practitioner trained in integrative medicine.
You combine traditional Chinese medicine, herbalism, acupuncture theory, and self-healing modalities with modern understanding.{context}
IMPORTANT: Read ALL previous specialists' analyses. Find where Western medicine and nutrition align or conflict with holistic perspectives.
Be specific about herbs, acupoints, and practices."""
    
    try:
        holistics_response = chat(model_choice, holistics_system,
            f"Analyze this case from your holistic/integrative medicine perspective.\n\nIMPORTANT: Read what all specialists said:\n=== DR. HEART'S ANALYSIS ===\n{dr_heart_response}\n=== END DR. HEART ===\n\n=== NUTRI'S ANALYSIS ===\n{nutri_response}\n=== END NUTRI ===\n\n=== LONGEVITY'S ANALYSIS ===\n{longevity_response}\n=== END LONGEVITY ===\n\nNow provide your holistic analysis.")
        all_responses["holistics"] = holistics_response
        yield {"header": "Holistics", "agent": "holistics", "status": "done", "message": holistics_response}
    except Exception as e:
        yield {"header": "Holistics", "agent": "holistics", "status": "error", "message": f"Error: {str(e)}"}
        return
    
    # === SYNTHESIZER - Fifth, sees all four ===
    yield {"header": "Synthesizer", "agent": "synthesizer", "status": "thinking", "message": "Building consensus from all specialists..."}
    
    synthesizer_system = f"""You are the Synthesizer, a medical professor who specializes in moderating complex multi-specialty discussions.
Your job is to find the signal in the noise, identify where specialists agree and disagree, and provide clear actionable takeaways.{context}
IMPORTANT: Create a clear consensus with numbered recommendations. This is the most important output."""
    
    try:
        synthesizer_response = chat(model_choice, synthesizer_system,
            f"Provide the final synthesized consensus.\n\n=== FULL ANALYSES FROM ALL SPECIALISTS ===\n\nDR. HEART:\n{dr_heart_response}\n\nNUTRI:\n{nutri_response}\n\nLONGEVITY:\n{longevity_response}\n\nHOLISTICS:\n{holistics_response}\n\n=== END ANALYSES ===\n\nProvide a synthesized consensus report with:\n1. Areas of AGREEMENT between specialists\n2. Key DISAGREEMENTS or tensions (and how they were resolved)\n3. Top 3-5 actionable recommendations (in priority order)\n4. What the patient should discuss with their doctor\n5. How recommendations respect the patient's constraints\n\nBe specific and actionable.")
        all_responses["synthesizer"] = synthesizer_response
        yield {"header": "Synthesizer", "agent": "synthesizer", "status": "done", "message": synthesizer_response}
    except Exception as e:
        yield {"header": "Synthesizer", "agent": "synthesizer", "status": "error", "message": f"Error: {str(e)}"}
        return
    
    yield {"header": "System", "agent": "system", "status": "complete", "message": "Round Table Complete! All specialists have finished their analysis."}

# Agent colors for UI
AGENT_COLORS = {
    "dr_heart": ("❤️", "#ff6b6b", "Cardiologist"),
    "nutri": ("🍔", "#feca57", "Nutritionist"),
    "longevity": ("⌛", "#54a0ff", "Longevity Researcher"),
    "holistics": ("🌿", "#a55eea", "Integrative Medicine"),
    "synthesizer": ("🤝", "#00d9ff", "Medical Professor"),
    "system": ("✓", "#00ff88", "System")
}

def create_message(msg_dict):
    """Convert streaming dict to chatbot tuple (message, None)"""
    agent = msg_dict.get("agent", "system")
    status = msg_dict.get("status", "")
    message = msg_dict.get("message", "")
    header = msg_dict.get("header", agent)
    
    emoji, color, role = AGENT_COLORS.get(agent, ("•", "#888", "Specialist"))
    
    if status == "thinking":
        return f"**{emoji} {header}** ({role})\n\n⏳ {message}..."
    elif status == "error":
        return f"**{emoji} {header}** ({role})\n\n❌ {message}"
    elif status == "complete":
        return f"**✅ {message}**"
    else:
        return f"**{emoji} {header}** ({role})\n\n{message}"

def stream_to_chatbot(msg_dict):
    """Convert streaming dict to chatbot format"""
    return (create_message(msg_dict), None)

# Build Gradio interface
with gr.Blocks(title="Health Round Table").queue() as demo:
    
    gr.Markdown(""""# Health Round Table
    ## Watch AI Specialists Collaborate on Your Health Case
    *Not medical advice — for educational debate only*
    """)
    
    with gr.Row():
        with gr.Column(scale=3):
            case_input = gr.Textbox(
                label="📋 Patient Case",
                placeholder="Enter patient case here...\n\nExample: 42 year old male, BP 145/95, chronic fatigue, fast food diet...",
                lines=8
            )
        with gr.Column(scale=1):
            goals_input = gr.Textbox(
                label="🎯 Goals",
                placeholder="Lower BP naturally, more energy...",
                lines=2
            )
            constraints_input = gr.Textbox(
                label="⚠️ Constraints",
                placeholder="No pharmaceuticals, vegetarian...",
                lines=2
            )
            model_choice = gr.Dropdown(
                choices=[
                    ("Mistral Large", "mistral-large-3:675b"),
                    ("Qwen 3 Vision", "qwen3-vl:235b-instruct"),
                    ("DeepSeek V3", "deepseek-v3.2"),
                    ("Gemma 3", "gemma3:27b"),
                ],
                value="mistral-large-3:675b",
                label="🤖 Model"
            )
    
    start_btn = gr.Button("🚀 Start Health Round Table", variant="primary")
    
    output_chatbot = gr.Chatbot(
        label="Round Table Discussion",
        height=600
    )
    
    clear_btn = gr.Button("🔄 Clear")
    
    gr.Markdown("""---
    **How it works:** Each specialist reads the previous specialists' analyses before giving their own perspective, creating a true collaborative debate.
    """)
    
    # Event handlers
    start_btn.click(
        fn=run_round_table,
        inputs=[case_input, goals_input, constraints_input, model_choice],
        outputs=output_chatbot
    )
    
    clear_btn.click(
        fn=lambda: (None, None, "", ""),
        outputs=[output_chatbot, case_input, goals_input, constraints_input]
    )

if __name__ == "__main__":
    print("Starting Health Round Table - Gradio Interface...")
    print("Open http://127.0.0.1:7860 in your browser")
    demo.launch(server_name="0.0.0.0", server_port=7860, prevent_thread_lock=True)
