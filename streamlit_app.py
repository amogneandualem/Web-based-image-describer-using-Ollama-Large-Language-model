import streamlit as st
import requests
import base64
import time

# ========== CONFIGURATION ==========
OLLAMA_HOST = st.secrets.get("OLLAMA_HOST", "http://localhost:11434")

VLM_MODELS = {
    "moondream:1.8b": "Fast & Lightweight",
    "llava:latest": "Detailed & Accurate",
}
TRANSLATOR_MODEL = "qwen2:7b"

# ========== PAGE SETUP ==========
st.set_page_config(
    page_title="AI Image Describer",
    page_icon="🖼️",
    layout="wide"
)

# ========== CUSTOM STYLING ==========
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1E40AF;
        padding-bottom: 20px;
        border-bottom: 2px solid #E5E7EB;
    }
    .success-box {
        padding: 15px;
        background: #D1FAE5;
        border-radius: 10px;
        border-left: 5px solid #10B981;
        margin: 10px 0;
    }
    .error-box {
        padding: 15px;
        background: #FEE2E2;
        border-radius: 10px;
        border-left: 5px solid #EF4444;
        margin: 10px 0;
    }
    .info-box {
        padding: 15px;
        background: #DBEAFE;
        border-radius: 10px;
        border-left: 5px solid #3B82F6;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ========== HELPER FUNCTIONS ==========
def test_ollama_connection():
    """Test if Ollama server is accessible"""
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=10)
        if response.status_code == 200:
            models = [m['name'] for m in response.json().get('models', [])]
            required = list(VLM_MODELS.keys()) + [TRANSLATOR_MODEL]
            missing = [m for m in required if m not in models]
            
            if missing:
                return False, f"⚠️ Missing: {', '.join(missing)}"
            return True, f"✅ Connected ({len(models)} models found)"
        return False, f"❌ Server error: {response.status_code}"
    except Exception as e:
        return False, f"❌ Connection failed: {str(e)}"

def generate_description(model, image_base64, language):
    """Generate description using Ollama"""
    try:
        # Step 1: Generate English description
        if language == 'Amharic':
            prompt = "Describe this image in one short English sentence."
        else:
            prompt = "Describe this image in detail in English."
        
        # Call Ollama for VLM
        vlm_response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "images": [image_base64],
                "stream": False
            },
            timeout=120
        )
        
        if vlm_response.status_code != 200:
            return None, f"VLM error: {vlm_response.status_code}"
        
        english_desc = vlm_response.json().get('response', '').strip()
        
        # Step 2: Translate if needed
        if language.lower() == 'english':
            return english_desc, None
        
        # Translate
        trans_response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": TRANSLATOR_MODEL,
                "prompt": f"Translate to {language}:\n\n{english_desc}",
                "stream": False
            },
            timeout=60
        )
        
        if trans_response.status_code != 200:
            return english_desc, f"Translation failed. English: {english_desc}"
        
        translated = trans_response.json().get('response', '').strip()
        return translated, english_desc
        
    except Exception as e:
        return None, f"Error: {str(e)}"

# ========== MAIN APP ==========
st.markdown('<h1 class="main-header">🖼️ AI Image Description Generator</h1>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Connection status
    st.markdown("### 🔗 Ollama Connection")
    if st.button("Test Connection", use_container_width=True):
        with st.spinner("Testing..."):
            success, msg = test_ollama_connection()
            if success:
                st.success(msg)
            else:
                st.error(msg)
    
    st.divider()
    
    # Model selection
    st.markdown("### 🤖 Select Model")
    selected_model = st.selectbox(
        "Vision Model",
        options=list(VLM_MODELS.keys()),
        label_visibility="collapsed"
    )
    st.caption(VLM_MODELS[selected_model])
    
    # Language selection
    st.markdown("### 🌍 Select Language")
    target_language = st.selectbox(
        "Output Language",
        ["English", "Chinese", "Amharic", "French", "Spanish"],
        label_visibility="collapsed"
    )
    
    st.divider()
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown("**Requirements:**")
    st.markdown("1. Ollama server running")
    st.markdown("2. Models: `llava`, `moondream`, `qwen2:7b`")
    st.markdown('</div>', unsafe_allow_html=True)

# Main content
tab1, tab2 = st.tabs(["📷 Upload Image", "📖 Instructions"])

with tab1:
    # File upload
    uploaded_file = st.file_uploader(
        "Choose an image (JPG, PNG)",
        type=['jpg', 'jpeg', 'png'],
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        # Display image
        st.image(uploaded_file, use_column_width=True)
        
        # Convert to base64
        image_base64 = base64.b64encode(uploaded_file.getvalue()).decode()
        
        # Generate button
        if st.button("🚀 Generate Description", type="primary", use_container_width=True):
            with st.spinner(f"Processing with {selected_model}..."):
                result, error_or_english = generate_description(
                    selected_model,
                    image_base64,
                    target_language
                )
                
                if result:
                    st.markdown("### ✅ Description Generated")
                    st.markdown('<div class="success-box">', unsafe_allow_html=True)
                    st.write(result)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Download button
                    st.download_button(
                        "📥 Download Result",
                        data=result,
                        file_name=f"description_{target_language}.txt"
                    )
                    
                    # Show English original if translated
                    if target_language.lower() != 'english' and error_or_english:
                        with st.expander("View Original English"):
                            st.write(error_or_english)
                else:
                    st.markdown('<div class="error-box">', unsafe_allow_html=True)
                    st.error(f"Failed: {error_or_english}")
                    st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("👈 Please upload an image to begin")

with tab2:
    st.header("📚 Complete Setup Guide")
    
    st.markdown("### Step 1: Install Ollama & Models")
    st.code("""
# Install Ollama from https://ollama.com
# Then run these commands:

# Pull required models
ollama pull llava:latest
ollama pull moondream:1.8b
ollama pull qwen2:7b

# Start Ollama server
ollama serve
""")
    
    st.markdown("### Step 2: Make Ollama Public with Ngrok")
    st.code("""
# Download ngrok from https://ngrok.com
# Sign up for free account
# Get your authtoken

# Start ngrok tunnel
ngrok http 11434

# Copy the URL shown (like https://abc123.ngrok.io)
""")
    
    st.markdown("### Step 3: Configure Streamlit Secrets")
    st.code("""
1. Go to: https://share.streamlit.io
2. Find your app: ufr2baqg57qg5jmzskupz6
3. Click "⋮" → "Settings" → "Secrets"
4. Add this (replace with your ngrok URL):

OLLAMA_HOST = "https://your-ngrok-url.ngrok.io"

5. Click "Save"
""")
    
    st.markdown("### Step 4: Test Your App")
    st.code("""
1. Visit: https://ufr2baqg57qg5jmzskupz6.streamlit.app
2. Upload any image
3. Click "Generate Description"
""")

# Footer
st.divider()
st.caption(f"Ollama Server: `{OLLAMA_HOST}` | Model: `{selected_model}` | Language: `{target_language}`")
st.caption("💡 **Note**: Keep your Ollama server running while using this app")
