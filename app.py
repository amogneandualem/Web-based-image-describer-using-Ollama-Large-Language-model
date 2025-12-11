import base64
import requests
import os
import webbrowser 
import subprocess # Added for opening the folder
from flask import Flask, render_template, request, jsonify
from threading import Timer 

app = Flask(__name__)

# --- Configuration ---
OLLAMA_HOST = 'http://127.0.0.1:11434' 

# Models available for SELECTION (VLM) + the fixed Translation Model (LLM)
VLM_MODELS = {
    "moondream:1.8b": "Fast Captioning (VLM)", 
    "llava:latest": "Detailed Object Analysis (VLM)", 
}
TRANSLATOR_MODEL = "qwen2:7b" 
# --- End Configuration ---

# --- API Check Function (No Change) ---
def check_ollama_status():
    """Checks the health and model availability of the Ollama server."""
    try:
        health_response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        health_response.raise_for_status()

        installed_models = {model['name'] for model in health_response.json().get('models', [])}
        required_models = set(VLM_MODELS.keys()) | {TRANSLATOR_MODEL}
        missing_models = required_models - installed_models

        if missing_models:
            return {
                "status": "Warning",
                "message": f"Running, but missing models: {', '.join(missing_models)} ⚠️"
            }, 200
        
        return {"status": "Available", "message": "Available ✅"}, 200

    except requests.exceptions.ConnectionError:
        return {"status": "Error", "message": "Connection Failed ❌"}, 503
    except requests.exceptions.RequestException as e:
        return {"status": "Error", "message": f"Status Error ({getattr(e.response, 'status_code', 'N/A')})"}, 503

# --- Flask Routes

@app.route('/')
def index():
    ollama_status, _ = check_ollama_status()
    
    return render_template('index.html', 
                           ollama_status=ollama_status['message'], 
                           models=VLM_MODELS)

@app.route('/health')
def health_check():
    status, code = check_ollama_status()
    return jsonify(status), code

@app.route('/generate', methods=['POST'])
def generate_response():
    data = request.json
    vlm_model_name = data.get('model') 
    image_base64 = data.get('image')
    target_language = data.get('language')
    
    translator_model = TRANSLATOR_MODEL 
    
    # --- Validation ---
    if not vlm_model_name or not target_language or not image_base64:
        return jsonify({"response": "Error: Model, language, and image selection are required."}), 400
    # ------------------
    
    # --------------------------------------------------------------------------------------
    # --- STEP 1: Generate English Description (Conditional Prompt) --------------------------
    # --------------------------------------------------------------------------------------
    
    if target_language == 'Amharic':
        # Use a simple, short prompt to reduce complexity for Amharic translation
        vlm_prompt = "Describe the image in a single, short sentence in English."
    else:
        # Use a detailed prompt for all other languages (like Chinese and English)
        vlm_prompt = (
            "Provide a highly detailed and exhaustive description of the image. "
            "List all visible objects, their actions, their spatial relationship, and the overall context "
            "of the scene in English."
        )
    
    vlm_payload = {
        "model": vlm_model_name,
        "prompt": vlm_prompt, 
        "images": [image_base64],
        "stream": False 
    }

    try:
        vlm_response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json=vlm_payload,
            timeout=180 
        )
        vlm_response.raise_for_status()
        
        english_description = vlm_response.json().get("response")
        if not english_description:
            return jsonify({"response": f"Error: Failed to get English description from {vlm_model_name}. Check Ollama logs."}), 500

    except requests.exceptions.RequestException as e:
        app.logger.error(f"VLM Request Failed: {e}")
        return jsonify({"response": f"VLM Error ({vlm_model_name}): Could not connect or request timed out. Details: {e}"}), 500
    
    # If the target language is already English, we skip the translation step
    if target_language.lower() == 'english':
        return jsonify({"response": english_description}), 200
        
    # --------------------------------------------------------------------------------------
    # --- STEP 2: Translate Description (Qwen2:7b - Fixed Model) --------------------------
    # --------------------------------------------------------------------------------------
    
    translator_model = TRANSLATOR_MODEL 
    
    translation_prompt = (
        f"Translate the following English description into the {target_language} language. "
        f"Provide ONLY the translated text, nothing else. "
        f"Description:\n\n'{english_description}'"
    )

    translation_payload = {
        "model": translator_model,
        "prompt": translation_prompt, 
        "stream": False 
    }

    try:
        translation_response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json=translation_payload,
            timeout=60
        )
        translation_response.raise_for_status()
        
        translated_text = translation_response.json().get("response", "Translation Failed.")
        
        translated_text = translated_text.strip()
        
        if not translated_text and target_language == 'Amharic':
             return jsonify({"response": f"Translation failed for {target_language}. The LLM produced no text. This usually indicates an issue with script generation."}), 500

        return jsonify({"response": translated_text}), 200

    except requests.exceptions.RequestException as e:
        app.logger.error(f"Translation Request Failed: {e}")
        return jsonify({"response": f"Translation Error ({translator_model}): Could not translate to {target_language}. Details: {e}"}), 500

# --- NEW FUNCTION: Open Project Folder ---
def open_folder():
    """Opens the current project directory in the OS file explorer."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Platform-specific command to open the folder
    if os.name == 'nt':  # Windows
        subprocess.Popen(['explorer', current_dir])
    elif os.uname().sysname == 'Darwin':  # macOS
        subprocess.Popen(['open', current_dir])
    else:  # Linux/Other POSIX
        subprocess.Popen(['xdg-open', current_dir])
# --- END NEW FUNCTION ---

# --- NEW FUNCTION: Open Browser ---
def open_browser():
      """Opens the browser automatically."""
      webbrowser.open_new("http://127.0.0.1:5000/")
# --- END NEW FUNCTION ---
if __name__ == '__main__':
    # Ensures auto-open only happens once
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        Timer(2, open_browser).start()  # <-- DEFAULT: Opens the browser

        # -------------------------------------------------------------------
        # OPTIONAL: Uncomment the line below and COMMENT OUT the line above 
        #           if you want to automatically open the project folder
        #           instead of the browser.
        # -------------------------------------------------------------------
        # Timer(2, open_folder).start() 
        
    app.run(debug=True, use_reloader=False)
