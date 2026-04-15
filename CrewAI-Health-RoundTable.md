# Health Round Table — CrewAI Implementation Sketch

**Date:** 2026-04-07  
**Framework:** CrewAI  
**Status:** Planning

---

## What is CrewAI?

CrewAI is a framework for building "crews" of AI agents that work together on tasks. Each agent has a role, a goal, and tools. Tasks are assigned to agents who work together to complete them.

**Think of it like this:**
- **Agent** = a person at the round table (Dr. Heart, Nutri, etc.)
- **Task** = the case to discuss
- **Crew** = the whole round table working together

---

## The Crew Structure

### Agents (the round table participants)

```
┌─────────────────────────────────────────────────────┐
│                   THE ROUND TABLE                   │
│                                                     │
│   ┌─────────────┐                                   │
│   │ Dr. Heart   │ → Cardiology perspective          │
│   └─────────────┘                                   │
│   ┌─────────────┐                                   │
│   │ Nutri       │ → Nutrition & supplements          │
│   └─────────────┘                                   │
│   ┌─────────────┐                                   │
│   │ Longevity   │ → Anti-aging, peptides, stem cells │
│   └─────────────┘                                   │
│   ┌─────────────┐                                   │
│   │ Holistics   │ → Alternative, TCM, self-healing  │
│   └─────────────┘                                   │
│   ┌─────────────┐                                   │
│   │ Synthesizer │ → Moderator, pulls it all together│
│   └─────────────┘                                   │
└─────────────────────────────────────────────────────┘
```

### How a case flows through the crew

```
User submits case:
{
  age: 42,
  sex: "male",
  weight: "180 lbs",
  concern: "high blood pressure, fatigue, depression",
  goal: "lower BP, more energy, natural approach preferred"
}
          │
          ▼
┌─────────────────────────────────────┐
│  Dr. Heart analyzes the case        │
│  "BP issues often relate to..."      │
└─────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────┐
│  Nutri analyzes                     │
│  "Dietary changes could help..."     │
└─────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────┐
│  Longevity specialist               │
│  "Peptides and anti-aging could..." │
└─────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────┐
│  Holistics practitioner             │
│  "Alternative approaches..."        │
└─────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────┐
│  Synthesizer pulls it all together  │
│  "Here's the consensus..."          │
└─────────────────────────────────────┘
          │
          ▼
    Final Report
    User sees the full discussion
```

---

## The Code Structure

### File: `health_round_table.py`

```python
from crewai import Agent, Task, Crew

# ─────────────────────────────────────────────────────────
# THE AGENTS
# ─────────────────────────────────────────────────────────

dr_heart = Agent(
    role="Cardiologist",
    goal="Provide heart health and cardiovascular insights",
    backstory="You are a board-certified cardiologist with 20 years "
              "of experience. You focus on blood pressure, cholesterol, "
              "circulation, and heart disease prevention.",
    verbose=True
)

nutri = Agent(
    role="Nutritionist",
    goal="Provide nutrition and supplement guidance",
    backstory="You are a functional medicine nutritionist who "
              "specializes in dietary approaches to health.",
    verbose=True
)

longevity = Agent(
    role="Longevity Researcher",
    goal="Provide anti-aging and longevity science insights",
    backstory="You are a longevity researcher focused on peptides, "
              "stem cells, gene expression, and cutting-edge anti-aging.",
    verbose=True
)

holistics = Agent(
    role="Holistic Practitioner",
    goal="Provide alternative and traditional medicine perspectives",
    backstory="You practice integrative medicine combining traditional "
              "Chinese medicine, herbalism, and self-healing modalities.",
    verbose=True
)

synthesizer = Agent(
    role="Medical Synthesizer",
    goal="Summarize and find consensus in the medical discussion",
    backstory="You are a medical professor who moderates discussions "
              "and synthesizes complex multi-specialty input into "
              "clear, actionable guidance.",
    verbose=True
)

# ─────────────────────────────────────────────────────────
# THE CASE TASK
# ─────────────────────────────────────────────────────────

case = """
Patient Profile:
- Age: 42
- Sex: Male
- Weight: 180 lbs
- Main Concerns: High blood pressure, fatigue, mild depression
- Secondary: Occasional joint pain
- Goal: Lower BP naturally, more energy, address depression without heavy meds
- Labs: Available but not uploaded yet
"""

case_task = Task(
    description=f"Analyze this health case and provide your specialist input:\n{case}",
    agent=dr_heart,  # Each agent does their own analysis
    expected_output="A detailed specialist perspective on the case"
)

# ─────────────────────────────────────────────────────────
# THE CREW (Round Table)
# ─────────────────────────────────────────────────────────

crew = Crew(
    agents=[dr_heart, nutri, longevity, holistics, synthesizer],
    tasks=[case_task],
    verbose=True
)

# ─────────────────────────────────────────────────────────
# RUN IT
# ─────────────────────────────────────────────────────────

result = crew.kickoff()
print(result)
```

---

## What You Need to Run This

### 1. Python installed (you probably have it)
### 2. Install CrewAI
```bash
pip install crewai
```

### 3. API keys (for AI models)
You have options:
- **OpenAI** — GPT-4 (you already have an account)
- **xAI/Grok** — their API (requires signup at x.ai)
- **Ollama** — local free models (no API needed)

### 4. A case to test with

---

## Next Steps to Build This

1. [ ] Install CrewAI on your machine
2. [ ] Get an API key (OpenAI or xAI)
3. [ ] Write the agent definitions
4. [ ] Create a simple case submission form
5. [ ] Run the first test case
6. [ ] Add more agents
7. [ ] Build the web interface

---

## Integration Possibilities

### With Grok/xAI
xAI is building Grok — once their API is available, Grok could be one of the agents (or the synthesizer). You'd sign up at x.ai and get an API key, same as OpenAI.

### With your Health Tracker
The health tracker we're building with Google Sheets could feed data into the round table — anonymized stats, supplements, symptoms could be automatically included in cases.

---

## Why CrewAI Makes Sense

1. **Built for this** — multi-agent collaboration is the core use case
2. **Clean syntax** — easy to define agents and tasks
3. **Flexible** — agents can use tools, search the web, read files
4. **Popular** — active development, good community
5. **Works with Ollama** — free local models option

---

## Cost to Start

| Item | Cost |
|------|------|
| CrewAI | Free |
| Ollama (local models) | Free |
| OpenAI API (test usage) | ~$0.10 |
| xAI API (when available) | TBD |

---

_Let me know if you want to start installing CrewAI and testing this._
