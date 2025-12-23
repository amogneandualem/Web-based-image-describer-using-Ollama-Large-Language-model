import streamlit as st
import requests
import base64
import time

# ================= CONFIGURATION =================
# Get Ollama URL from Streamlit Secrets or use default
OLLAMA_HOST = st.secrets.get("OLLAMA_HOST", "http://localhost:11434")

VLM_MODELS = {
    "moondream:1.8b": "Fast Captioning",
    "llava:latest": "Detailed Analysis",
}
TRANSLATOR_MODEL = "qwen2:7b"

# ================= PAGE SETUP =================
st.set_page_config(
    page_title="LLM Image Describer",
    page_icon="🖼️",
    layout="wide"
)

# ================= HELPER FUNCTIONS =================
def test_ollama_connection(host_url):
    """Test connection to Ollama server"""
    try:
        response = requests.get(f"{host_url}/api/tags", timeout=10)
        if response.status_code == 200:
            installed_models = {model['name'] for model in response.json().get('models', [])}
            required = set(VLM_MODELS.keys()) | {TRANSLATOR_MODEL}
            missing = required - installed_models
            
            if missing:
                return False, f"⚠️ Missing models: {', '.join(missing)}"
            return True, "✅ Connected with all models"
        return False, f"❌ Server error: {response.status_code}"
    except Exception as e:
        return False, f"❌ Connection failed: {str(e)}"

def process_image_file(uploaded_file):
    """Convert uploaded file to base64"""
    file_bytes = uploaded_file.getvalue()
    return base64.b64encode(file_bytes).decode('utf-8')

def generate_description(model, image_base64, language, host_url):
    """Generate description using Ollama"""
    # Step 1: Create English prompt
    if language == 'Amharic':
        prompt = "Describe the image in a single, short sentence in English."
    else:
        prompt = "Provide a detailed description of this image in English."
    
    # Step 1: Get English description
    payload = {
        "model": model,
        "prompt": prompt,
        "images": [image_base64],
        "stream": False
    }
    
    try:
        response = requests.post(
            f"{host_url}/api/generate",
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        english_desc = response.json().get("response", "")
        
        # Step 2: Translate if needed
        if language.lower() == 'english':
            return english_desc, ""
        
        trans_prompt = f"Translate this to {language}:\n\n{english_desc}"
        trans_payload = {
            "model": TRANSLATOR_MODEL,
            "prompt": trans_prompt,
            "stream": False
        }
        
        trans_response = requests.post(
            f"{host_url}/api/generate",
            json=trans_payload,
            timeout=60
        )
        trans_response.raise_for_status()
        
        translated = trans_response.json().get("response", "").strip()
        return translated, english_desc
        
    except Exception as e:
        raise Exception(f"Ollama error: {str(e)}")

# ================= MAIN APP UI =================
st.title("🖼️ LLM Image Describer")
st.markdown("Upload an image to get AI-generated descriptions in multiple languages.")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Connection status
    st.subheader("🔗 Ollama Connection")
    
    # Let user input Ollama URL (overrides secrets)
    custom_host = st.text_input(
        "Ollama Server URL",
        value=OLLAMA_HOST,
        help="Enter your Ollama server URL (e.g., https://your-ngrok.ngrok.io)"
    )
    
    # Test connection button
    if st.button("Test Connection", type="secondary"):
        with st.spinner("Testing..."):
            success, message = test_ollama_connection(custom_host)
            if success:
                st.success(message)
            else:
                st.error(message)
                st.info("Make sure Ollama is running and accessible at the URL above.")
    
    st.divider()
    
    # Model selection
    selected_model = st.selectbox(
        "Vision Model",
        options=list(VLM_MODELS.keys()),
        format_func=lambda x: f"{x} - {VLM_MODELS[x]}"
    )
    
    # Language selection
    target_language = st.selectbox(
        "Output Language",
        ["English", "Chinese", "Amharic", "French", "Spanish", "German"]
    )
    
    st.divider()
    st.info("💡 **Requirements:**\n- Ollama server running\n- Models: llava, moondream, qwen2:7b")

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📷 Upload Image")
    
    uploaded_file = st.file_uploader(
        "Choose an image file",
        type=['jpg', 'jpeg', 'png'],
        help="Supported formats: JPG, JPEG, PNG",
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        # Display the image
        st.image(uploaded_file, caption="Your Image", use_column_width=True)
        
        # Show file info
        file_size = len(uploaded_file.getvalue()) / 1024
        st.caption(f"File: {uploaded_file.name} | Size: {file_size:.1f} KB")
        
        # Process button
        if st.button("🚀 Generate Description", type="primary", use_container_width=True):
            with st.spinner("Processing..."):
                try:
                    # Convert image
                    image_base64 = process_image_file(uploaded_file)
                    
                    # Generate description
                    with st.spinner("Analyzing with AI..."):
                        result, english_original = generate_description(
                            selected_model, 
                            image_base64, 
                            target_language,
                            custom_host
                        )
                    
                    # Display results
                    st.success("✅ Analysis Complete!")
                    
                    # Main result
                    st.text_area("Description", result, height=200, label_visibility="collapsed")
                    
                    # Download button
                    st.download_button(
                        label="📥 Download Result",
                        data=result,
                        file_name=f"image_description_{target_language}.txt",
                        mime="text/plain"
                    )
                    
                    # Show original if translated
                    if target_language.lower() != 'english' and english_original:
                        with st.expander("View Original English"):
                            st.write(english_original)
                            
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.info("""
                    **Troubleshooting:**
                    1. Check Ollama server is running
                    2. Verify URL is correct
                    3. Test connection in sidebar
                    """)
    else:
        st.info("👈 Please upload an image to begin")

with col2:
    st.subheader("📝 How to Use")
    
    st.markdown("""
    ### Setup Instructions:
    
    1. **Start Ollama on your computer:**
    ```bash
    ollama serve
    ```
    
    2. **Install and run ngrok (for public access):**
    ```bash
    ngrok http 11434
    ```
    
    3. **Copy the ngrok URL (e.g., `https://abc123.ngrok.io`)**
    
    4. **Paste the URL in the sidebar → "Ollama Server URL"**
    
    5. **Click "Test Connection" to verify**
    
    6. **Upload an image and click "Generate Description"**
    
    ### Required Models:
    Run these commands in your terminal:
    ```bash
    ollama pull llava:latest
    ollama pull moondream:1.8b
    ollama pull qwen2:7b
    ```
    """)

# Footer
st.divider()
st.caption(f"Connected to: `{custom_host}` | Using model: {selected_model} | Language: {target_language}")
