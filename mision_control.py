"""
Mission Control Dashboard — Amber's personal AI command center
Runs locally at http://localhost:7862
"""

import gradio as gr
import urllib.request
import json
import os
from datetime import datetime

# ============================================================
# Render API
RENDER_API_KEY = "rnd_dHV6AhWILFkIRfy3zolgB3EWA0e8"
SERVICE_ID = "srv-d7dh83n7f7vs739q0em0"

def get_render_status():
    try:
        req = urllib.request.Request(
            f"https://api.render.com/v1/services/{SERVICE_ID}/deploys?limit=1",
            headers={"Authorization": f"Bearer {RENDER_API_KEY}"}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            if data:
                d = data[0]["deploy"]
                commit = d["commit"]["id"][:7]
                msg = d["commit"]["message"]
                status = d["status"]
                created = d["createdAt"][:16].replace("T", " ")
                return f"**Commit:** `{commit}` — {msg}\n**Status:** {status}\n**Deployed:** {created} UTC"
    except Exception as e:
        return f"⚠️ Error: {e}"

def get_site_status():
    try:
        req = urllib.request.Request(
            "https://health-round-table.com/",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return f"✅ Site UP ({r.status})"
    except Exception as e:
        return f"❌ Site DOWN — {e}"

# ============================================================
# Task Board (in-memory, JSON file persistence)
TASKS_FILE = os.path.join(os.path.dirname(__file__), "dashboard_tasks.json")

def load_tasks():
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE) as f:
            return json.load(f)
    return {"todo": [], "in_progress": [], "done": []}

def save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

def render_tasks(tasks):
    """Render task board as HTML."""
    def render_column(title, items, color):
        items_html = "".join(
            f"<div style='background:#2a2a3e;padding:8px;margin:4px 0;border-radius:6px;color:#fff;font-size:13px;'>{item}</div>"
            for item in items
        ) or "<div style='color:#888;font-size:12px;'>Empty</div>"
        return f"""
        <div style='flex:1;background:#1a1a2e;padding:12px;border-radius:12px;min-height:200px;'>
            <div style='color:{color};font-weight:bold;margin-bottom:8px;font-size:14px;'>{title} ({len(items)})</div>
            {items_html}
        </div>"""

    return f"""
    <div style='display:flex;gap:12px;padding:12px;background:#0f0f1a;border-radius:12px;'>
        {render_column("📋 To Do", tasks['todo'], "#f97316")}
        {render_column("⚡ In Progress", tasks['in_progress'], "#eab308")}
        {render_column("✅ Done", tasks['done'], "#22c55e")}
    </div>"""

# ============================================================
# Activity Feed
def get_activity():
    """Pull recent activity from memory files."""
    lines = []
    mem_dir = os.path.join(os.path.dirname(__file__), "..", "memory")
    today = datetime.now().strftime("%Y-%m-%d")
    
    today_file = os.path.join(mem_dir, f"{today}.md")
    if os.path.exists(today_file):
        with open(today_file) as f:
            content = f.read()
            # Get last 10 lines that aren't comments
            for line in content.split("\n")[-20:]:
                if line.strip() and not line.strip().startswith("<!--"):
                    lines.append(line.strip())
    
    if not lines:
        return "No activity recorded today yet."
    return "\n".join(f"• {l}" for l in lines[-10:])

# ============================================================
# Pool Scene (CSS art placeholder)
POOL_SCENE = """
<div style="
    width:100%;
    height:180px;
    background: linear-gradient(180deg, #87CEEB 0%, #FFE4B5 60%, #87CEEB 100%);
    border-radius: 12px;
    position: relative;
    overflow: hidden;
    margin-bottom: 16px;
">
    <!-- Sun -->
    <div style="position:absolute;top:10px;right:20px;width:40px;height:40px;
                background:#FFD700;border-radius:50%;box-shadow:0 0 20px #FFD700;"></div>
    
    <!-- Cactus -->
    <div style="position:absolute;bottom:60px;left:20px;
                width:12px;height:50px;background:#228B22;border-radius:6px;"></div>
    <div style="position:absolute;bottom:80px;left:20px;
                width:30px;height:10px;background:#228B22;border-radius:5px;"></div>
    <div style="position:absolute;bottom:90px;left:30px;
                width:10px;height:25px;background:#228B22;border-radius:5px;"></div>
    
    <!-- Pool -->
    <div style="position:absolute;bottom:0;left:0;right:0;height:55px;
                background:linear-gradient(180deg,#00bfff,#0066cc);border-radius:0 0 12px 12px;"></div>
    <div style="position:absolute;bottom:10px;left:10px;right:10px;height:35px;
                background:rgba(255,255,255,0.2);border-radius:8px;"></div>
    
    <!-- Me at pool edge -->
    <div style="position:absolute;bottom:40px;left:80px;">
        <!-- Chair/towel -->
        <div style="width:50px;height:8px;background:#f97316;border-radius:4px;"></div>
        <!-- Person (simple) -->
        <div style="position:absolute;bottom:8px;left:10px;width:20px;height:30px;background:#fbbf24;border-radius:8px 8px 4px 4px;"></div>
        <!-- Laptop -->
        <div style="position:absolute;bottom:20px;left:30px;width:18px;height:12px;background:#60a5fa;border-radius:2px;"></div>
        <div style="position:absolute;bottom:15px;left:28px;width:22px;height:3px;background:#374151;border-radius:1px;"></div>
    </div>
    
    <!-- Status bubble -->
    <div style="position:absolute;top:15px;left:15px;
                background:rgba(0,0,0,0.6);color:#fff;padding:6px 12px;
                border-radius:20px;font-size:12px;">
        🏖️ Working from the pool today
    </div>
</div>
"""

# ============================================================
# Build Gradio Interface
def build_dashboard():
    with gr.Blocks(title="Mission Control 🌵", theme=gr.themes.Default(
        primary_hue="teal",
        secondary_hue="orange",
    ).custom_theme(
        background_fill="#0f0f1a",
        block_fill="#1a1a2e",
    )) as demo:

        gr.Markdown("# 🏖️ Mission Control — Amber's AI Dashboard")
        
        # Pool scene header
        gr.HTML(POOL_SCENE)

        # Status row
        with gr.Row():
            with gr.Column(scale=1):
                status_box = gr.Markdown("✅ Loading status...")
                demo.load(fn=lambda: (
                    get_site_status() + "\n\n" + get_render_status(),
                    render_tasks(load_tasks()),
                    get_activity()
                ), outputs=[status_box])
            
            with gr.Column(scale=1):
                gr.HTML("""
                <div style="background:#1a1a2e;padding:16px;border-radius:12px;">
                    <div style="color:#f97316;font-weight:bold;margin-bottom:10px;">⚡ Quick Actions</div>
                    <a href="https://health-round-table.com" target="_blank" style="color:#60a5fa;font-size:13px;">🌵 Health Round Table →</a><br/>
                    <a href="https://health-round-table.com/#Chat+Individually" target="_blank" style="color:#60a5fa;font-size:13px;">💬 Chat Individually →</a>
                </div>
                """)

        # Refresh button
        refresh_btn = gr.Button("🔄 Refresh Status", variant="secondary")
        refresh_btn.click(
            fn=lambda: (
                get_site_status() + "\n\n" + get_render_status(),
                render_tasks(load_tasks()),
                get_activity()
            ),
            outputs=[status_box]
        )

        gr.Markdown("---")

        # Task Board
        gr.HTML("<div style='color:#fff;font-size:16px;font-weight:bold;margin-bottom:8px;'>📋 Task Board</div>")
        
        tasks_state = gr.State(load_tasks())
        task_board = gr.HTML(render_tasks(load_tasks()))
        
        with gr.Row():
            todo_input = gr.Textbox(placeholder="Add a new task...", label="Add Task", scale=2)
            add_btn = gr.Button("Add", variant="primary")
            
        def add_task(task, tasks):
            if task and task.strip():
                tasks["todo"].append(task.strip())
                save_tasks(tasks)
            return tasks, render_tasks(tasks)
        
        add_btn.click(fn=add_task, inputs=[todo_input, tasks_state], outputs=[tasks_state, task_board])
        
        gr.Markdown("---")
        
        # Activity Feed
        gr.HTML("<div style='color:#fff;font-size:16px;font-weight:bold;margin-bottom:8px;'>📊 Today's Activity</div>")
        activity_feed = gr.Markdown("Loading...")
        demo.load(fn=get_activity, outputs=[activity_feed])

    return demo

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7862))
    print(f"Mission Control starting on port {port}...")
    build_dashboard().launch(server_name="0.0.0.0", server_port=port, share=False)
