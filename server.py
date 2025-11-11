"""
Simple Flask server to serve the React frontend and provide API endpoints.
"""
import os
import sys
from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# Force unbuffered output
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buffering=1)

load_dotenv()

from src.search_service import SearchService
from src.models import SearchOptions, SearchError
from src.troubleshooter import generate_troubleshoot_result
from src.youtube_service import search_youtube

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

API_KEY = os.getenv("OPENAI_API_KEY")
print(f"OpenAI API Key loaded: {'Yes' if API_KEY else 'No'}")
if API_KEY:
    print(f"API Key starts with: {API_KEY[:10]}...")
service = SearchService(api_key=API_KEY) if API_KEY else None
print(f"SearchService initialized: {service is not None}")

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    try:
        return send_from_directory(app.static_folder, path)
    except:
        return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/generate-plan', methods=['POST'])
def api_generate_plan():
    print("=== API CALLED ===")
    if not service:
        print("ERROR: OpenAI API key not configured")
        return jsonify({"error": "OpenAI API key not configured"}), 500
    
    data = request.json
    product_type = data.get('productType', '')
    brand = data.get('brand', '')
    model = data.get('model', '')
    issue = data.get('issue', '')
    details = data.get('details', '')
    
    print(f"Received request - Type: {product_type}, Brand: {brand}, Model: {model}")
    print(f"Issue: {issue}")
    print(f"Details: {details}")
    
    try:
        # Use gpt-4o (reasoning_effort not supported on this model)
        result, raw_response = generate_troubleshoot_result(
            service, product_type, brand, model, issue, details,
            model_name="gpt-4o",
            reasoning_effort="low"  # This will be ignored for gpt-4o
        )
        print(f"Generated result - Hypothesis: {result.hypothesis[:100]}...")
        print(f"Raw AI response: {raw_response[:200]}...")
        return jsonify({
            "observations": result.observations,
            "hypothesis": result.hypothesis,
            "actionPlan": result.actionPlan,
            "escalationCriteria": result.escalationCriteria,
            "warnings": result.warnings or [],
            "suggestedKeywords": result.suggestedKeywords or []
        })
    except SearchError as e:
        print(f"SearchError: {e.message}")
        return jsonify({"error": e.message}), 500
    except Exception as e:
        print(f"Exception: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/youtube-search', methods=['POST'])
def api_youtube_search():
    data = request.json
    query = data.get('query', '')
    
    try:
        videos = search_youtube(
            data.get('productType', ''),
            data.get('brand', ''),
            data.get('model', ''),
            data.get('keywords', [])
        )
        return jsonify(videos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
