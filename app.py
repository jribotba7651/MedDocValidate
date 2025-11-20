import streamlit as st
import pdfplumber
from anthropic import Anthropic
import os
from datetime import datetime

# 🔑 API Key Configuration - Supports both local .env and Streamlit Cloud secrets
def get_api_key():
    """Get API key from either Streamlit secrets or environment variable"""
    try:
        # Try Streamlit secrets first (for cloud deployment)
        if hasattr(st, 'secrets') and 'ANTHROPIC_API_KEY' in st.secrets:
            return st.secrets['ANTHROPIC_API_KEY']
    except:
        pass
    
    # Fall back to environment variable (for local development)
    api_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not api_key:
        st.error("⚠️ No API key found. Please configure ANTHROPIC_API_KEY in Streamlit secrets or .env file")
        st.stop()
    
    return api_key

# Page config
st.set_page_config(
    page_title="MedDoc Validate - FDA Compliance Checker",
    page_icon="🏥",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        background-color: #1f77b4;
        color: white;
        padding: 0.5rem 2rem;
        font-size: 1.1rem;
        border-radius: 5px;
        border: none;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #145a8d;
    }
    .compliance-header {
        background: linear-gradient(90deg, #1f77b4 0%, #2ca02c 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin: 1rem 0;
    }
    .gap-item {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #ffc107;
        margin: 0.5rem 0;
    }
    .recommendation-item {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #28a745;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
    <div class="compliance-header">
        <h1>🏥 MedDoc Validate</h1>
        <p>FDA 21 CFR Part 820 Compliance Document Validator</p>
    </div>
""", unsafe_allow_html=True)

# Initialize session state
if 'validation_results' not in st.session_state:
    st.session_state.validation_results = None

# Main content
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📄 Upload Document")
    st.write("Upload your medical device compliance document (SOP, DHR, Quality Manual)")
    
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=['pdf'],
        help="Maximum file size: 10MB"
    )
    
    if uploaded_file:
        st.success(f"✓ File uploaded: {uploaded_file.name}")
        
        # Extract text preview
        with pdfplumber.open(uploaded_file) as pdf:
            total_pages = len(pdf.pages)
            st.info(f"📊 Document has {total_pages} page(s)")
            
            # Show first page preview
            first_page_text = pdf.pages[0].extract_text()[:500]
            with st.expander("Preview first page"):
                st.text(first_page_text + "...")

with col2:
    st.subheader("⚙️ Validation Settings")
    
    regulation = st.selectbox(
        "Select Regulation",
        ["21 CFR Part 820.70 - Production and Process Controls",
         "21 CFR Part 820.75 - Process Validation",
         "21 CFR Part 820.80 - Receiving, In-Process, and Finished Device Acceptance"]
    )
    
    detail_level = st.select_slider(
        "Detail Level",
        options=["Basic", "Standard", "Comprehensive"],
        value="Standard"
    )

# Validation button
if uploaded_file:
    if st.button("🔍 Validate Compliance", use_container_width=True):
        with st.spinner("Analyzing document against FDA regulations..."):
            try:
                # Get API key
                api_key = get_api_key()
                
                # Extract full text from PDF
                full_text = ""
                with pdfplumber.open(uploaded_file) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            full_text += text + "\n"
                
                # Truncate if too long (Claude has token limits)
                max_chars = 50000
                if len(full_text) > max_chars:
                    full_text = full_text[:max_chars]
                    st.warning(f"⚠️ Document truncated to {max_chars} characters for analysis")
                
                # Initialize Anthropic client
                client = Anthropic(api_key=api_key)
                
                # Prepare prompt based on regulation and detail level
                prompt = f"""You are an FDA regulatory compliance expert. Analyze the following medical device document against {regulation}.

Document Content:
{full_text}

Provide a {detail_level.lower()} analysis with:

1. COMPLIANCE SCORE (0-100%)
2. GAPS FOUND: List specific gaps with exact CFR citations (e.g., 21 CFR 820.70(a))
3. RECOMMENDATIONS: Specific, actionable recommendations to address each gap
4. SUMMARY: Overall compliance status

Format your response clearly with these sections."""

                # Call Claude API
                message = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4000,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                
                # Extract response
                validation_result = message.content[0].text
                
                # Store in session state
                st.session_state.validation_results = {
                    'result': validation_result,
                    'file_name': uploaded_file.name,
                    'regulation': regulation,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                st.success("✓ Validation complete!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error during validation: {str(e)}")
                st.info("💡 Make sure your ANTHROPIC_API_KEY is configured correctly")

# Display results
if st.session_state.validation_results:
    st.markdown("---")
    st.header("📊 Validation Results")
    
    results = st.session_state.validation_results
    
    # Metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Document", results['file_name'])
    with col2:
        st.metric("Regulation", results['regulation'].split('-')[0].strip())
    with col3:
        st.metric("Analyzed", results['timestamp'])
    
    # Results
    st.markdown("### Detailed Analysis")
    st.markdown(f"""
    <div class="metric-card">
        {results['result']}
    </div>
    """, unsafe_allow_html=True)
    
    # Download report
    st.download_button(
        label="📥 Download Report",
        data=f"""
FDA COMPLIANCE VALIDATION REPORT
================================

Document: {results['file_name']}
Regulation: {results['regulation']}
Generated: {results['timestamp']}

{results['result']}

---
Generated by MedDoc Validate
        """,
        file_name=f"compliance_report_{results['file_name']}.txt",
        mime="text/plain"
    )
    
    if st.button("🔄 Analyze Another Document"):
        st.session_state.validation_results = None
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p><strong>MedDoc Validate</strong> - Medical Device Compliance Document Validator</p>
        <p>⚠️ This tool provides preliminary analysis. Always consult with regulatory experts for final compliance determination.</p>
    </div>
""", unsafe_allow_html=True)
