import streamlit as st
import pdfplumber
import os
import json
from datetime import datetime
from validator import FDAComplianceValidator, SEVERITY_LEVELS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
        st.error("⚠️ No API key found.")
        st.stop()

    return api_key

# Page config
st.set_page_config(
    page_title="Compliance Check - FDA Compliance Checker",
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
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
        color: #000000;
        line-height: 1.6;
    }
    .recommendation-item strong {
        color: #2c3e50;
        font-size: 1.05rem;
    }
    .recommendation-item p {
        color: #2c3e50;
        margin: 0.5rem 0;
    }
    .finding-critical {
        background-color: #fee;
        padding: 2rem;
        border-radius: 8px;
        border: 2px solid #dc3545;
        margin: 1.5rem 0;
        line-height: 1.8;
    }
    .finding-major {
        background-color: #fff3cd;
        padding: 2rem;
        border-radius: 8px;
        border: 2px solid #fd7e14;
        margin: 1.5rem 0;
        line-height: 1.8;
    }
    .finding-minor {
        background-color: #d1ecf1;
        padding: 2rem;
        border-radius: 8px;
        border: 2px solid #0dcaf0;
        margin: 1.5rem 0;
        line-height: 1.8;
    }
    .strength-item {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #28a745;
        margin: 0.5rem 0;
    }
    .severity-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
        font-size: 1rem;
    }
    .severity-critical {
        background-color: #dc3545;
        color: white;
    }
    .severity-major {
        background-color: #fd7e14;
        color: white;
    }
    .severity-minor {
        background-color: #0dcaf0;
        color: white;
    }
    .finding-section {
        margin: 1.5rem 0;
    }
    .finding-header {
        font-size: 1.3rem;
        font-weight: bold;
        margin-bottom: 1rem;
        color: #333;
    }
    .finding-content {
        margin-left: 1rem;
        margin-bottom: 1rem;
        font-size: 1rem;
    }
    .risk-box {
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
        font-weight: 500;
    }
    .risk-critical {
        background-color: #dc3545;
        color: white;
    }
    .risk-major {
        background-color: #fd7e14;
        color: white;
    }
    .risk-minor {
        background-color: #0dcaf0;
        color: white;
    }
    .action-box {
        background-color: #d4edda;
        padding: 1.2rem;
        border-radius: 5px;
        border-left: 4px solid #28a745;
        margin-top: 20px;
        margin-bottom: 1rem;
    }
    .requirement-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
    <div class="compliance-header">
        <h1>🏥 Compliance Check</h1>
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

                # Initialize validator
                validator = FDAComplianceValidator(api_key)

                # Run validation
                results = validator.validate_document(full_text, regulation, detail_level)

                # Format for display
                formatted_output = validator.format_results_for_display(results)

                # Store in session state
                st.session_state.validation_results = {
                    'structured_results': results,
                    'formatted_output': formatted_output,
                    'file_name': uploaded_file.name,
                    'regulation': regulation,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                st.success("✓ Validation complete!")
                st.rerun()

            except Exception as e:
                st.error(f"❌ Error during validation: {str(e)}")
                st.info("💡 Make sure your ANTHROPIC_API_KEY is configured correctly")
                import traceback
                st.code(traceback.format_exc())

# Display results
if st.session_state.validation_results:
    st.markdown("---")
    st.header("📊 Validation Results")

    results = st.session_state.validation_results
    structured = results.get('structured_results', {})

    # Metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Document", results['file_name'])
    with col2:
        st.metric("Regulation", results['regulation'].split('-')[0].strip())
    with col3:
        st.metric("Analyzed", results['timestamp'])

    # Overall Assessment
    if 'overall_assessment' in structured:
        assessment = structured['overall_assessment']
        st.markdown("### Overall Compliance Assessment")

        col1, col2, col3 = st.columns(3)
        with col1:
            score = assessment.get('compliance_score', 'N/A')
            st.metric("Compliance Score", f"{score}%", delta=None)
        with col2:
            risk = assessment.get('overall_risk_level', 'N/A')
            risk_color = "🔴" if risk == "HIGH" else "🟡" if risk == "MEDIUM" else "🟢"
            st.metric("Risk Level", f"{risk_color} {risk}")
        with col3:
            ready = assessment.get('ready_for_fda_inspection', False)
            ready_icon = "✅" if ready else "⚠️"
            st.metric("FDA Inspection Ready", f"{ready_icon} {'Yes' if ready else 'No'}")

        if 'executive_summary' in assessment:
            st.info(assessment['executive_summary'])

    # Inspection Readiness Summary
    if 'inspection_readiness' in structured:
        ir = structured['inspection_readiness']
        st.markdown("### Inspection Readiness Summary")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🔴 Critical Gaps", ir.get('critical_gaps_count', 0))
        with col2:
            st.metric("🟠 Major Gaps", ir.get('major_gaps_count', 0))
        with col3:
            st.metric("🟡 Minor Gaps", ir.get('minor_gaps_count', 0))
        with col4:
            st.metric("⏱️ Time to Compliance", ir.get('estimated_time_to_compliance', 'N/A'))

        if ir.get('inspection_risk_areas'):
            st.markdown("**High-Risk Areas for FDA Inspection:**")
            for area in ir['inspection_risk_areas']:
                st.markdown(f"- {area}")

    # Detailed Findings
    if 'findings' in structured and structured['findings']:
        st.markdown("### 🔍 Detailed Findings")
        st.write("")  # Add spacing

        for i, finding in enumerate(structured['findings'], 1):
            severity = finding.get('severity', 'MINOR')
            cfr = finding.get('cfr_citation', 'N/A')

            # Determine icon based on severity
            if severity == "CRITICAL":
                icon = "🔴"
            elif severity == "MAJOR":
                icon = "🟠"
            else:
                icon = "🟡"

            with st.expander(f"{icon} [{i}] {cfr} - {severity}", expanded=(severity == "CRITICAL")):
                # CFR Citation Header
                st.markdown(f"### {cfr}")
                st.write("")

                # Requirement
                st.markdown("**📋 Requirement**")
                st.info(finding.get('requirement_description', 'N/A'))

                # Finding
                st.markdown("**🔍 Finding**")
                st.write(finding.get('finding', 'N/A'))
                st.write("")

                # Risk - color-coded based on severity
                st.markdown("**⚠️ Risk to Compliance**")
                risk_text = finding.get('risk_to_compliance', 'N/A')
                if severity == "CRITICAL":
                    st.error(risk_text)
                elif severity == "MAJOR":
                    st.warning(risk_text)
                else:
                    st.info(risk_text)

                st.write("")

                # Recommendation
                st.markdown("**✅ Recommendation**")
                st.success(finding.get('recommendation', 'N/A'))

                # Optional fields
                if finding.get('evidence'):
                    st.write("")
                    st.markdown("**📄 Evidence**")
                    st.write(finding['evidence'])

                if finding.get('severity_justification'):
                    st.write("")
                    st.markdown("**⚖️ Severity Justification**")
                    st.write(finding['severity_justification'])

                if finding.get('regulatory_precedent'):
                    st.write("")
                    st.markdown("**📚 Regulatory Precedent**")
                    st.write(finding['regulatory_precedent'])

    # Strengths
    if 'strengths' in structured and structured['strengths']:
        st.markdown("### ✅ Compliance Strengths")
        st.write("")
        for strength in structured['strengths']:
            cfr = strength.get('cfr_citation', 'N/A')
            desc = strength.get('description', 'N/A')
            st.success(f"**{cfr}:** {desc}")

    # Priority Actions
    if 'priority_actions' in structured and structured['priority_actions']:
        st.markdown("### 📋 Priority Action Items")
        st.write("")

        for action in sorted(structured['priority_actions'], key=lambda x: x.get('priority', 999)):
            priority = action.get('priority', 'N/A')
            cfr_citation = action.get('cfr_citation', 'N/A')
            action_desc = action.get('action', 'N/A')
            effort = action.get('estimated_effort', 'N/A')
            impact = action.get('impact', 'N/A')

            # Display as a clean card using native Streamlit
            st.markdown(f"#### {priority}. {cfr_citation}")
            st.write(f"**Action:** {action_desc}")

            col1, col2 = st.columns(2)
            with col1:
                st.write(f"📊 **Effort:** {effort}")
            with col2:
                st.write(f"🎯 **Impact:** {impact}")

            st.divider()

    # Formatted Text Output (fallback or supplement)
    if results.get('formatted_output'):
        with st.expander("📄 View Full Text Report"):
            st.text(results['formatted_output'])

    # Download report
    st.markdown("---")
    download_data = f"""
FDA COMPLIANCE VALIDATION REPORT
================================

Document: {results['file_name']}
Regulation: {results['regulation']}
Generated: {results['timestamp']}

{results.get('formatted_output', '')}

---
STRUCTURED DATA (JSON)
{json.dumps(structured, indent=2)}

---
Generated by Compliance Check
    """

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📥 Download Text Report",
            data=download_data,
            file_name=f"compliance_report_{results['file_name']}.txt",
            mime="text/plain",
            use_container_width=True
        )
    with col2:
        st.download_button(
            label="📥 Download JSON Data",
            data=json.dumps(structured, indent=2),
            file_name=f"compliance_data_{results['file_name']}.json",
            mime="application/json",
            use_container_width=True
        )

    st.markdown("---")
    if st.button("🔄 Analyze Another Document", use_container_width=True):
        st.session_state.validation_results = None
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p><strong>Compliance Check</strong> - Medical Device Compliance Document Validator</p>
        <p>⚠️ This tool provides preliminary analysis. Always consult with regulatory experts for final compliance determination.</p>
    </div>
""", unsafe_allow_html=True)
