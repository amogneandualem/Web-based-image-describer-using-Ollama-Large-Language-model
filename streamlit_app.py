import streamlit as st
import requests
import base64
import io

st.set_page_config(
    page_title="LLM Image Describer",
    page_icon="🖼️",
    layout="wide"
)

# Initialize session state for OLLAMA_HOST if not present
if 'ollama_host' not in st.session_state:
    # First, try to get from secrets, otherwise use default (localhost for local, but for Streamlit Cloud we need to set it)
    st.session_state.ollama_host = st.secrets.get("OLLAMA_HOST", "http://localhost:11434")

# --- Sidebar for Configuration ---
with st.sidebar:
    st.header("⚙️ Ollama Configuration")
    
    # Let the user override the host in the session
    ollama_host_input = st.text_input(
        "Ollama Server URL",
        value=st.session_state.ollama_host,
        help="URL of your Ollama server (e.g., http://localhost:11434 or https://your-ngrok-url.ngrok.io)"
    )
    
    # Update session state if the input changes
    if ollama_host_input != st.session_state.ollama_host:
        st.session_state.ollama_host = ollama_host_input
        st.rerun()
    
    # Test connection button
    if st.button("Test Connection"):
        try:
            response = requests.get(f"{st.session_state.ollama_host}/api/tags", timeout=10)
            if response.status_code == 200:
                st.success("✅ Connected to Ollama server!")
            else:
                st.error(f"❌ Server error: {response.status_code}")
        except Exception as e:
            st.error(f"❌ Cannot connect to Ollama server: {e}")
    
    st.divider()
    
    # Model selection
    VLM_MODELS = {
        "moondream:1.8b": "Fast Captioning (VLM)",
        "llava:latest": "Detailed Object Analysis (VLM)",
    }
    TRANSLATOR_MODEL = "qwen2:7b"
    
    selected_model = st.selectbox(
        "Select VLM Model",
        options=list(VLM_MODELS.keys()),
        format_func=lambda x: f"{x} ({VLM_MODELS[x]})",
        help="Choose which Vision Language Model to use for analysis"
    )
    
    # Language selection
    target_language = st.selectbox(
        "Target Language",
        ["English", "Chinese", "Amharic", "French", "Spanish", "German", "Japanese"],
        index=0
    )
    
    st.divider()
    st.info("💡 **Note**: Make sure your Ollama server has the required models: llava, moondream, qwen2:7b")

# Main app
st.title("🖼️ Web-based LLM Image Describer")
st.markdown("Upload an image or use your camera to get AI-generated descriptions in multiple languages.")

# --- Helper Functions ---
def check_ollama_status():
    """Check if Ollama server is reachable and has required models"""
    try:
        response = requests.get(f"{st.session_state.ollama_host}/api/tags", timeout=10)
        if response.status_code == 200:
            installed_models = {model['name'] for model in response.json().get('models', [])}
            required_models = set(VLM_MODELS.keys()) | {TRANSLATOR_MODEL}
            missing_models = required_models - installed_models
            
            if missing_models:
                return {
                    "status": "warning",
                    "message": f"⚠️ Missing models: {', '.join(missing_models)}",
                    "missing": missing_models
                }
            return {
                "status": "success", 
                "message": "✅ Ollama Connected with all models",
                "missing": set()
            }
        else:
            return {
                "status": "error",
                "message": f"❌ Server error: {response.status_code}",
                "missing": set()
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"❌ Cannot connect to Ollama: {str(e)}",
            "missing": set()
        }

def generate_vlm_description(model, image_base64, target_language):
    """Generate English description using VLM"""
    if target_language == 'Amharic':
        vlm_prompt = "Describe the image in a single, short sentence in English."
    else:
        vlm_prompt = (
            "Provide a highly detailed and exhaustive description of the image. "
            "List all visible objects, their actions, their spatial relationship, and the overall context "
            "of the scene in English."
        )
    
    payload = {
        "model": model,
        "prompt": vlm_prompt,
        "images": [image_base64],
        "stream": False
    }
    
    try:
        response = requests.post(
            f"{st.session_state.ollama_host}/api/generate",
            json=payload,
            timeout=180
        )
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as e:
        raise Exception(f"VLM Error: {str(e)}")

def translate_description(text, target_language):
    """Translate text to target language"""
    translation_prompt = (
        f"Translate the following English description into the {target_language} language. "
        f"Provide ONLY the translated text, nothing else. "
        f"Description:\n\n'{text}'"
    )
    
    payload = {
        "model": TRANSLATOR_MODEL,
        "prompt": translation_prompt,
        "stream": False
    }
    
    try:
        response = requests.post(
            f"{st.session_state.ollama_host}/api/generate",
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except Exception as e:
        raise Exception(f"Translation Error: {str(e)}")

# --- Main Content Area ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📷 Image Input")
    
    # Image source selection
    input_method = st.radio(
        "Choose input method:",
        ["Upload Image", "Use Camera"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    image_data = None
    preview_image = None
    
    if input_method == "Upload Image":
        uploaded_file = st.file_uploader(
            "Choose an image file",
            type=['jpg', 'jpeg', 'png', 'bmp'],
            label_visibility="collapsed"
        )
        if uploaded_file is not None:
            # Read the file and convert to base64
            file_bytes = uploaded_file.getvalue()
            image_data = base64.b64encode(file_bytes).decode('utf-8')
            preview_image = file_bytes
            
            # Display the image
            st.image(preview_image, caption="Uploaded Image", use_column_width=True)
    
    else:  # Camera input
        camera_image = st.camera_input("Take a picture", label_visibility="collapsed")
        if camera_image is not None:
            # Convert to base64
            file_bytes = camera_image.getvalue()
            image_data = base64.b64encode(file_bytes).decode('utf-8')
            preview_image = file_bytes

with col2:
    st.subheader("📝 Analysis Results")
    
    if preview_image:
        st.image(preview_image, caption="Image to analyze", use_column_width=True)
    
    # Response area
    response_placeholder = st.empty()
    
    if image_data and st.button("🚀 Generate Description", type="primary", use_container_width=True):
        # First, check Ollama connection
        status = check_ollama_status()
        if status["status"] == "error":
            st.error("Cannot connect to Ollama server. Please check the connection and try again.")
            st.stop()
        
        # Initialize progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: Get English description
            status_text.text("Step 1/2: Analyzing image with VLM...")
            progress_bar.progress(30)
            
            english_description = generate_vlm_description(
                selected_model, 
                image_data, 
                target_language
            )
            
            if not english_description:
                st.error("Failed to generate description. The model returned empty response.")
                st.stop()
            
            # Step 2: Translate if needed
            if target_language.lower() == 'english':
                final_text = english_description
                progress_bar.progress(100)
                status_text.text("Analysis complete!")
            else:
                status_text.text(f"Step 2/2: Translating to {target_language}...")
                progress_bar.progress(70)
                
                translated_text = translate_description(english_description, target_language)
                final_text = translated_text
                
                progress_bar.progress(100)
                status_text.text("Translation complete!")
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            # Display results
            with response_placeholder.container():
                st.success("✅ Analysis Complete!")
                
                # Main result
                st.text_area("Description", final_text, height=200, label_visibility="collapsed")
                
                # Download button
                st.download_button(
                    label="📥 Download Result",
                    data=final_text,
                    file_name=f"image_description_{target_language}.txt",
                    mime="text/plain"
                )
                
                # Show English original if translation was done
                if target_language.lower() != 'english':
                    with st.expander("View Original English Description"):
                        st.write(english_description)
        
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"❌ Error: {str(e)}")
            st.info("Make sure your Ollama server is running and accessible.")
    
    elif not image_data:
        st.info("👈 Please upload an image or take a photo first.")
        with response_placeholder.container():
            st.markdown("""
            ### How to use:
            1. **Select input method** (Upload or Camera)
            2. **Choose your target language**
            3. **Select a VLM model** from the sidebar
            4. **Click 'Generate Description'**
            
            ### Requirements:
            - Ollama server must be running and accessible
            - Required models: `llava:latest`, `moondream:1.8b`, `qwen2:7b`
            """)

# Footer
st.divider()
st.caption(f"Ollama Server: `{st.session_state.ollama_host}` | Models: {', '.join(VLM_MODELS.keys())} | Translator: {TRANSLATOR_MODEL}")
