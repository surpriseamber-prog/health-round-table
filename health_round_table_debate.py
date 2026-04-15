"""
Health Round Table - Agent-to-Agent Debate Version
Each agent sees previous agents' responses and can react to them.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import requests
import json

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

def run_round_table(case, goals="", constraints="", model="mistral-large-3:675b"):
    """Run the health round table with agent-to-agent interaction."""
    
    # Build constraint/goals context
    context = ""
    if goals:
        context += f"\n\nPATIENT GOALS:\n{goals}"
    if constraints:
        context += f"\n\nIMPORTANT CONSTRAINTS:\n{constraints}"
    
    # Track all responses for later agents
    all_responses = {}
    
    # === DR. HEART - First, no previous context ===
    print("\n" + "="*60)
    print("DR. HEART - Analyzing case first...")
    print("="*60)
    
    dr_heart_system = f"""You are Dr. Heart, a board-certified cardiologist with 20 years of experience.
You specialize in blood pressure, cholesterol, circulation, and heart disease prevention.
You are pragmatic and evidence-based, but open to integrative approaches when appropriate.{context}
IMPORTANT: Give practical, actionable advice. Be specific about dosages and timelines."""
    
    dr_heart_response = chat(model, dr_heart_system, 
        f"Analyze this case from your cardiology perspective:\n\n{case}\n\nProvide: Your assessment, key concerns, and recommendations.")
    all_responses["dr_heart"] = dr_heart_response
    print(f"\nDr. Heart's Response:\n{dr_heart_response[:500]}...")
    
    # === NUTRI - Second, sees Dr. Heart ===
    print("\n" + "="*60)
    print("NUTRI - Reviewing Dr. Heart's analysis...")
    print("="*60)
    
    nutri_system = f"""You are Nutri, a functional medicine nutritionist with expertise in dietary approaches 
to chronic disease. You focus on food as medicine, metabolic health, and evidence-based supplements.{context}
IMPORTANT: 
- Read Dr. Heart's analysis below carefully
- React to specific points Dr. Heart made
- Agree, expand on, or respectfully challenge his cardiology perspective
- Build on his foundation with nutritional insights
Be specific about foods, supplements, and meal ideas."""
    
    nutri_response = chat(model, nutri_system,
        f"Analyze this case from your nutrition perspective.\n\nIMPORTANT: First, read Dr. Heart's analysis and react to it:\n\n=== DR. HEART'S ANALYSIS ===\n{dr_heart_response}\n=== END DR. HEART ===\n\nNow provide your nutritional analysis, specifically addressing points raised by Dr. Heart.")
    all_responses["nutri"] = nutri_response
    print(f"\nNutri's Response:\n{nutri_response[:500]}...")
    
    # === LONGEVITY - Third, sees Dr. Heart and Nutri ===
    print("\n" + "="*60)
    print("LONGEVITY - Reviewing previous specialists...")
    print("="*60)
    
    longevity_system = f"""You are Longevity, a longevity researcher specializing in the science of aging.
You stay current on peptides, stem cell research, gene expression, NAD+, rapamycin, and other cutting-edge anti-aging interventions.{context}
IMPORTANT:
- Read ALL previous specialists' analyses below
- React to specific points made by Dr. Heart AND Nutri
- Find connections or tensions between their perspectives
- Add longevity/scientific depth to the discussion
Be specific about what to try first."""
    
    longevity_response = chat(model, longevity_system,
        f"Analyze this case from your anti-aging/longevity perspective.\n\nIMPORTANT: First read what the other specialists said, then provide your analysis:\n\n=== DR. HEART'S ANALYSIS ===\n{dr_heart_response}\n=== END DR. HEART ===\n\n=== NUTRI'S ANALYSIS ===\n{nutri_response}\n=== END NUTRI ===\n\nNow provide your longevity-focused analysis, building on and reacting to both previous specialists.")
    all_responses["longevity"] = longevity_response
    print(f"\nLongevity's Response:\n{longevity_response[:500]}...")
    
    # === HOLISTICS - Fourth, sees all three ===
    print("\n" + "="*60)
    print("HOLISTICS - Adding integrative perspective...")
    print("="*60)
    
    holistics_system = f"""You are Holistics, a holistic practitioner trained in integrative medicine.
You combine traditional Chinese medicine, herbalism, acupuncture theory, and self-healing modalities with modern understanding.{context}
IMPORTANT:
- Read ALL previous specialists' analyses below
- Find where Western medicine (Dr. Heart) and nutrition (Nutri) align or conflict with holistic perspectives
- Add integrative/traditional medicine insights
- Address any gaps or oversights from the previous specialists
Be specific about herbs, acupoints, and practices."""
    
    holistics_response = chat(model, holistics_system,
        f"Analyze this case from your holistic/integrative medicine perspective.\n\nIMPORTANT: First read what all specialists said, then provide your analysis:\n\n=== DR. HEART'S ANALYSIS ===\n{dr_heart_response}\n=== END DR. HEART ===\n\n=== NUTRI'S ANALYSIS ===\n{nutri_response}\n=== END NUTRI ===\n\n=== LONGEVITY'S ANALYSIS ===\n{longevity_response}\n=== END LONGEVITY ===\n\nNow provide your holistic analysis, building on and reacting to ALL previous specialists.")
    all_responses["holistics"] = holistics_response
    print(f"\nHolistics's Response:\n{holistics_response[:500]}...")
    
    # === SYNTHESIZER - Fifth, sees all four ===
    print("\n" + "="*60)
    print("SYNTHESIZER - Building consensus...")
    print("="*60)
    
    synthesizer_system = f"""You are the Synthesizer, a medical professor who specializes in moderating complex multi-specialty discussions.
Your job is to find the signal in the noise, identify where specialists agree and disagree, and provide clear actionable takeaways.{context}
IMPORTANT:
- You have access to ALL specialists' full analyses
- Find specific areas of AGREEMENT between specialists
- Find specific DISAGREEMENTS or tensions
- Identify what the patient should prioritize
- Create a clear consensus with numbered recommendations
This is the most important output - make it actionable."""
    
    synthesizer_response = chat(model, synthesizer_system,
        f"Provide the final synthesized consensus.\n\n=== FULL ANALYSES FROM ALL SPECIALISTS ===\n\nDR. HEART:\n{dr_heart_response}\n\nNUTRI:\n{nutri_response}\n\nLONGEVITY:\n{longevity_response}\n\nHOLISTICS:\n{holistics_response}\n\n=== END ANALYSES ===\n\nProvide a synthesized consensus report with:\n1. Areas of AGREEMENT between specialists\n2. Key DISAGREEMENTS or tensions (and how they were resolved)\n3. Top 3-5 actionable recommendations (in priority order)\n4. What the patient should discuss with their doctor\n5. How recommendations respect the patient's constraints\n\nBe specific and actionable.")
    all_responses["synthesizer"] = synthesizer_response
    print(f"\nSynthesizer's Response:\n{synthesizer_response[:500]}...")
    
    print("\n" + "="*60)
    print("ROUND TABLE COMPLETE!")
    print("="*60)
    
    return all_responses

if __name__ == "__main__":
    case = """PATIENT CASE:
Age: 42
Sex: Male
Weight: 180 lbs
BP: 145/95
Main Concerns: Chronic fatigue, mild depression, poor sleep
Lifestyle: Sedentary office job, fast food 3-4x/week
Goals: Lower BP naturally, more energy"""
    
    constraints = "NO PHARMACEUTICAL MEDICATIONS - prefer natural approaches"
    
    results = run_round_table(case, goals="Lower BP naturally, more energy", constraints=constraints)
    
    print("\n\n=== FINAL RESULTS ===")
    for specialist, response in results.items():
        print(f"\n--- {specialist.upper()} ---\n{response}")
