"""
Health Round Table Web - Streaming Debate Version
Agents complete sequentially but content streams in real-time.
Each agent sees previous agents' outputs.
"""

from flask import Flask, render_template, request, jsonify, Response
import requests
import json
import sys

app = Flask(__name__)

API_KEY = "939d10536ea749c2ac9f1ae783335eaa.L8GP6pNpV7FVESvej9RAoDTT"
BASE_URL = "https://ollama.com"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def chat(model, system, user_message):
    """Non-streaming chat - returns complete response"""
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

def generate_events(case, goals, constraints, model):
    """Generator that yields SSE events as agents complete"""
    
    context = ""
    if goals:
        context += f"\n\nPATIENT GOALS:\n{goals}"
    if constraints:
        context += f"\n\nIMPORTANT CONSTRAINTS:\n{constraints}"
    
    all_responses = {}
    specialist_order = ["dr_heart", "nutri", "longevity", "holistics", "synthesizer"]
    
    specialist_prompts = {
        "dr_heart": {
            "name": "Dr. Heart",
            "system": f"""You are Dr. Heart, a board-certified cardiologist with 20 years of experience.
You specialize in blood pressure, cholesterol, circulation, and heart disease prevention.
You are pragmatic and evidence-based, but open to integrative approaches when appropriate.{context}
IMPORTANT: Give practical, actionable advice. Be specific about dosages and timelines.""",
            "user_template": "Analyze this case from your cardiology perspective:\n\n{case}\n\nProvide: Your assessment, key concerns, and recommendations."
        },
        "nutri": {
            "name": "Nutri",
            "system": f"""You are Nutri, a functional medicine nutritionist with expertise in dietary approaches 
to chronic disease. You focus on food as medicine, metabolic health, and evidence-based supplements.{context}
IMPORTANT: Read Dr. Heart's analysis and react to it. Build on his foundation with nutritional insights.
Be specific about foods, supplements, and meal ideas.""",
            "user_template": """Analyze this case from your nutrition perspective.
IMPORTANT: First read Dr. Heart's analysis and react to it:
=== DR. HEART'S ANALYSIS ===
{prev_response}
=== END DR. HEART ===

Now provide your nutritional analysis, specifically addressing points raised by Dr. Heart."""
        },
        "longevity": {
            "name": "Longevity",
            "system": f"""You are Longevity, a longevity researcher specializing in the science of aging.
You stay current on peptides, stem cell research, gene expression, NAD+, rapamycin, and other cutting-edge anti-aging interventions.{context}
IMPORTANT: Read ALL previous specialists' analyses and find connections or tensions between their perspectives.
Be specific about what to try first.""",
            "user_template": """Analyze this case from your anti-aging/longevity perspective.
IMPORTANT: First read what the other specialists said, then provide your analysis:
=== DR. HEART'S ANALYSIS ===
{dr_heart_response}
=== END DR. HEART ===

=== NUTRI'S ANALYSIS ===
{nutri_response}
=== END NUTRI ===

Now provide your longevity-focused analysis, building on and reacting to both previous specialists."""
        },
        "holistics": {
            "name": "Holistics",
            "system": f"""You are Holistics, a holistic practitioner trained in integrative medicine.
You combine traditional Chinese medicine, herbalism, acupuncture theory, and self-healing modalities with modern understanding.{context}
IMPORTANT: Read ALL previous specialists' analyses. Find where Western medicine and nutrition align or conflict with holistic perspectives.
Be specific about herbs, acupoints, and practices.""",
            "user_template": """Analyze this case from your holistic/integrative medicine perspective.
IMPORTANT: First read what all specialists said, then provide your analysis:
=== DR. HEART'S ANALYSIS ===
{dr_heart_response}
=== END DR. HEART ===

=== NUTRI'S ANALYSIS ===
{nutri_response}
=== END NUTRI ===

=== LONGEVITY'S ANALYSIS ===
{longevity_response}
=== END LONGEVITY ===

Now provide your holistic analysis, building on and reacting to ALL previous specialists."""
        },
        "synthesizer": {
            "name": "Synthesizer",
            "system": f"""You are the Synthesizer, a medical professor who specializes in moderating complex multi-specialty discussions.
Your job is to find the signal in the noise, identify where specialists agree and disagree, and provide clear actionable takeaways.{context}
IMPORTANT: Create a clear consensus with numbered recommendations. This is the most important output.""",
            "user_template": """Provide the final synthesized consensus.
=== FULL ANALYSES FROM ALL SPECIALISTS ===

DR. HEART:
{dr_heart_response}

NUTRI:
{nutri_response}

LONGEVITY:
{longevity_response}

HOLISTICS:
{holistics_response}

=== END ANALYSES ===

Provide a synthesized consensus report with:
1. Areas of AGREEMENT between specialists
2. Key DISAGREEMENTS or tensions (and how they were resolved)
3. Top 3-5 actionable recommendations (in priority order)
4. What the patient should discuss with their doctor
5. How recommendations respect the patient's constraints

Be specific and actionable."""
        }
    }
    
    # Dr. Heart - First, no previous context
    yield f"event: agent_start\ndata: dr_heart\n\n"
    yield f"event: status\ndata: Dr. Heart is analyzing the case...\n\n"
    
    spec = specialist_prompts["dr_heart"]
    user_prompt = spec["user_template"].format(case=case)
    response = chat(model, spec["system"], user_prompt)
    all_responses["dr_heart"] = response
    yield f"event: agent_chunk\ndata: dr_heart:{response}\n\n"
    yield f"event: agent_done\ndata: dr_heart\n\n"
    
    # Nutri - sees Dr. Heart
    yield f"event: agent_start\ndata: nutri\n\n"
    yield f"event: status\ndata: Nutri is reviewing Dr. Heart's analysis...\n\n"
    
    spec = specialist_prompts["nutri"]
    user_prompt = spec["user_template"].format(prev_response=response)
    response = chat(model, spec["system"], user_prompt)
    all_responses["nutri"] = response
    yield f"event: agent_chunk\ndata: nutri:{response}\n\n"
    yield f"event: agent_done\ndata: nutri\n\n"
    
    # Longevity - sees Dr. Heart and Nutri
    yield f"event: agent_start\ndata: longevity\n\n"
    yield f"event: status\ndata: Longevity is building on previous analyses...\n\n"
    
    spec = specialist_prompts["longevity"]
    user_prompt = spec["user_template"].format(
        dr_heart_response=all_responses["dr_heart"],
        nutri_response=all_responses["nutri"]
    )
    response = chat(model, spec["system"], user_prompt)
    all_responses["longevity"] = response
    yield f"event: agent_chunk\ndata: longevity:{response}\n\n"
    yield f"event: agent_done\ndata: longevity\n\n"
    
    # Holistics - sees all three
    yield f"event: agent_start\ndata: holistics\n\n"
    yield f"event: status\ndata: Holistics is adding integrative perspective...\n\n"
    
    spec = specialist_prompts["holistics"]
    user_prompt = spec["user_template"].format(
        dr_heart_response=all_responses["dr_heart"],
        nutri_response=all_responses["nutri"],
        longevity_response=all_responses["longevity"]
    )
    response = chat(model, spec["system"], user_prompt)
    all_responses["holistics"] = response
    yield f"event: agent_chunk\ndata: holistics:{response}\n\n"
    yield f"event: agent_done\ndata: holistics\n\n"
    
    # Synthesizer - sees all four
    yield f"event: agent_start\ndata: synthesizer\n\n"
    yield f"event: status\ndata: Synthesizer is building consensus...\n\n"
    
    spec = specialist_prompts["synthesizer"]
    user_prompt = spec["user_template"].format(
        dr_heart_response=all_responses["dr_heart"],
        nutri_response=all_responses["nutri"],
        longevity_response=all_responses["longevity"],
        holistics_response=all_responses["holistics"]
    )
    response = chat(model, spec["system"], user_prompt)
    all_responses["synthesizer"] = response
    yield f"event: agent_chunk\ndata: synthesizer:{response}\n\n"
    yield f"event: agent_done\ndata: synthesizer\n\n"
    
    yield f"event: complete\ndata: Round Table Complete!\n\n"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/run_streaming", methods=["POST"])
def run_streaming():
    data = request.json
    case = data.get("case", "")
    goals = data.get("goals", "")
    constraints = data.get("constraints", "")
    model = data.get("model", "mistral-large-3:675b")
    
    return Response(
        generate_events(case, goals, constraints, model),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )

if __name__ == "__main__":
    print("Starting Health Round Table Web - Streaming Version...")
    print("Open http://127.0.0.1:5001 in your browser")
    app.run(host="0.0.0.0", port=5001, debug=False, threaded=True)
