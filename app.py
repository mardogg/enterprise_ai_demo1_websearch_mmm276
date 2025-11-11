"""
Gradio-based chat UI for the AI Tech Assistant

Run with:
    python app.py

This UI uses the existing SearchService in src/search_service.py.
"""

import os
import textwrap
import traceback
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    # We'll allow startup without a key but will display a clear message in the UI
    API_KEY = None

from src.search_service import SearchService
from src.models import SearchOptions, SearchError
from src.troubleshooter import generate_troubleshoot_result
from src.youtube_service import search_youtube
from src import diagnostics as diag

import gradio as gr

# ---------- Helpers for new wizard UI ----------
def _md_list(items, numbered=False):
    if not items:
        return ""
    if numbered:
        return "\n".join(f"{i+1}. {it}" for i, it in enumerate(items))
    return "\n".join(f"- {it}" for it in items)

def _iframe_html(video_id: str, title: str = "Tutorial") -> str:
    title_attr = title.replace('"', "'") or "Tutorial"
    return (
        f"<div class='video-wrapper'><iframe width='560' height='315' title='{title_attr}' "
        f"src='https://www.youtube.com/embed/{video_id}' frameborder='0' "
        "allow='accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture' allowfullscreen></iframe></div>"
    )

# Map temperature to reasoning effort used by SearchOptions
def _map_temp_to_effort(temp: float) -> str:
    if temp <= 0.33:
        return "low"
    if temp <= 0.66:
        return "medium"
    return "high"


def _format_citations(citations, max_results: int) -> str:
    if not citations:
        return ""
    lines = []
    for i, c in enumerate(citations[:max_results], start=1):
        # Citation has title and url on the model
        try:
            title = getattr(c, "title", None) or getattr(c, "url", "")
            url = getattr(c, "url", "")
        except Exception:
            title = str(c)
            url = ""
        if url:
            lines.append(f"[{i}] {title} — {url}")
        else:
            lines.append(f"[{i}] {title}")
    return "\n\nSources:\n" + "\n".join(lines)


def make_service():
    if not API_KEY:
        return None
    try:
        return SearchService(api_key=API_KEY)
    except Exception:
        return None


service = make_service()

# Handle a single user message and return updated chat history
def handle_message(user_message, chat_history, temperature, max_results, model_name, techsupport_mode):
    # chat_history may be either a list of (user, assistant) tuples (old "tuples" format)
    # or a list of dicts with {"role","content"} (Gradio 'messages' format).
    # Normalize to messages format (list of dicts) which Chatbot(type='messages') expects.
    if chat_history is None:
        chat_history = []

    msgs = []
    # detect tuples format
    if chat_history and isinstance(chat_history[0], tuple):
        for u, a in chat_history:
            msgs.append({"role": "user", "content": u})
            if a is not None:
                msgs.append({"role": "assistant", "content": a})
    else:
        # assume already messages format (list of dicts)
        msgs = list(chat_history)

    # Append the current user message as a 'user' role
    msgs.append({"role": "user", "content": user_message})

    # Lightweight intent guardrails: handle greetings and non-issue inputs gracefully
    msg_low = (user_message or "").strip().lower()
    greetings = ("hi", "hello", "hey", "yo", "hiya", "sup")
    is_greeting = any(msg_low == g or msg_low.startswith(g + " ") for g in greetings)
    issue_keywords = (
        "won't", "cant", "can't", "cannot", "error", "fail", "failed", "failing",
        "crash", "boot", "blue screen", "slow", "freeze", "frozen", "battery",
        "wifi", "network", "install", "update", "broken", "not working", "doesn't",
        "doesnt", "issue", "problem", "bug", "offline"
    )
    looks_like_issue = any(k in msg_low for k in issue_keywords) or len(msg_low) > 25

    # If techsupport mode is enabled but the message doesn't look like a problem, ask for details instead of generating a plan
    if techsupport_mode and not looks_like_issue:
        helper = (
            "Hi! To build a useful troubleshooting plan, please share: device/model, OS, exact symptoms, any error messages, "
            "and what you've already tried. Example: 'Dell XPS 13, Windows 11. Won't boot: power LED blinks 2x amber/1x white. "
            "Tried different charger; no change.'"
        )
        msgs.append({"role": "assistant", "content": helper})
        return msgs, ""

    # If not in techsupport mode and this is just a greeting, keep it conversational
    if (not techsupport_mode) and is_greeting:
        helper = "Hi there! Tell me what you need help with. Enable 'Tech support prompt' for a structured troubleshooting plan."
        msgs.append({"role": "assistant", "content": helper})
        return msgs, ""

    # If service not available, show friendly error
    if service is None:
        error_msg = "⚠️ Error: OpenAI API key not configured. Please set OPENAI_API_KEY in .env or pass it to the server."
        # replace last user message with assistant error reply in messages format
        msgs.append({"role": "assistant", "content": error_msg})
        return msgs, ""

    # Build options
    reasoning = _map_temp_to_effort(float(temperature))
    options = SearchOptions(model=model_name or os.getenv("OPENAI_MODEL", "gpt-4o-mini"), reasoning_effort=reasoning)

    # If techsupport_mode is enabled, wrap the user message in a detailed
    # troubleshooting prompt so the assistant returns a full diagnostic
    # summary (hypotheses, step-by-step diagnostics, safety warnings,
    # fix paths, and escalation criteria).
    if techsupport_mode and looks_like_issue:
        prompt = textwrap.dedent(f"""
        You are an expert PC/Mac repair technician. Create a concise, field-ready troubleshooting plan for the following customer issue.

        Output exactly in this structure:
        ## Quick Hypotheses
        - (3–6 bullets of likely causes)

        ## Diagnostics (Step-by-Step)
        1. ...
        2. ...
        3. ...
           - If success: ...
           - If fails: ...

        ## Safety & Data-Loss Warnings
        - ...

        ## Fix Paths
        - ...

        ## When to Escalate
        - (criteria for parts order, depot send-out, vendor handoff, DRD L2/L3, etc.)

        Customer issue: {user_message}
        """).strip()
    else:
        prompt = user_message

    try:
        result = service.search(prompt, options)
        assistant_text = result.text
        # append citations limited by max_results
        assistant_text += _format_citations(result.citations, int(max_results))

        # Append assistant response to messages
        msgs.append({"role": "assistant", "content": assistant_text})

    except SearchError as e:
        msgs.append({"role": "assistant", "content": f"⚠️ Error: {e.message}"})
    except Exception as e:
        tb = traceback.format_exc()
        chat_history_repr = f"⚠️ Error: {str(e)}"
        msgs.append({"role": "assistant", "content": chat_history_repr})

    return msgs, ""


# UI build
css = textwrap.dedent("""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
:root {
    --bg: #0b0f14; /* charcoal */
    --panel: #111820; /* deep slate */
    --card: #131e29; /* panel cards */
    --accent: #14b8a6; /* teal */
    --accent-600: #0ea5a3;
    --muted: #9aa7b2; /* muted gray */
    --text: #e8eef3;
    --outline: rgba(255,255,255,0.06);
}

body { background: var(--bg); color: var(--text); font-family: Inter, Poppins, 'Segoe UI', Roboto, Arial, sans-serif; }
.gradio-container { background: transparent; }
.app-title { color: var(--text); font-weight: 700; letter-spacing: 0.2px; }
.app-sub { color: var(--muted); opacity: 0.95; }
.footer { color: var(--muted); opacity: 0.9; margin-top: 16px; }
.panel { border-radius: 14px; background: var(--panel); border: 1px solid var(--outline); box-shadow: 0 10px 30px rgba(0,0,0,0.35); padding: 14px; }
.card { border-radius: 14px; background: var(--card); border: 1px solid var(--outline); padding: 12px 14px; }
.section-title { color: var(--accent); font-weight: 600; margin: 8px 0 6px; }
.video-wrapper { position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; border-radius: 12px; border: 1px solid var(--outline); }
.video-wrapper iframe { position: absolute; top: 0; left: 0; width: 100%; height: 100%; }
.gr-button { border-radius: 12px; background: linear-gradient(180deg, var(--accent), var(--accent-600)); color: white; box-shadow: 0 6px 18px rgba(20,184,166,0.18); border: none; }
.gr-button:hover { filter: brightness(1.05); }
.gradio-container .gradio-row { gap: 14px; }
""")


def build_ui():
    with gr.Blocks(css=css, theme="default") as demo:
        gr.Markdown("<h1 class='app-title'>AI Tech Assistant</h1>")
        gr.Markdown("<p class='app-sub'>A cleaner workflow: enter your device and issue on the left. Your plan and tutorial appear on the right.</p>")

        with gr.Row():
            # Left: Inputs
            with gr.Column(scale=2):
                with gr.Group(elem_classes="panel"):
                    gr.Markdown("<div class='section-title'>Step 1 — Identify Device</div>")
                    product_type = gr.Dropdown(
                        label="Product Type", choices=[
                            "Laptop/PC", "Smartphone", "Tablet", "Router/Modem", "Game Console", "Printer", "Smart TV", "Other"
                        ], value=None, info="Required"
                    )
                    brand = gr.Textbox(label="Brand", placeholder="Dell, Apple, Netgear...", info="Required")
                    model = gr.Textbox(label="Model", placeholder="XPS 13, iPhone 12, R7000...", info="Required")

                with gr.Group(elem_classes="panel"):
                    gr.Markdown("<div class='section-title'>Step 2 — Describe Issue</div>")
                    issue_summary = gr.Textbox(label="Issue summary", placeholder="Overheating, won't boot, slow wifi...", info="Required")
                    details = gr.Textbox(label="Advanced details (optional)", lines=3, placeholder="Error messages, when it happens, what you've tried...")
                    with gr.Row():
                        temp = gr.Slider(minimum=0.0, maximum=1.0, value=0.3, step=0.01, label="Temperature")
                        model_name = gr.Textbox(label="Model (LLM)", value=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
                    generate_btn = gr.Button("Generate Plan", variant="primary")

            # Right: Outputs
            with gr.Column(scale=3):
                with gr.Group(elem_classes="panel"):
                    gr.Markdown("<div class='section-title'>Plan</div>")
                    with gr.Row():
                        with gr.Column():
                            obs_md = gr.Markdown(label="Observations", value="", elem_classes="card")
                            hyp_md = gr.Markdown(label="Hypothesis", value="", elem_classes="card")
                        with gr.Column():
                            plan_md = gr.Markdown(label="Action Plan", value="", elem_classes="card")
                            esc_md = gr.Markdown(label="When to Escalate", value="", elem_classes="card")
                    warn_md = gr.Markdown(label="Warnings", value="", elem_classes="card")

                with gr.Group(elem_classes="panel"):
                    gr.Markdown("<div class='section-title'>YouTube Helper</div>")
                    video_html = gr.HTML(value="", elem_id="yt_embed")
                    with gr.Row():
                        video_picker = gr.Dropdown(label="Pick a result", choices=[], value=None)
                        youtube_link = gr.Markdown(visible=True)
                    videos_state = gr.State(value={"videos": [], "query": ""})

        # Tools row: Diagnostics
        with gr.Row():
            with gr.Column(scale=2):
                with gr.Group(elem_classes="panel"):
                    gr.Markdown("<div class='section-title'>Diagnostics (optional)</div>")
                    consent = gr.Checkbox(label="Allow read-only local diagnostics", value=False)
                    redact = gr.Checkbox(label="Redact IPs", value=True)
                    run_diag = gr.Button("Run Diagnostics", interactive=False)
                    diag_summary = gr.Markdown(elem_classes="card")

                    def _toggle(cons):
                        return gr.update(interactive=bool(cons))
                    consent.change(_toggle, inputs=[consent], outputs=[run_diag])

                    def _run_diagnostics(redact_ips: bool):
                        results = diag.collect(redact_ips)
                        summary = diag.summarize(results)
                        def _sect(name):
                            items = summary.get(name, [])
                            return f"#### {name}\n" + ("\n" + _md_list(items) if items else "\n- No data")
                        md = "\n\n".join([_sect("Network"), _sect("Storage"), _sect("Performance"), _sect("Connectivity")])
                        return md
                    run_diag.click(_run_diagnostics, inputs=[redact], outputs=[diag_summary])

    # Generate callback
    def _generate(product_type, brand, model, issue_summary, details, temperature, model_name):
        # Validate required
        missing = []
        if not product_type:
            missing.append("Product Type")
        if not brand:
            missing.append("Brand")
        if not model:
            missing.append("Model")
        if not issue_summary:
            missing.append("Issue summary")
        if missing:
            msg = "Please complete required fields: " + ", ".join(missing)
            return (
                "-",  # obs
                f"⚠️ {msg}",
                "", "", "",
                gr.update(), gr.update(),  # video html and link
                [], None,  # picker choices, picker value
                {"videos": [], "query": ""},
            )

        if service is None:
            return (
                "-",
                "⚠️ OpenAI API key not configured.",
                "", "", "",
                gr.update(), gr.update(), [], None, {"videos": [], "query": ""}
            )

        # Generate LLM plan
        ts, raw = generate_troubleshoot_result(
            service,
            product_type, brand, model,
            issue_summary, details,
            model_name=model_name, reasoning_effort=_map_temp_to_effort(float(temperature))
        )

        # Render outputs
        obs = _md_list(ts.observations)
        hyp = ts.hypothesis
        plan = _md_list(ts.actionPlan, numbered=True)
        esc = _md_list(ts.escalationCriteria)
        warn = _md_list(ts.warnings or [])

        # YouTube helper
        yt = search_youtube(ts.productType, ts.brand, ts.model, ts.suggestedKeywords)
        vids = yt.get("videos", [])
        first = vids[0] if vids else {"videoId": "xQZ8dS2o3kI", "title": "Tutorial"}
        html = _iframe_html(first.get("videoId", ""), first.get("title", "Tutorial"))
        q = yt.get("query", "")
        link_md = f"Open full results on YouTube: [link](https://www.youtube.com/results?search_query={q.replace(' ', '+')})"
        state = {"videos": vids, "query": q}

        picker_choices = [v.get("title", f"Video {i+1}") for i, v in enumerate(vids)]
        picker_value = picker_choices[0] if picker_choices else None

        return (
            obs, hyp, plan, esc, warn,
            html, link_md,
            picker_choices, picker_value,
            state
        )
        # Wire events
        generate_btn.click(
            _generate,
            inputs=[product_type, brand, model, issue_summary, details, temp, model_name],
            outputs=[
                obs_md, hyp_md, plan_md, esc_md, warn_md,
                video_html, youtube_link,
                video_picker, video_picker,  # update choices and value
                videos_state,
            ]
        )

        issue_summary.submit(
            _generate,
            inputs=[product_type, brand, model, issue_summary, details, temp, model_name],
            outputs=[
                obs_md, hyp_md, plan_md, esc_md, warn_md,
                video_html, youtube_link,
                video_picker, video_picker,
                videos_state,
            ]
        )

        def _pick_video(title: str, state: dict):
            vids = state.get("videos", [])
            for v in vids:
                if v.get("title") == title:
                    return _iframe_html(v.get("videoId", ""), v.get("title", "Tutorial"))
            return gr.update()

        video_picker.change(_pick_video, inputs=[video_picker, videos_state], outputs=[video_html])

        gr.Markdown("Built by Marwa Monsour", elem_classes="footer")

    return demo


def main():
    demo = build_ui()
    # Use default queue configuration. Older/newer gradio versions may
    # not accept the concurrency_count kwarg, so call without it for
    # broader compatibility.
    demo.queue()
    # Allow launching on a port set via env var GRADIO_SERVER_PORT for flexibility
    try:
        server_port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))
    except Exception:
        server_port = 7860
    demo.launch(server_name="0.0.0.0", server_port=server_port, show_error=True)


if __name__ == "__main__":
    main()
