"""
Health Round Table - Social Layer
Public debates, shareable links, recent feed, voting.
"""

import gradio as gr
import requests
import uuid
import time
from datetime import datetime

API_KEY = "939d10536ea749c2ac9f1ae783335eaa.L8GP6pNpV7FVESvej9RAoDTT"
BASE_URL = "https://ollama.com"

headers = {"Authorization": f"Bearer {API_KEY}",
           "Content-Type": "application/json"}

# In-memory store (resets on restart - noted limitation for free tier)
debates_db = {}  # debate_id -> {case, goals, constraints, results, votes, timestamp, status}
recent_ids = []   # ordered list of debate IDs (newest first)


def chat(model, system, user_message):
    payload = {"model": model, "messages": [{"role": "system", "content": system}, {
        "role": "user", "content": user_message}], "stream": False}
    response = requests.post(
        f"{BASE_URL}/api/chat",
        headers=headers,
        json=payload)
    if response.status_code != 200:
        raise Exception(f"Error {response.status_code}: {response.text}")
    return response.json()["message"]["content"]


def run_debate(discussion_state, case, goals, constraints, model_choice):
    """Generator that yields messages one by one - enables streaming in Gradio"""
    discussion = []
    context = ""
    if goals:
        context += f"\n\nPATIENT GOALS:\n{goals}"
    if constraints:
        context += f"\n\nIMPORTANT CONSTRAINTS:\n{constraints}"

    yield {"debate_id": discussion_state["debate_id"], "messages": discussion.copy(), "status": "starting"}

    # Dr. Heart
    discussion.append({"role": "assistant",
                       "content": "❤️ Dr. Heart is analyzing the case..."})
    yield {"debate_id": discussion_state["debate_id"], "messages": discussion.copy(), "status": "dr_heart"}
    dr_heart_system = f"""You are Dr. Heart, a board-certified cardiologist. Focus on BP, cholesterol, circulation.{context}
IMPORTANT: Give practical, actionable advice."""
    try:
        dr_heart_response = chat(
            model_choice,
            dr_heart_system,
            f"Analyze: {case}")
        discussion.append({"role": "assistant",
                           "content": f"**Dr. Heart:**\n{dr_heart_response}"})
    except Exception as e:
        discussion.append({"role": "assistant",
                           "content": f"Dr. Heart error: {str(e)}"})
        yield {"debate_id": discussion_state["debate_id"], "messages": discussion.copy(), "status": "done"}
        return

    # Nutri
    discussion.append({"role": "assistant",
                       "content": "🍔 Nutri is reviewing Dr. Heart's analysis..."})
    yield {"debate_id": discussion_state["debate_id"], "messages": discussion.copy(), "status": "nutri"}
    nutri_system = f"""You are Nutri, a functional medicine nutritionist. Build on Dr. Heart's foundation.{context}"""
    try:
        nutri_response = chat(
            model_choice,
            nutri_system,
            f"React to Dr. Heart and add nutrition perspective:\n=== DR. HEART ===\n{dr_heart_response}\n=== END ===\nCase: {case}")
        discussion.append({"role": "assistant",
                           "content": f"**Nutri:**\n{nutri_response}"})
    except Exception as e:
        discussion.append(
            {"role": "assistant", "content": f"Nutri error: {str(e)}"})
        yield {"debate_id": discussion_state["debate_id"], "messages": discussion.copy(), "status": "done"}
        return

    # Longevity
    discussion.append({"role": "assistant",
                       "content": "⌛ Longevity is building on previous analyses..."})
    yield {"debate_id": discussion_state["debate_id"], "messages": discussion.copy(), "status": "longevity"}
    longevity_system = f"""You are Longevity, a longevity researcher. Add anti-aging perspective.{context}"""
    try:
        longevity_response = chat(
            model_choice,
            longevity_system,
            f"Build on Dr. Heart and Nutri:\n=== DR. HEART ===\n{dr_heart_response}\n=== NUTRI ===\n{nutri_response}\n=== END ===\nCase: {case}")
        discussion.append({"role": "assistant",
                           "content": f"**Longevity:**\n{longevity_response}"})
    except Exception as e:
        discussion.append({"role": "assistant",
                           "content": f"Longevity error: {str(e)}"})
        yield {"debate_id": discussion_state["debate_id"], "messages": discussion.copy(), "status": "done"}
        return

    # Holistics
    discussion.append({"role": "assistant",
                       "content": "🌿 Holistics is adding integrative perspective..."})
    yield {"debate_id": discussion_state["debate_id"], "messages": discussion.copy(), "status": "holistics"}
    holistics_system = f"""You are Holistics, integrative medicine practitioner.{context}"""
    try:
        holistics_response = chat(
            model_choice,
            holistics_system,
            f"Build on all previous:\n=== DR. HEART ===\n{dr_heart_response}\n=== NUTRI ===\n{nutri_response}\n=== LONGEVITY ===\n{longevity_response}\n=== END ===\nCase: {case}")
        discussion.append({"role": "assistant",
                           "content": f"**Holistics:**\n{holistics_response}"})
    except Exception as e:
        discussion.append({"role": "assistant",
                           "content": f"Holistics error: {str(e)}"})
        yield {"debate_id": discussion_state["debate_id"], "messages": discussion.copy(), "status": "done"}
        return

    # Synthesizer
    discussion.append({"role": "assistant",
                       "content": "🤝 Synthesizer is building consensus..."})
    yield {"debate_id": discussion_state["debate_id"], "messages": discussion.copy(), "status": "synthesizer"}
    synthesizer_system = f"""You are the Synthesizer, medical professor. Create consensus.{context}
IMPORTANT: Give clear numbered recommendations."""
    try:
        synthesizer_response = chat(
            model_choice,
            synthesizer_system,
            f"Create consensus:\n=== DR. HEART ===\n{dr_heart_response}\n=== NUTRI ===\n{nutri_response}\n=== LONGEVITY ===\n{longevity_response}\n=== HOLISTICS ===\n{holistics_response}\n=== END ===")
        discussion.append(
            {"role": "assistant", "content": f"**Synthesizer:**\n{synthesizer_response}"})
    except Exception as e:
        discussion.append({"role": "assistant",
                           "content": f"Synthesizer error: {str(e)}"})
        yield {"debate_id": discussion_state["debate_id"], "messages": discussion.copy(), "status": "done"}
        return

    discussion.append({"role": "assistant",
                       "content": "✅ Round Table Complete!"})
    yield {"debate_id": discussion_state["debate_id"], "messages": discussion.copy(), "status": "done"}


def create_debate_id():
    """Generate a short, URL-safe debate ID"""
    return str(uuid.uuid4())[:8]


def submit_new_debate(case, goals, constraints, model_choice):
    """Create a new debate and return its ID"""
    debate_id = create_debate_id()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    debates_db[debate_id] = {
        "case": case,
        "goals": goals,
        "constraints": constraints,
        "model": model_choice,
        "results": None,
        "votes": 0,
        "timestamp": timestamp,
        "status": "pending"
    }

    # Add to recent IDs (newest first)
    recent_ids.insert(0, debate_id)
    if len(recent_ids) > 20:
        recent_ids.pop()

    return debate_id, f"Debate created! ID: {debate_id}"


def vote_debate(debate_id, direction):
    """Vote on a debate (+1 or -1)"""
    if debate_id in debates_db:
        debates_db[debate_id]["votes"] += direction
    return debates_db.get(debate_id, {}).get("votes", 0)


def get_recent_debates():
    """Get recent debates for the home page feed"""
    feed = []
    for bid in recent_ids:
        if bid in debates_db:
            d = debates_db[bid]
            case_preview = d["case"][:80] + \
                "..." if len(d["case"]) > 80 else d["case"]
            feed.append({
                "id": bid,
                "case": case_preview,
                "votes": d["votes"],
                "timestamp": d["timestamp"],
                "status": d["status"]
            })
    return feed

# ============================================================
# GRADIO UI - Social Layer with Tabs
# ============================================================


with gr.Blocks(title="Health Round Table - Social") as social_demo:

    gr.Markdown("""# Health Round Table - Social
    *Public debates. Anonymous. Real specialists. Not medical advice.*
    """)

    debate_id_state = gr.State("")

    with gr.Tabs():
        # ---- HOME / RECENT DEBATES ----
        with gr.TabItem("🏠 Home - Recent Debates"):
            gr.Markdown("## Recent Debates")
            feed_display = gr.DataFrame(
                headers=[
                    "Debate ID",
                    "Case Preview",
                    "Votes",
                    "Submitted",
                    "Status"],
                label="Public Debates",
                interactive=False,
                wrap=True,
                column_widths=[120, 400, 80, 140, 100]
            )
            refresh_btn = gr.Button("🔄 Refresh Feed")
            refresh_btn.click(fn=get_recent_debates, outputs=feed_display)

            gr.Markdown("---")
            gr.Markdown("### Submit a New Case")
            new_case_input = gr.Textbox(
                label="Patient Case",
                placeholder="42yo male, BP 145/95, fatigue...",
                lines=5)
            new_goals_input = gr.Textbox(
                label="Goals (optional)",
                placeholder="Lower BP, more energy...",
                lines=2)
            new_constraints_input = gr.Textbox(
                label="Constraints (optional)",
                placeholder="No pharma, vegetarian...",
                lines=2)
            new_model_choice = gr.Dropdown(
                choices=[
                    ("Mistral Large",
                     "mistral-large-3:675b"),
                    ("Qwen3",
                     "qwen3-vl:235b-instruct"),
                    ("DeepSeek",
                     "deepseek-v3.2")],
                value="mistral-large-3:675b", label="Model"
            )
            new_submit_btn = gr.Button(
                "🚀 Submit Case & Start Debate",
                variant="primary")
            new_output = gr.Textbox(label="Result", lines=3, interactive=False)
            new_submit_btn.click(
                fn=submit_new_debate,
                inputs=[
                    new_case_input,
                    new_goals_input,
                    new_constraints_input,
                    new_model_choice],
                outputs=[new_output]
            )

        # ---- SUBMIT NEW ----
        with gr.TabItem("➕ Submit Case"):
            gr.Markdown("## Submit a New Case Study")
            gr.Markdown(
                "Enter a health case below. All fields optional except the case itself.")
            case_input = gr.Textbox(
                label="Patient Case *",
                placeholder="Describe the case...",
                lines=6)
            goals_input = gr.Textbox(
                label="Goals",
                placeholder="What should the patient achieve?",
                lines=2)
            constraints_input = gr.Textbox(
                label="Constraints",
                placeholder="Any limitations? (no pharma, vegetarian, etc.)",
                lines=2)
            model_choice = gr.Dropdown(
                choices=[
                    ("Mistral Large",
                     "mistral-large-3:675b"),
                    ("Qwen3",
                     "qwen3-vl:235b-instruct"),
                    ("DeepSeek",
                     "deepseek-v3.2")],
                value="mistral-large-3:675b", label="Model"
            )
            submit_btn = gr.Button(
                "🚀 Run Health Round Table",
                variant="primary")
            clear_btn = gr.Button("🔄 Clear")
            clear_btn.click(
                fn=lambda: [
                    None,
                    None,
                    None,
                    None,
                    None],
                inputs=[],
                outputs=[
                    case_input,
                    goals_input,
                    constraints_input,
                    model_choice,
                    output_chatbot])

        # ---- DISCUSSION (shown after submission) ----
        with gr.TabItem("💬 Discussion"):
            gr.Markdown("## Round Table Discussion")
            gr.Markdown(
                "*Watch specialists debate in real-time as each agent completes their analysis.*")
            output_chatbot = gr.Chatbot(label="Discussion Feed", height=600)
            debate_id_display = gr.Textbox(
                label="Debate ID (copy to share)", interactive=False, lines=1)

    # Outputs for submit tab
    submit_outputs = [output_chatbot, debate_id_display]

    # Link submit button to debate runner
    submit_btn.click(
        fn=run_debate,
        inputs=[
            debate_id_state,
            case_input,
            goals_input,
            constraints_input,
            model_choice],
        outputs=submit_outputs
    )

    # Vote buttons on home feed
    with gr.TabItem("👍 Upvote"):
        gr.Textbox(label="Enter Debate ID to Upvote", lines=1)

    # Initialize feed on load
    social_demo.load(fn=get_recent_debates, outputs=feed_display)

if __name__ == "__main__":
    print("Starting Health Round Table - Social Layer...")
    print("Open https://health-round-table.onrender.com")
    social_demo.launch(server_name="0.0.0.0", server_port=7861)
