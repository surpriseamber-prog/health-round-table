"""
Health Round Table v1 — CrewAI + Gemini Implementation
A panel of specialist AI agents discussing anonymized health cases.
"""

import os
from crewai import Agent, Task, Crew
from crewai_llm import LiteLLM

# ─────────────────────────────────────────────────────────
# SET YOUR GEMINI API KEY HERE
# ─────────────────────────────────────────────────────────
os.environ["GEMINI_API_KEY"] = "AIzaSyAepBijiiitlEHBBpfduFtYn0RL9DKaGco"

# ─────────────────────────────────────────────────────────
# CONFIGURE LLM — Using Gemini via LiteLLM
# ─────────────────────────────────────────────────────────
llm = LiteLLM(model="gemini/gemini-1.5-flash")

# ─────────────────────────────────────────────────────────
# THE AGENTS — Each specialist at the round table
# ─────────────────────────────────────────────────────────

dr_heart = Agent(
    role="Cardiologist",
    goal="Provide expert cardiovascular health insights based on the case",
    backstory="""
    You are a board-certified cardiologist with 20 years of experience.
    You specialize in blood pressure, cholesterol, circulation, and heart disease prevention.
    You are pragmatic and evidence-based, but open to integrative approaches when appropriate.
    """,
    llm=llm,
    verbose=True,
    allow_delegation=False
)

nutri = Agent(
    role="Nutritionist",
    goal="Provide expert nutrition and supplement guidance based on the case",
    backstory="""
    You are a functional medicine nutritionist with expertise in dietary approaches 
    to chronic disease. You focus on food as medicine, metabolic health, and 
    evidence-based supplements.
    """,
    llm=llm,
    verbose=True,
    allow_delegation=False
)

longevity = Agent(
    role="Longevity Researcher",
    goal="Provide anti-aging and longevity science insights based on the case",
    backstory="""
    You are a longevity researcher specializing in the science of aging.
    You stay current on peptides, stem cell research, gene expression, NAD+,
    rapamycin, and other cutting-edge anti-aging interventions.
    """,
    llm=llm,
    verbose=True,
    allow_delegation=False
)

holistics = Agent(
    role="Holistic Practitioner",
    goal="Provide alternative and traditional medicine perspectives based on the case",
    backstory="""
    You are a holistic practitioner trained in integrative medicine.
    You combine traditional Chinese medicine, herbalism, acupuncture theory,
    and self-healing modalities with modern understanding.
    """,
    llm=llm,
    verbose=True,
    allow_delegation=False
)

synthesizer = Agent(
    role="Medical Synthesizer",
    goal="Summarize the discussion and find consensus or clear next steps",
    backstory="""
    You are a medical professor who specializes in moderating complex 
    multi-specialty discussions. Your job is to find the signal in the noise,
    identify where specialists agree and disagree, and provide clear 
    actionable takeaways.
    """,
    llm=llm,
    verbose=True,
    allow_delegation=True
)

# ─────────────────────────────────────────────────────────
# THE CASE — Anonymized patient information
# ─────────────────────────────────────────────────────────

case = """
PATIENT CASE (Anonymized):

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
Labs: Available but not yet reviewed
"""

# ─────────────────────────────────────────────────────────
# THE TASKS — Each agent analyzes the case
# ─────────────────────────────────────────────────────────

task_heart = Task(
    description=f"Analyze this case from a cardiologist perspective:\n\n{case}",
    agent=dr_heart,
    expected_output="Your cardiology assessment: what you see, what concerns you, and your recommendations."
)

task_nutri = Task(
    description=f"Analyze this case from a nutrition perspective:\n\n{case}",
    agent=nutri,
    expected_output="Your nutrition assessment: dietary changes, supplements, and food-based interventions."
)

task_longevity = Task(
    description=f"Analyze this case from a longevity/anti-aging perspective:\n\n{case}",
    agent=longevity,
    expected_output="Your longevity assessment: anti-aging interventions, peptides, or research-backed approaches."
)

task_holistics = Task(
    description=f"Analyze this case from a holistic/alternative medicine perspective:\n\n{case}",
    agent=holistics,
    expected_output="Your holistic assessment: alternative approaches, herbs, TCM, self-healing modalities."
)

task_synthesize = Task(
    description=f"""Review all the specialist perspectives below and synthesize them into a clear report.

    The specialists have analyzed this case:
    {case}
    
    Provide:
    1. Areas of agreement between specialists
    2. Key disagreements
    3. Top 3-5 actionable recommendations
    4. What the patient should discuss with their doctor
    """,
    agent=synthesizer,
    expected_output="A clear synthesis: consensus points, disagreements, and actionable next steps."
)

# ─────────────────────────────────────────────────────────
# THE CREW — The round table working together
# ─────────────────────────────────────────────────────────

crew = Crew(
    agents=[dr_heart, nutri, longevity, holistics, synthesizer],
    tasks=[task_heart, task_nutri, task_longevity, task_holistics, task_synthesize],
    verbose=True
)

# ─────────────────────────────────────────────────────────
# RUN IT
# ─────────────────────────────────────────────────────────

print("🏥 Health Round Table — Starting Discussion...\n")
print("=" * 60)

result = crew.kickoff()

print("\n" + "=" * 60)
print("🏁 FINAL SYNTHESIS:")
print("=" * 60)
print(result)
