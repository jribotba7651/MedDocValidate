import streamlit as st

st.set_page_config(page_title="MedDoc Test", page_icon="🏥")

st.title("🏥 MedDoc Validate - Test Page")

# Test 1: Check if Streamlit works
st.success("✓ Streamlit is working!")

# Test 2: Check for API key
try:
    if hasattr(st, 'secrets') and 'ANTHROPIC_API_KEY' in st.secrets:
        api_key = st.secrets['ANTHROPIC_API_KEY']
        st.success(f"✓ API Key found: {api_key[:10]}...{api_key[-4:]}")
    else:
        st.warning("⚠️ No API key in Streamlit secrets")
        st.info("👉 Go to Settings → Secrets and add: ANTHROPIC_API_KEY = 'your_key'")
except Exception as e:
    st.error(f"❌ Error checking secrets: {str(e)}")

# Test 3: Check imports
try:
    import pdfplumber
    st.success("✓ pdfplumber imported")
except ImportError as e:
    st.error(f"❌ pdfplumber import failed: {e}")

try:
    from anthropic import Anthropic
    st.success("✓ anthropic imported")
except ImportError as e:
    st.error(f"❌ anthropic import failed: {e}")

st.markdown("---")
st.info("If all tests pass, the full app should work. Replace this file with the full app.py")