"""
Health Round Table v1 - Using Ollama Cloud
A panel of specialist AI agents discussing anonymized health cases.
"""

import os
import requests
import sys

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

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
    response = requests.post(
        f"{BASE_URL}/api/chat",
        headers=headers,
        json=payload
    )
    if response.status_code != 200:
        raise Exception(f"Error {response.status_code}: {response.text}")
    return response.json()["message"]["content"]

# Agent prompts
dr_heart = """You are Dr. Heart, a board-certified cardiologist with 20 years of experience.
You specialize in blood pressure, cholesterol, circulation, and heart disease prevention.
You are pragmatic and evidence-based, but open to integrative approaches when appropriate."""

nutri = """You are Nutri, a functional medicine nutritionist with expertise in dietary approaches 
to chronic disease. You focus on food as medicine, metabolic health, and evidence-based supplements."""

longevity = """You are Longevity, a longevity researcher specializing in the science of aging.
You stay current on peptides, stem cell research, gene expression, NAD+, rapamycin, and other cutting-edge anti-aging interventions."""

holistics = """You are Holistics, a holistic practitioner trained in integrative medicine.
You combine traditional Chinese medicine, herbalism, acupuncture theory, and self-healing modalities with modern understanding."""

synthesizer = """You are the Synthesizer, a medical professor who specializes in moderating complex multi-specialty discussions.
Your job is to find the signal in the noise, identify where specialists agree and disagree, and provide clear actionable takeaways."""

case = """PATIENT CASE (Anonymized):
Age: 42
Sex: Male
Weight: 180 lbs
Main Concerns: 
  - High blood pressure (readings around 145/95)
  - Chronic fatigue
  - Mild depression
Secondary Concerns:
  - Occasional joint pain
  - Poor sleep quality
Current Lifestyle:
  - Sedentary office job
  - Diet: fast food 3-4x per week, otherwise regular
  - Alcohol: 2-3 drinks per week
  - No regular exercise
Goals:
  - Lower blood pressure naturally if possible
  - More energy during the day
  - Address depression without heavy medication if possible
Labs: Available but not yet reviewed"""

print("=" * 60)
print("HEALTH ROUND TABLE - Starting Discussion")
print("=" * 60)

model = "mistral-large-3:675b"

# Dr. Heart
print("\n[DR. HEART - Cardiologist] analyzing...")
result = chat(model, dr_heart, f"Analyze this case from your cardiology perspective:\n\n{case}\n\nProvide: Your assessment, key concerns, and recommendations.")
print(f"\nDr. Heart:\n{result}\n")

# Nutri
print("[NUTRI - Nutritionist] analyzing...")
result = chat(model, nutri, f"Analyze this case from your nutrition perspective:\n\n{case}\n\nProvide: Dietary changes, supplements, and food-based interventions.")
print(f"\nNutri:\n{result}\n")

# Longevity
print("[LONGEVITY - Anti-Aging Researcher] analyzing...")
result = chat(model, longevity, f"Analyze this case from your longevity/anti-aging perspective:\n\n{case}\n\nProvide: Anti-aging interventions, peptides, or research-backed approaches.")
print(f"\nLongevity:\n{result}\n")

# Holistics
print("[HOLISTICS - Holistic Practitioner] analyzing...")
result = chat(model, holistics, f"Analyze this case from your holistic/alternative medicine perspective:\n\n{case}\n\nProvide: Alternative approaches, herbs, TCM, self-healing modalities.")
print(f"\nHolistics:\n{result}\n")

# Synthesizer
print("=" * 60)
print("[SYNTHESIZER] Preparing final consensus...")
print("=" * 60)

result = chat(model, synthesizer, f"""Review the patient case and analyses from all specialists:
{case}

Provide a synthesized consensus report with:
1. Areas of agreement between specialists
2. Key disagreements
3. Top 3-5 actionable recommendations
4. What the patient should discuss with their doctor""")

print(f"\nFINAL SYNTHESIS:\n{result}")
print("\n" + "=" * 60)
print("HEALTH ROUND TABLE - Discussion Complete!")
print("=" * 60)
