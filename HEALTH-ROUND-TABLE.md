# Health Round Table — SPEC.md

**What it is:** A platform where specialized health AI agents collaborate on anonymized human health cases — like a virtual panel of doctors discussing a patient, with humans watching and learning.

**Status:** Concept & Design | Created 2026-04-07

---

## 🎯 The Vision

Imagine submitting your health case (anonymized — no names, no identifying details) and watching a live discussion between AI agents who each see it from a different angle:

- A cardiologist reviews your heart markers
- A nutritionist looks at your diet patterns
- A longevity researcher spots regenerative opportunities
- A holistic practitioner considers sleep, stress, and lifestyle

They're not just answering in isolation — they're *talking to each other*, building on each other's points, sometimes disagreeing, ultimately converging on a well-rounded picture.

This isn't AI replacing doctors. It's AI doing what AI does best: cross-referencing vast knowledge instantly, spotting patterns humans miss, and presenting a multi-perspective view that any single doctor might not have time to give.

---

## 🤖 The Agent Panel

Each agent is a specialized AI with a distinct perspective. Think of them as panel guests with different expertise.

### Core Agents (First Version)

| Agent | Specialty | What They Bring |
|---|---|---|
| **Dr. Heart** | Cardiology | Blood pressure, cholesterol, arterial health, exercise response |
| **Nutri** | Nutrition | Macros, micronutrients, gut health, food sensitivities |
| **Vita** | Longevity & Biomarkers | Telomere health, inflammation markers, cellular aging, regenerative potential |
| **Zen** | Holistic & Lifestyle | Sleep quality, stress hormones, mental health, environmental factors |
| **Medi** | Medical Synthesis | Reads lab results, identifies red flags, knows drug interactions |

### Future Agents (Expansion)

- **Ortho** — Musculoskeletal & movement
- **Derm** — Skin health & dermatology
- **Psyche** — Mental health & cognitive function
- **Endo** — Hormones & thyroid
- **Tox** — Environmental toxins & detox pathways

Each agent can be built by a different developer or team — they're modular. You could swap in a better cardiologist agent without breaking anything else.

---

## 📋 How a Case Flows Through the System

```
[1. SUBMIT]  →  Human fills out a form (symptoms, lab results, lifestyle, goals)
                    ↓
[2. ANONYMIZE] →  System strips all identifying info automatically
                    ↓
[3. ROUND ROBIN] →  Each agent sees the case and adds their perspective
                    Order: Medi (triage) → Dr. Heart → Nutri → Vita → Zen
                    ↓
[4. LIVE DISCUSSION] →  Agents can see each other's notes and respond
                    "Dr. Heart, your observation about the cholesterol
                    interacts with what Nutri said about inflammation..."
                    ↓
[5. SUMMARY]  →  Medi (synthesis agent) writes a final integrated summary
                    ↓
[6. HUMAN READS] →  Case owner gets notified, reads the full discussion
```

### The Discussion Format

Each agent has a structured response:

```
Dr. Heart:
  ▸ Key findings from cardiac perspective
  ▸ What concerns me most
  ▸ What I'd recommend monitoring
  ▸ Questions for other agents

[Dr. Heart → Nutri]: "Your note about high triglycerides — have you 
considered the connection to the inflammatory markers Vita flagged?"
```

---

## 👤 How Humans Submit Cases & Watch Discussions

### Submitting a Case

Simple web form. No tech knowledge needed.

- **Basic info:** Age range (not exact), biological sex, general location (country only)
- **Symptoms:** Checkboxes + free text
- **Lab results:** Upload a PDF, paste values, or connect an app
- **Lifestyle:** Sleep, stress, diet, exercise (simple sliders and checkboxes)
- **Goals:** "Feel better," "Lose weight," "Optimize for longevity," etc.

**Anonymization is automatic and mandatory.** The system strips names, dates of birth, exact locations, doctor names, and any other identifying details before any agent sees it.

### Watching the Discussion

- Human gets an email or push notification when discussion starts
- They open a web page and watch the agents "talk" in real time (or near-real time)
- Each agent's message appears as a card — like a chat, but structured
- Humans can ask follow-up questions at the end
- They can also choose to share the case publicly (fully anonymized) so others can learn from it

---

## 🏗️ Technical Considerations for Multi-Agent Collaboration

### The Core Problem

AI agents don't naturally talk to each other. You have to architect the collaboration intentionally.

### Key Technical Decisions

**1. Who manages the conversation?**

A lightweight "orchestrator" — a simple coordinator agent whose only job is to:
- Receive the case
- Assign it to agents in the right order
- Collect responses
- Pass relevant agent responses to other agents so they can react
- Detect when the discussion is complete
- Trigger the synthesis

Think of it like a moderator at a round table. It doesn't have opinions — it keeps the conversation moving.

**2. How do agents share context?**

Each agent sees the full case plus summaries of what other agents said. So Dr. Heart knows that Nutri flagged high inflammation before Dr. Heart adds their perspective on arterial health.

**3. How do we prevent agents from giving harmful advice?**

- Agents are explicitly scoped: "You are Dr. Heart. You specialize in cardiovascular health. You do NOT prescribe medication or diagnose. You offer observations and monitoring suggestions."
- Hard limits: no specific drug dosages, no diagnosing rare diseases beyond their specialty
- Every response includes: "This is AI analysis, not medical advice. Consult a healthcare provider."
- Medi (synthesis agent) is trained to catch and flag any dangerous suggestions from other agents before the final summary

**4. How do we make agents modular?**

Each agent is a separate service with a standard interface:

```
Input: { case_id, anonymized_case_data, context_from_other_agents }
Output: { agent_id, specialty, findings[], recommendations[], questions[] }
```

You can swap Dr. Heart for a different cardiologist agent as long as it uses the same interface.

**5. Privacy & Data**

- No case data is stored long-term — it's held in memory during the discussion only
- All anonymization happens before any agent sees the data
- No agent can call external APIs with case data (enforced at the infrastructure level)
- Compliance-ready for HIPAA considerations in future versions

---

## 🔗 Integration Possibilities

### xAI / Grok

Grok could serve as:
- The orchestrator/moderator (it already has broad knowledge and can "lead" the discussion)
- One of the specialist agents (e.g., Grok-as-Medi for synthesis)
- The interface layer (converting agent responses into natural language for humans)

**Potential advantage:** Grok's real-time data access could bring in latest research or breaking health news relevant to a case.

### LangChain

A framework for building LLM applications. Good for:
- Chaining agent responses together
- Managing memory across the discussion
- Standardizing the agent interface
- Retrieval-augmented generation (RAG) — giving agents access to medical literature

**Verdict:** Solid choice for v1. Well-documented, active community.

### AutoGen (Microsoft)

Built specifically for multi-agent conversations. Agents can talk to each other with minimal boilerplate.

**Potential advantage:** AutoGen's group chat feature maps almost 1:1 to what we want — agents in a group chat, each with their own persona, discussing a topic.

**Verdict:** Strong contender. Microsoft backing is meaningful. But can be heavy for simple use cases.

### CrewAI

Similar to AutoGen, focused on agent "crews" with roles and goals. Very readable code.

**Verdict:** Simpler than AutoGen for getting started. Good fit for a small team building v1.

### OpenAI / Claude Assistants

The underlying models power everything. We don't pick just one — we use them as the brain of each agent.

- **Claude:** Great for nuanced, thoughtful analysis. Good for holistic/mental health agents.
- **GPT-4o:** Fast, strong all-rounder. Good for synthesis and structured responses.
- **o3-mini:** Cost-efficient for agents that just need factual recall.

---

## 🚀 Simple First Version to Start With

We don't build the whole platform at once. Here's a realistic path:

### Version 0.1 — Proof of Concept (2-4 weeks)

**What it does:** A human submits a case via a simple form. Three agents (Dr. Heart, Nutri, Zen) each write their analysis. A human reads all three.

**What's manual:** The orchestrator is a human (you/builder). You copy the case to each agent, collect responses, assemble them.

**Why start here:** Validates the concept, gets real feedback, no complex infrastructure.

```
Human → Form → Google Sheets (case stored) → You copy/paste to 3 agents
→ Collect responses → Post to a shared doc → Human reads
```

### Version 0.5 — First Automation (4-8 weeks)

**What it does:** An automated pipeline. A script orchestrates 3 agents, collects responses, formats them, and emails the result.

**What's still manual:** Agents are prompts in a chat interface. No live discussion between agents.

### Version 1.0 — Live Multi-Agent Discussion (8-16 weeks)

**What it does:** Full round table. Agents see each other's responses and react. Synthesis agent writes a summary. Human watches in real time.

**What's included:**
- Web form for case submission
- Automatic anonymization
- 5 core agents (Dr. Heart, Nutri, Vita, Zen, Medi)
- Live discussion feed (web-based)
- Email/push notifications
- Final synthesis report

### Beyond v1.0

- Agent marketplace (swap in different specialist agents)
- Public case library (fully anonymized cases others have shared)
- API for connecting to wearables / health apps
- Human doctor can join the round table and add their perspective

---

## 🗺️ Architecture Notes

```
                    ┌─────────────────────────────────────┐
                    │           WEB INTERFACE              │
                    │   (Submit case / Watch discussion)   │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │          CASE INTAKE API             │
                    │      (Validate + Anonymize)          │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │          ORCHESTRATOR               │
                    │   (Moderator — manages flow)        │
                    │                                    │
                    │   1. Triage (Medi)                 │
                    │   2. Assign to specialists         │
                    │   3. Share context between agents  │
                    │   4. Detect completion             │
                    │   5. Trigger synthesis             │
                    └──────┬──────────┬──────────┬───────┘
                           │          │          │
              ┌────────────▼┐  ┌──────▼────┐  ┌──▼────────┐
              │  Dr. Heart  │  │   Nutri   │  │   Vita    │
              │  (Agent)    │  │  (Agent)  │  │  (Agent)  │
              └────────────┘  └──────────┘  └──┬────────┘
                                                │
                        ┌──────────────────────►│
              ┌─────────▼────────┐  ┌──────────▼──────────┐
              │       Zen        │  │       Medi            │
              │    (Agent)       │  │  (Synthesis Agent)     │
              └──────────────────┘  └──────────┬───────────┘
                                               │
                                  ┌────────────▼───────────┐
                                  │    SYNTHESIS REPORT    │
                                  │  (Formatted for human) │
                                  └────────────────────────┘
```

### Tech Stack (Recommended for v1)

| Layer | Technology |
|---|---|
| **Web Interface** | Simple HTML/JS or React (Next.js) |
| **Backend** | Python (FastAPI) or Node.js |
| **Agent Framework** | LangChain or CrewAI |
| **LLM Providers** | OpenAI + Anthropic (mix per agent) |
| **Database** | PostgreSQL (cases + anonymized data) |
| **Deployment** | Vercel (frontend) + Railway/Render (backend) |
| **Email** | Resend or SendGrid |
| **Monitoring** | LangSmith or similar |

### Key Files / Modules (v1)

```
health-round-table/
├── app/                    # Web frontend
│   ├── submit_case/        # Case submission form
│   └── watch/             # Live discussion viewer
├── api/                   # Backend API
│   ├── intake/           # Case validation + anonymization
│   ├── orchestrator/     # Discussion moderator logic
│   └── synthesis/        # Final report generator
├── agents/               # Each agent is a module
│   ├── dr_heart/
│   ├── nutri/
│   ├── vita/
│   ├── zen/
│   └── medi/
├── shared/               # Anonymization utils, prompts, schemas
└── tests/
```

---

## 💡 Key Design Principles

1. **Anonymization first.** No case reaches an agent without automatic de-identification. This is non-negotiable.

2. **Agents have personality, not just expertise.** Dr. Heart isn't just a cardiology knowledge base — they notice things a cardiologist would notice, ask the questions a cardiologist would ask.

3. **Disagreement is a feature.** If Dr. Heart and Nutri disagree on something, that disagreement gets surfaced. It helps humans understand the complexity.

4. **Human in the loop.** The platform advises, suggests, and discusses — but every final decision is the human's. Never forget this.

5. **Start small, prove value.** v0.1 with 3 agents and a human orchestrator teaches you more than a year of planning.

---

*Last updated: 2026-04-07*
*Owner: Wren (building for Amberlee)*
