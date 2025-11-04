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

import gradio as gr

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
    if techsupport_mode:
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
    --bg: #071428; /* deep navy background */
    --panel: #0b1724; /* dark slate panel */
    --card: #0f2636; /* chat bubble background */
    --user-bubble: #142534; /* user bubble */
    --assistant-bubble: #0b1622; /* assistant bubble */
    --primary: #0A84FF; /* electric blue accent */
    --primary-600: #0C7BE6;
    --muted: #9FB7D6; /* muted blue-gray text */
    --text: #E6F0F8;
}

body { background: var(--bg); color: var(--text); font-family: Inter, Poppins, 'Segoe UI', Roboto, Arial, sans-serif; }
.gradio-container { background: transparent; }
.app-title { color: var(--primary); font-weight: 700; }
.app-sub { color: var(--muted); opacity: 0.95; }
.footer { color: var(--muted); opacity: 0.9; margin-top: 12px; }
/* Chat bubbles */
.gradio-chatbot .message { border-radius: 14px; padding: 14px; box-shadow: 0 8px 20px rgba(2,6,23,0.6); max-width: 88%; }
.gradio-chatbot .message.user { background: var(--user-bubble); color: var(--text); align-self: flex-end; }
.gradio-chatbot .message.bot { background: var(--assistant-bubble); color: var(--text); align-self: flex-start; }
.gradio-chatbot { background: transparent; }
/* Buttons */
.gr-button { border-radius: 12px; background: linear-gradient(180deg, var(--primary), var(--primary-600)); color: white; box-shadow: 0 6px 18px rgba(10,132,255,0.12); }
.gr-button:hover { background: #33CFFF; }
.panel { border-radius: 12px; background: var(--panel); box-shadow: 0 10px 40px rgba(2,6,23,0.6); }
.gradio-input textarea { background: #071a2a; color: var(--text); border-radius: 10px; }
.gradio-container .gradio-row { gap: 12px; }
""")


def build_ui():
    with gr.Blocks(css=css, theme="default") as demo:
        gr.Markdown("<h1 class='app-title'>💡 AI Tech Assistant</h1>")
        gr.Markdown("<p class='app-sub'>Your personal enterprise AI helper.</p>")

        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(elem_id="chatbot", label="AI Assistant", type="messages")
                user_input = gr.Textbox(placeholder="Describe the customer symptom...", show_label=False, lines=2)
                with gr.Row():
                    send_btn = gr.Button("Send", variant="primary")
                    clear_btn = gr.Button("Clear")
            with gr.Column(scale=1):
                gr.Markdown("### Parameters")
                temp = gr.Slider(minimum=0.0, maximum=1.0, value=0.3, step=0.01, label="Temperature")
                max_results = gr.Dropdown(choices=[1,2,3,4,5,10], value=5, label="Max sources to show")
                model_name = gr.Textbox(label="Model", value=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
                techsupport_mode = gr.Checkbox(label="Tech support prompt", value=True)
                gr.Markdown("---")
                gr.Markdown("Built by Marwa Monsour", elem_classes="footer")

                # event bindings (must be inside the Blocks context)
                send_btn.click(fn=handle_message, inputs=[user_input, chatbot, temp, max_results, model_name, techsupport_mode], outputs=[chatbot, user_input])
                user_input.submit(fn=handle_message, inputs=[user_input, chatbot, temp, max_results, model_name, techsupport_mode], outputs=[chatbot, user_input])
                clear_btn.click(lambda: ([], ""), None, [chatbot, user_input])

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
