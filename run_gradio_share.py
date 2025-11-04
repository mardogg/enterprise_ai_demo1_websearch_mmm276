"""
Launch the Gradio app with a public share link so the UI is viewable remotely.
This script calls build_ui() from app.py and launches with share=True.
"""
import os
import argparse
from dotenv import load_dotenv
load_dotenv()

# Import the UI builder and run with share=True
from app import build_ui


def main():
    parser = argparse.ArgumentParser(description="Launch Gradio app with optional port override")
    parser.add_argument("--port", "-p", type=int, help="Port to bind the Gradio server to (overrides GRADIO_SERVER_PORT)")
    args = parser.parse_args()

    # Port precedence: CLI arg -> GRADIO_SERVER_PORT env var -> default 7860
    port = None
    if args.port:
        port = args.port
    else:
        try:
            port = int(os.environ.get("GRADIO_SERVER_PORT", "7860"))
        except Exception:
            port = 7860

    demo = build_ui()
    demo.queue()
    # share=True creates a public url via gradio's tunneling service
    # Capture the return value from launch (some gradio versions return an object)
    server = demo.launch(share=True, server_name="0.0.0.0", server_port=port)

    # Try to extract a share_url if available and write it to a file so the user
    # can easily retrieve it from another terminal.
    share_url = None
    try:
        # Newer gradio returns an object with 'share_url' attribute
        share_url = getattr(server, "share_url", None)
    except Exception:
        share_url = None

    # Older gradio may return a tuple (local, share) or a string
    if not share_url:
        try:
            if isinstance(server, tuple) and len(server) >= 2:
                share_url = server[1]
            elif isinstance(server, str) and server.startswith("http"):
                share_url = server
        except Exception:
            share_url = None

    if share_url:
        print(f"Gradio share URL: {share_url}")
        try:
            with open("gradio_share_url.txt", "w", encoding="utf-8") as f:
                f.write(share_url)
        except Exception:
            pass
    else:
        print("Gradio started but share URL could not be programmatically determined. Please check the terminal output for the public link.")


if __name__ == "__main__":
    main()
