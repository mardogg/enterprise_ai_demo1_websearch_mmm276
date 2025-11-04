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
def handle_message(user_message, chat_history, temperature, max_results, model_name):
    # chat_history is list of (user, assistant) tuples
    if chat_history is None:
        chat_history = []

    # Append user message
    chat_history.append((user_message, None))

    # If service not available, show friendly error
    if service is None:
        error_msg = "⚠️ Error: OpenAI API key not configured. Please set OPENAI_API_KEY in .env or pass it to the server."
        chat_history[-1] = (user_message, error_msg)
        return chat_history, ""

    # Build options
    reasoning = _map_temp_to_effort(float(temperature))
    options = SearchOptions(model=model_name or os.getenv("OPENAI_MODEL", "gpt-4o-mini"), reasoning_effort=reasoning)

    try:
        result = service.search(user_message, options)
        assistant_text = result.text
        # append citations limited by max_results
        assistant_text += _format_citations(result.citations, int(max_results))

        # Replace the last tuple (user, None) with actual assistant response
        chat_history[-1] = (user_message, assistant_text)

    except SearchError as e:
        chat_history[-1] = (user_message, f"⚠️ Error: {e.message}")
    except Exception as e:
        tb = traceback.format_exc()
        chat_history[-1] = (user_message, f"⚠️ Error: {str(e)}")

    return chat_history, ""


# UI build
css = textwrap.dedent("""
body { background: #0E1117; color: #FFFFFF; font-family: Inter, Poppins, sans-serif; }
.gradio-container { background: transparent; }
.app-title { color: #00AEEF; font-weight: 700; }
.app-sub { color: #FFFFFF; opacity: 0.85; }
.footer { color: #39FF14; opacity: 0.9; margin-top: 12px; }
/* Chat bubbles */
.gradio-chatbot .message { border-radius: 12px; padding: 12px; box-shadow: 0 6px 18px rgba(0,0,0,0.5); }
.gradio-chatbot .message.user { background: #1F2937; color: #FFFFFF; align-self: flex-end; }
.gradio-chatbot .message.bot { background: #111827; color: #FFFFFF; align-self: flex-start; }
/* Buttons */
.gr-button { border-radius: 12px; background: linear-gradient(180deg, #00AEEF, #0095CC); }
.gr-button:hover { background: #33CFFF; }
.panel { border-radius: 12px; background: #0E1117; box-shadow: 0 8px 30px rgba(0,0,0,0.6); }
""")


def build_ui():
    with gr.Blocks(css=css, theme="default") as demo:
        gr.Markdown("<h1 class='app-title'>💡 AI Tech Assistant</h1>")
        gr.Markdown("<p class='app-sub'>Your personal enterprise AI helper.</p>")

        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(elem_id="chatbot", label="AI Assistant")
                user_input = gr.Textbox(placeholder="Describe the customer symptom...", show_label=False, lines=2)
                with gr.Row():
                    send_btn = gr.Button("Send", variant="primary")
                    clear_btn = gr.Button("Clear")
            with gr.Column(scale=1):
                gr.Markdown("### Parameters")
                temp = gr.Slider(minimum=0.0, maximum=1.0, value=0.3, step=0.01, label="Temperature")
                max_results = gr.Dropdown(choices=[1,2,3,4,5,10], value=5, label="Max sources to show")
                model_name = gr.Textbox(label="Model", value=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
                gr.Markdown("---")
                gr.Markdown("Built by Marwa Monsour", elem_classes="footer")

        # event bindings
        send_btn.click(fn=handle_message, inputs=[user_input, chatbot, temp, max_results, model_name], outputs=[chatbot, user_input])
        user_input.submit(fn=handle_message, inputs=[user_input, chatbot, temp, max_results, model_name], outputs=[chatbot, user_input])
        clear_btn.click(lambda: ([], ""), None, [chatbot, user_input])

    return demo


def main():
    demo = build_ui()
    demo.queue(concurrency_count=4)
    demo.launch(server_name="0.0.0.0", server_port=7860, show_error=True)


if __name__ == "__main__":
    main()
