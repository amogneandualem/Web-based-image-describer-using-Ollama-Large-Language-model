import streamlit as st
import requests
import base64
import io

st.set_page_config(
    page_title="LLM Image Describer",
    page_icon="🖼️",
    layout="wide"
)

# --- CONFIGURATION ---
# Set this in Streamlit Cloud Secrets
OLLAMA_HOST = st.secrets.get("OLLAMA_HOST", "http://localhost:11434")

VLM_MODELS = {
    "moondream:1.8b": "Fast Captioning (VLM)",
    "llava:latest": "Detailed Object Analysis (VLM)",
}
TRANSLATOR_MODEL = "qwen2:7b"

# --- HELPER FUNCTIONS ---
def check_ollama_status():
    """Check if Ollama server is reachable"""
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=10)
        if response.status_code == 200:
            installed_models = {model['name'] for model in response.json().get('models', [])}
            required_models = set(VLM_MODELS.keys()) | {TRANSLATOR_MODEL}
            missing_models = required_models - installed_models
            
            if missing_models:
                return {
                    "status": "warning",
                    "message": f"⚠️ Missing: {', '.join(missing_models)}"
                }
            return {"status": "success", "message": "✅ Connected"}
        return {"status": "error", "message": f"❌ Server error"}
    except Exception as e:
        return {"status": "error", "message": f"❌ Cannot connect: {str(e)}"}

def process_uploaded_file(uploaded_file):
    """Process uploaded file without Pillow"""
    # Read file bytes and convert to base64
    file_bytes = uploaded_file.getvalue()
    return base64.b64encode(file_bytes).decode('utf-8')

# --- MAIN APP ---
st.title("🖼️ LLM Image Describer")
st.markdown("Upload an image to get AI-generated descriptions in multiple languages.")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Status check
    if st.button("Test Ollama Connection"):
        status = check_ollama_status()
        if status["status"] == "success":
            st.success(status["message"])
        elif status["status"] == "warning":
            st.warning(status["message"])
        else:
            st.error(status["message"])
    
    selected_model = st.selectbox(
        "Select VLM Model",
        options=list(VLM_MODELS.keys()),
        format_func=lambda x: f"{x} ({VLM_MODELS[x]})"
    )
    
    target_language = st.selectbox(
        "Target Language",
        ["English", "Chinese", "Amharic", "French", "Spanish"]
    )
    
    st.info("💡 Requires running Ollama server with models: llava, moondream, qwen2:7b")

# Main content
st.header("📷 Image Input")

uploaded_file = st.file_uploader(
    "Choose an image file",
    type=['jpg', 'jpeg', 'png'],
    help="Upload an image file (JPG, JPEG, PNG)"
)

if uploaded_file is not None:
    # Show file info
    st.write(f"**File:** {uploaded_file.name}")
    st.write(f"**Size:** {len(uploaded_file.getvalue()) / 1024:.1f} KB")
    
    # Display image using Streamlit's built-in method
    st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
    
    if st.button("🚀 Generate Description", type="primary"):
        with st.spinner("Processing image..."):
            try:
                # Convert to base64
                image_base64 = process_uploaded_file(uploaded_file)
                
                # Step 1: Generate English description
                with st.spinner("Step 1/2: Analyzing with VLM..."):
                    vlm_prompt = (
                        "Describe the image in a single, short sentence in English."
                        if target_language == 'Amharic'
                        else "Provide a detailed description of the image in English."
                    )
                    
                    vlm_payload = {
                        "model": selected_model,
                        "prompt": vlm_prompt,
                        "images": [image_base64],
                        "stream": False
                    }
                    
                    vlm_response = requests.post(
                        f"{OLLAMA_HOST}/api/generate",
                        json=vlm_payload,
                        timeout=120
                    )
                    vlm_response.raise_for_status()
                    english_description = vlm_response.json().get("response", "")
                
                # Step 2: Translate if needed
                if target_language.lower() == 'english':
                    final_text = english_description
                else:
                    with st.spinner(f"Step 2/2: Translating to {target_language}..."):
                        trans_prompt = f"Translate to {target_language}:\n\n{english_description}"
                        trans_payload = {
                            "model": TRANSLATOR_MODEL,
                            "prompt": trans_prompt,
                            "stream": False
                        }
                        
                        trans_response = requests.post(
                            f"{OLLAMA_HOST}/api/generate",
                            json=trans_payload,
                            timeout=60
                        )
                        trans_response.raise_for_status()
                        final_text = trans_response.json().get("response", "").strip()
                
                # Display results
                st.success("✅ Analysis Complete!")
                st.text_area("Description", final_text, height=200)
                
                # Download button
                st.download_button(
                    label="📥 Download Result",
                    data=final_text,
                    file_name=f"description_{target_language}.txt",
                    mime="text/plain"
                )
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("Make sure Ollama server is running and accessible.")
else:
    st.info("👈 Please upload an image to begin.")

# Footer
st.divider()
st.caption(f"Ollama Server: `{OLLAMA_HOST}` | Target language: {target_language}")
