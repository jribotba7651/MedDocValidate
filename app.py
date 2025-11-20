import streamlit as st
import pdfplumber
import os
import json
from datetime import datetime
from anthropic import Anthropic
from dotenv import load_dotenv

# The newest Anthropic model is "claude-sonnet-4-20250514", not "claude-3-7-sonnet-20250219", "claude-3-5-sonnet-20241022" nor "claude-3-sonnet-20240229". 
# If the user doesn't specify a model, always prefer using "claude-sonnet-4-20250514" as it is the latest model.
# do not change this unless explicitly requested by the user

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

st.set_page_config(
    page_title="FDA Compliance Validator",
    page_icon="📋",
    layout="wide"
)

if not ANTHROPIC_API_KEY:
    st.warning("⚠️ Anthropic API key not configured. Add it in Settings → Secrets.")
    anthropic_client = None
else:
    anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)

st.title("📋 Medical Device FDA Compliance Validator")
st.markdown("Upload medical device documentation to validate compliance against FDA regulations")

with st.sidebar:
    st.header("About")
    st.write("""
    This tool helps validate medical device compliance documents against FDA regulations.
    
    **Features:**
    - PDF document upload
    - Automated text extraction
    - AI-powered compliance analysis
    - Detailed compliance reports
    """)
    
    st.header("FDA Regulations Checked")
    st.write("""
    - 21 CFR Part 820 (Quality System)
    - 21 CFR Part 11 (Electronic Records)
    - ISO 13485 alignment
    - Device classification requirements
    - Pre-market submission requirements
    """)

def extract_text_from_pdf(pdf_file):
    """Extract text from uploaded PDF file"""
    try:
        text = ""
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        if not text.strip():
            st.warning("⚠️ No text could be extracted from this PDF. This may be a scanned document or image-based PDF. Consider using OCR software to convert it to text first.")
            return None
        
        return text
    except Exception as e:
        st.error(f"Error extracting text from PDF: {str(e)}")
        return None

def validate_compliance(document_text):
    """Use Anthropic Claude to validate compliance against FDA regulations"""
    
    # Check if API client is available
    if anthropic_client is None:
        st.error("⚠️ Cannot validate: Anthropic API key not configured. Please add your API key in Settings → Secrets.")
        return None
    
    try:
        prompt = f"""You are an FDA compliance expert specialized in medical device regulations. 
        
Analyze the following medical device documentation and validate it against FDA regulations including:
- 21 CFR Part 820 (Quality System Regulation)
- 21 CFR Part 11 (Electronic Records)
- Device classification requirements (Class I, II, III)
- Pre-market submission requirements (510(k), PMA, De Novo)
- ISO 13485 quality management standards

Document to analyze:
{document_text[:15000]}

Provide a comprehensive compliance analysis in JSON format with the following structure:
{{
    "overall_compliance_score": <number 0-100>,
    "compliance_status": "<Compliant/Partially Compliant/Non-Compliant>",
    "findings": [
        {{
            "regulation": "<regulation reference>",
            "status": "<Pass/Fail/Needs Review>",
            "description": "<detailed finding>",
            "severity": "<Critical/Major/Minor>"
        }}
    ],
    "recommendations": [
        "<specific recommendation>"
    ],
    "missing_elements": [
        "<missing required element>"
    ],
    "strengths": [
        "<compliance strength>"
    ]
}}

Respond ONLY with valid JSON, no other text."""

        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        content_block = response.content[0]
        if hasattr(content_block, 'text'):
            content = content_block.text
        else:
            content = str(content_block)
        
        # Strip markdown code blocks if present
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:]
        if content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        
        result = json.loads(content)
        return result
    except Exception as e:
        st.error(f"Error during compliance validation: {str(e)}")
        return None

def generate_report(validation_results, filename):
    """Generate a downloadable compliance report"""
    report = f"""
FDA COMPLIANCE VALIDATION REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Document: {filename}

{'='*80}
OVERALL ASSESSMENT
{'='*80}

Compliance Score: {validation_results.get('overall_compliance_score', 'N/A')}/100
Status: {validation_results.get('compliance_status', 'N/A')}

{'='*80}
DETAILED FINDINGS
{'='*80}

"""
    
    findings = validation_results.get('findings', [])
    for i, finding in enumerate(findings, 1):
        report += f"""
Finding #{i}
Regulation: {finding.get('regulation', 'N/A')}
Status: {finding.get('status', 'N/A')}
Severity: {finding.get('severity', 'N/A')}
Description: {finding.get('description', 'N/A')}
{'-'*80}
"""
    
    report += f"""
{'='*80}
MISSING ELEMENTS
{'='*80}

"""
    missing = validation_results.get('missing_elements', [])
    if missing:
        for i, element in enumerate(missing, 1):
            report += f"{i}. {element}\n"
    else:
        report += "No critical missing elements identified.\n"
    
    report += f"""
{'='*80}
RECOMMENDATIONS
{'='*80}

"""
    recommendations = validation_results.get('recommendations', [])
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            report += f"{i}. {rec}\n"
    else:
        report += "No specific recommendations at this time.\n"
    
    report += f"""
{'='*80}
STRENGTHS
{'='*80}

"""
    strengths = validation_results.get('strengths', [])
    if strengths:
        for i, strength in enumerate(strengths, 1):
            report += f"{i}. {strength}\n"
    else:
        report += "Analysis in progress.\n"
    
    report += f"""
{'='*80}
DISCLAIMER
{'='*80}

This report is generated using AI-powered analysis and should be reviewed by 
qualified regulatory professionals. It does not constitute legal or regulatory 
advice. Always consult with FDA compliance experts for final validation.

{'='*80}
"""
    
    return report

uploaded_file = st.file_uploader(
    "Upload Medical Device Compliance Document (PDF)",
    type=['pdf'],
    help="Upload a PDF containing medical device documentation for FDA compliance validation"
)

if uploaded_file is not None:
    st.success(f"File uploaded: {uploaded_file.name}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("File Size", f"{uploaded_file.size / 1024:.2f} KB")
    with col2:
        st.metric("File Type", "PDF")
    
    if st.button("🔍 Validate Compliance", type="primary"):
        with st.spinner("Extracting text from PDF..."):
            document_text = extract_text_from_pdf(uploaded_file)
        
        if document_text:
            st.success(f"✅ Extracted {len(document_text)} characters from PDF")
            
            with st.expander("View Extracted Text (Preview)"):
                st.text_area("Document Text", document_text[:2000] + "..." if len(document_text) > 2000 else document_text, height=200)
            
            with st.spinner("Analyzing compliance against FDA regulations..."):
                validation_results = validate_compliance(document_text)
            
            if validation_results:
                st.success("✅ Compliance validation complete!")
                
                st.header("Validation Results")
                
                col1, col2 = st.columns(2)
                with col1:
                    score = validation_results.get('overall_compliance_score', 0)
                    st.metric("Compliance Score", f"{score}/100")
                with col2:
                    status = validation_results.get('compliance_status', 'Unknown')
                    if status == "Compliant":
                        st.success(f"Status: {status}")
                    elif status == "Partially Compliant":
                        st.warning(f"Status: {status}")
                    else:
                        st.error(f"Status: {status}")
                
                st.subheader("📊 Detailed Findings")
                findings = validation_results.get('findings', [])
                for finding in findings:
                    severity = finding.get('severity', 'Minor')
                    if severity == "Critical":
                        icon = "🔴"
                    elif severity == "Major":
                        icon = "🟡"
                    else:
                        icon = "🟢"
                    
                    with st.expander(f"{icon} {finding.get('regulation', 'N/A')} - {finding.get('status', 'N/A')}"):
                        st.write(f"**Severity:** {severity}")
                        st.write(f"**Description:** {finding.get('description', 'N/A')}")
                
                st.subheader("⚠️ Missing Elements")
                missing = validation_results.get('missing_elements', [])
                if missing:
                    for element in missing:
                        st.warning(element)
                else:
                    st.info("No critical missing elements identified.")
                
                st.subheader("💡 Recommendations")
                recommendations = validation_results.get('recommendations', [])
                if recommendations:
                    for rec in recommendations:
                        st.info(rec)
                else:
                    st.success("No specific recommendations at this time.")
                
                st.subheader("✅ Strengths")
                strengths = validation_results.get('strengths', [])
                if strengths:
                    for strength in strengths:
                        st.success(strength)
                
                report_text = generate_report(validation_results, uploaded_file.name)
                
                st.divider()
                st.subheader("📥 Download Report")
                st.download_button(
                    label="Download Compliance Report",
                    data=report_text,
                    file_name=f"compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
        else:
            st.error("Failed to extract text from PDF. Please ensure the file is a valid PDF document.")

else:
    st.info("👆 Upload a PDF document to begin compliance validation")
    
    st.markdown("---")
    st.subheader("How to Use")
    st.markdown("""
    1. **Upload** your medical device compliance document in PDF format
    2. **Click** the 'Validate Compliance' button to start analysis
    3. **Review** the detailed compliance findings and recommendations
    4. **Download** the comprehensive compliance report
    
    The validator checks your documentation against:
    - Quality System Regulations (21 CFR Part 820)
    - Electronic Records (21 CFR Part 11)
    - Device classification requirements
    - Pre-market submission standards
    - ISO 13485 quality management
    """)
