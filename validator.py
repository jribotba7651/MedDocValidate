"""
Enhanced FDA Compliance Validator
Provides structured validation against 21 CFR Part 820 with severity classifications
"""

import json
from typing import Dict, List, Optional
from anthropic import Anthropic


# Severity Definitions based on FDA enforcement precedents
SEVERITY_LEVELS = {
    "CRITICAL": {
        "description": "Direct patient safety impact or likely FDA Warning Letter",
        "risk_level": "HIGH",
        "enforcement_likelihood": "Very High",
        "examples": ["Missing process validation", "No DHR system", "Inadequate CAPA"]
    },
    "MAJOR": {
        "description": "Significant compliance gap, potential FDA 483 observation",
        "risk_level": "MEDIUM-HIGH",
        "enforcement_likelihood": "High",
        "examples": ["Incomplete procedures", "Inadequate training records", "Missing verifications"]
    },
    "MINOR": {
        "description": "Documentation gap or improvement opportunity",
        "risk_level": "LOW-MEDIUM",
        "enforcement_likelihood": "Low",
        "examples": ["Format inconsistencies", "Missing references", "Unclear wording"]
    }
}


# Detailed CFR Requirements
CFR_REQUIREMENTS = {
    "21 CFR Part 820.70 - Production and Process Controls": {
        "citation": "21 CFR 820.70",
        "title": "Production and Process Controls",
        "subsections": {
            "820.70(a)": {
                "requirement": "General - Written procedures for production and process controls",
                "key_elements": [
                    "Written procedures defining and controlling production processes",
                    "Procedures ensure devices conform to specifications",
                    "Monitoring and control of process parameters",
                    "Adherence to procedures is ensured"
                ],
                "critical_keywords": ["procedures", "production", "specifications", "monitoring", "control"]
            },
            "820.70(b)": {
                "requirement": "Production and process changes",
                "key_elements": [
                    "Changes reviewed and approved before implementation",
                    "Impact on device specifications assessed",
                    "Documentation of change control process",
                    "Validation when required"
                ],
                "critical_keywords": ["change control", "approval", "validation", "impact assessment"]
            },
            "820.70(c)": {
                "requirement": "Environmental control",
                "key_elements": [
                    "Environmental conditions controlled where necessary",
                    "Monitoring procedures established",
                    "Action limits defined",
                    "Documentation of environmental controls"
                ],
                "critical_keywords": ["environmental control", "monitoring", "action limits", "cleanroom"]
            },
            "820.70(d)": {
                "requirement": "Personnel",
                "key_elements": [
                    "Personnel qualified for assigned tasks",
                    "Training documented",
                    "Competency demonstrated",
                    "Hygiene practices established"
                ],
                "critical_keywords": ["training", "qualification", "competency", "hygiene"]
            },
            "820.70(e)": {
                "requirement": "Contamination control",
                "key_elements": [
                    "Procedures to prevent contamination",
                    "Cleaning and sanitization protocols",
                    "Sterility maintenance where required",
                    "Documentation of contamination control"
                ],
                "critical_keywords": ["contamination", "cleaning", "sanitization", "sterility"]
            },
            "820.70(f)": {
                "requirement": "Buildings",
                "key_elements": [
                    "Suitable building design for operations",
                    "Space adequate for device manufacturing",
                    "Orderly storage and handling",
                    "Proper maintenance of facilities"
                ],
                "critical_keywords": ["facilities", "building", "space", "storage"]
            },
            "820.70(g)": {
                "requirement": "Equipment",
                "key_elements": [
                    "Equipment suitable for intended use",
                    "Calibration and maintenance schedules",
                    "Adjustment and inspection documented",
                    "Equipment qualification where needed"
                ],
                "critical_keywords": ["equipment", "calibration", "maintenance", "qualification"]
            },
            "820.70(h)": {
                "requirement": "Manufacturing material",
                "key_elements": [
                    "Material handling procedures established",
                    "Material identified and controlled",
                    "Storage conditions appropriate",
                    "Material traceability maintained"
                ],
                "critical_keywords": ["materials", "handling", "storage", "traceability"]
            },
            "820.70(i)": {
                "requirement": "Automated processes",
                "key_elements": [
                    "Automated processes validated",
                    "Software validation documented",
                    "Output quality ensured",
                    "Change control for automation"
                ],
                "critical_keywords": ["automation", "software validation", "computer system"]
            }
        }
    },
    "21 CFR Part 820.75 - Process Validation": {
        "citation": "21 CFR 820.75",
        "title": "Process Validation",
        "subsections": {
            "820.75(a)": {
                "requirement": "General - Validation of processes where results cannot be fully verified",
                "key_elements": [
                    "Validation required for processes not fully verifiable by inspection/testing",
                    "High degree of assurance established",
                    "Approved methods and procedures",
                    "Validation protocol documented"
                ],
                "critical_keywords": ["validation", "protocol", "high degree of assurance", "verification"]
            },
            "820.75(b)": {
                "requirement": "Validation activities",
                "key_elements": [
                    "Validation performed by qualified personnel",
                    "Validation protocol establishes methods and acceptance criteria",
                    "Results documented and approved",
                    "Revalidation when required"
                ],
                "critical_keywords": ["validation protocol", "acceptance criteria", "qualified personnel", "revalidation"]
            }
        }
    },
    "21 CFR Part 820.80 - Receiving, In-Process, and Finished Device Acceptance": {
        "citation": "21 CFR 820.80",
        "title": "Receiving, In-Process, and Finished Device Acceptance",
        "subsections": {
            "820.80(a)": {
                "requirement": "General - Procedures for acceptance activities",
                "key_elements": [
                    "Written procedures for acceptance activities",
                    "Acceptance criteria established",
                    "Acceptance activities documented",
                    "Product release authorization"
                ],
                "critical_keywords": ["acceptance", "procedures", "criteria", "release"]
            },
            "820.80(b)": {
                "requirement": "Receiving acceptance activities",
                "key_elements": [
                    "Incoming product inspected or tested",
                    "Acceptance status documented",
                    "Supplier evaluation performed",
                    "Nonconforming product identified"
                ],
                "critical_keywords": ["receiving inspection", "incoming", "supplier", "acceptance"]
            },
            "820.80(c)": {
                "requirement": "In-process acceptance activities",
                "key_elements": [
                    "In-process inspections and tests performed",
                    "Monitoring of process parameters",
                    "Acceptance documented at specified stages",
                    "Product identification maintained"
                ],
                "critical_keywords": ["in-process", "inspection", "monitoring", "stages"]
            },
            "820.80(d)": {
                "requirement": "Final acceptance activities",
                "key_elements": [
                    "Final inspection and testing performed",
                    "Complete DHR review before release",
                    "All acceptance activities completed",
                    "Release authorization documented"
                ],
                "critical_keywords": ["final inspection", "DHR", "release", "testing"]
            },
            "820.80(e)": {
                "requirement": "Acceptance records",
                "key_elements": [
                    "Records identify inspector or tester",
                    "Date of inspection documented",
                    "Results recorded",
                    "Acceptance/rejection decision clear"
                ],
                "critical_keywords": ["records", "inspector", "date", "results"]
            }
        }
    }
}


class FDAComplianceValidator:
    """Enhanced FDA Compliance Validator with structured analysis"""

    def __init__(self, api_key: str):
        """Initialize validator with Anthropic API key"""
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"

    def get_regulation_requirements(self, regulation: str) -> Dict:
        """Get detailed requirements for a specific regulation"""
        for reg_key, reg_data in CFR_REQUIREMENTS.items():
            if regulation in reg_key:
                return reg_data
        return {}

    def build_enhanced_prompt(self, document_text: str, regulation: str, detail_level: str) -> str:
        """Build enhanced validation prompt with structured output requirements"""

        reg_requirements = self.get_regulation_requirements(regulation)

        if not reg_requirements:
            return self._build_basic_prompt(document_text, regulation, detail_level)

        # Build detailed subsection requirements
        subsection_details = ""
        for subsection, details in reg_requirements.get("subsections", {}).items():
            subsection_details += f"\n{subsection}: {details['requirement']}\n"
            subsection_details += f"Key Elements to Verify:\n"
            for element in details['key_elements']:
                subsection_details += f"  - {element}\n"

        prompt = f"""You are an FDA regulatory compliance expert with extensive experience in medical device inspections and 21 CFR Part 820 Quality System Regulations.

REGULATION TO ASSESS: {reg_requirements['title']} ({reg_requirements['citation']})

DETAILED REQUIREMENTS:
{subsection_details}

SEVERITY CLASSIFICATION GUIDELINES:
- CRITICAL: Direct patient safety impact, missing required systems, likely FDA Warning Letter
  Examples: Missing validation, no DHR system, inadequate CAPA

- MAJOR: Significant compliance gap, likely FDA 483 observation, regulatory action possible
  Examples: Incomplete procedures, inadequate training records, missing critical documentation

- MINOR: Documentation improvement opportunity, low enforcement risk
  Examples: Format inconsistencies, unclear wording, missing non-critical references

DOCUMENT TO ANALYZE:
{document_text}

ANALYSIS REQUIREMENTS ({detail_level} level):
Provide a thorough, structured analysis. You MUST respond with valid JSON in the following format:

{{
  "overall_assessment": {{
    "compliance_score": <0-100>,
    "overall_risk_level": "HIGH|MEDIUM|LOW",
    "ready_for_fda_inspection": true|false,
    "executive_summary": "Brief 2-3 sentence summary of compliance status"
  }},
  "findings": [
    {{
      "cfr_citation": "21 CFR 820.XX(x)",
      "requirement_description": "What the regulation requires",
      "finding": "Specific gap or compliance observation found in the document",
      "severity": "CRITICAL|MAJOR|MINOR",
      "severity_justification": "Why this severity level was assigned based on FDA enforcement precedents",
      "evidence": "Specific quotes or references from the document (or lack thereof)",
      "risk_to_compliance": "What could happen if not addressed",
      "recommendation": "Specific, actionable steps to address this finding",
      "regulatory_precedent": "FDA enforcement examples or guidance documents that support this assessment"
    }}
  ],
  "strengths": [
    {{
      "cfr_citation": "21 CFR 820.XX(x)",
      "description": "What the document does well in terms of compliance"
    }}
  ],
  "priority_actions": [
    {{
      "priority": "1|2|3",
      "action": "Specific action to take",
      "cfr_citation": "21 CFR 820.XX(x)",
      "estimated_effort": "LOW|MEDIUM|HIGH",
      "impact": "How this improves compliance"
    }}
  ],
  "inspection_readiness": {{
    "critical_gaps_count": <number>,
    "major_gaps_count": <number>,
    "minor_gaps_count": <number>,
    "estimated_time_to_compliance": "Realistic estimate",
    "inspection_risk_areas": ["List of areas that would likely receive scrutiny"]
  }}
}}

IMPORTANT:
- Be thorough and cite specific CFR subsections
- Base severity on real FDA enforcement precedents
- Provide actionable, specific recommendations
- Consider industry best practices beyond minimum compliance
- Return ONLY valid JSON, no additional text or markdown formatting
"""
        return prompt

    def _build_basic_prompt(self, document_text: str, regulation: str, detail_level: str) -> str:
        """Fallback basic prompt if regulation not in detailed requirements"""
        prompt = f"""You are an FDA regulatory compliance expert. Analyze the following medical device document against {regulation}.

Document Content:
{document_text}

Provide a {detail_level.lower()} analysis with valid JSON format:

{{
  "overall_assessment": {{
    "compliance_score": <0-100>,
    "overall_risk_level": "HIGH|MEDIUM|LOW",
    "executive_summary": "Brief summary"
  }},
  "findings": [
    {{
      "cfr_citation": "21 CFR XXX.XX",
      "finding": "Gap description",
      "severity": "CRITICAL|MAJOR|MINOR",
      "recommendation": "Specific action"
    }}
  ]
}}

Return ONLY valid JSON.
"""
        return prompt

    def validate_document(
        self,
        document_text: str,
        regulation: str,
        detail_level: str = "Standard"
    ) -> Dict:
        """
        Validate document against FDA regulation

        Args:
            document_text: Extracted text from PDF document
            regulation: Full regulation name (e.g., "21 CFR Part 820.70 - Production and Process Controls")
            detail_level: Analysis depth ("Basic", "Standard", "Comprehensive")

        Returns:
            Dict containing structured validation results
        """
        # Build enhanced prompt
        prompt = self.build_enhanced_prompt(document_text, regulation, detail_level)

        # Call Claude API
        message = self.client.messages.create(
            model=self.model,
            max_tokens=8000,  # Increased for detailed structured output
            temperature=0,  # Deterministic for compliance analysis
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Extract response
        response_text = message.content[0].text

        # Try to parse as JSON
        try:
            # Remove markdown code blocks if present
            if response_text.strip().startswith("```"):
                # Extract content between ```json and ```
                lines = response_text.split('\n')
                json_lines = []
                in_code_block = False
                for line in lines:
                    if line.strip().startswith("```"):
                        in_code_block = not in_code_block
                        continue
                    if in_code_block:
                        json_lines.append(line)
                response_text = '\n'.join(json_lines)

            validation_results = json.loads(response_text)
            return validation_results

        except json.JSONDecodeError:
            # If JSON parsing fails, return structured error with raw text
            return {
                "overall_assessment": {
                    "compliance_score": 0,
                    "overall_risk_level": "UNKNOWN",
                    "executive_summary": "Unable to parse structured results. See raw analysis below."
                },
                "raw_analysis": response_text,
                "error": "JSON parsing failed - response may not be properly structured"
            }

    def format_results_for_display(self, results: Dict) -> str:
        """Format JSON results into readable text for UI display"""

        if "error" in results:
            return results.get("raw_analysis", "Analysis failed")

        output = []

        # Overall Assessment
        assessment = results.get("overall_assessment", {})
        output.append("=" * 60)
        output.append("OVERALL COMPLIANCE ASSESSMENT")
        output.append("=" * 60)
        output.append(f"Compliance Score: {assessment.get('compliance_score', 'N/A')}%")
        output.append(f"Overall Risk Level: {assessment.get('overall_risk_level', 'N/A')}")
        output.append(f"FDA Inspection Ready: {assessment.get('ready_for_fda_inspection', 'N/A')}")
        output.append(f"\n{assessment.get('executive_summary', '')}")

        # Inspection Readiness
        if "inspection_readiness" in results:
            ir = results["inspection_readiness"]
            output.append("\n" + "=" * 60)
            output.append("INSPECTION READINESS SUMMARY")
            output.append("=" * 60)
            output.append(f"Critical Gaps: {ir.get('critical_gaps_count', 0)}")
            output.append(f"Major Gaps: {ir.get('major_gaps_count', 0)}")
            output.append(f"Minor Gaps: {ir.get('minor_gaps_count', 0)}")
            output.append(f"Estimated Time to Compliance: {ir.get('estimated_time_to_compliance', 'N/A')}")

            if ir.get('inspection_risk_areas'):
                output.append("\nHigh-Risk Areas for Inspection:")
                for area in ir['inspection_risk_areas']:
                    output.append(f"  • {area}")

        # Findings
        findings = results.get("findings", [])
        if findings:
            output.append("\n" + "=" * 60)
            output.append("DETAILED FINDINGS")
            output.append("=" * 60)

            for i, finding in enumerate(findings, 1):
                output.append(f"\n[{i}] {finding.get('cfr_citation', 'N/A')} - {finding.get('severity', 'N/A')}")
                output.append(f"Requirement: {finding.get('requirement_description', 'N/A')}")
                output.append(f"Finding: {finding.get('finding', 'N/A')}")
                output.append(f"Risk: {finding.get('risk_to_compliance', 'N/A')}")
                output.append(f"Recommendation: {finding.get('recommendation', 'N/A')}")

                if finding.get('regulatory_precedent'):
                    output.append(f"Regulatory Precedent: {finding['regulatory_precedent']}")

        # Strengths
        strengths = results.get("strengths", [])
        if strengths:
            output.append("\n" + "=" * 60)
            output.append("COMPLIANCE STRENGTHS")
            output.append("=" * 60)
            for strength in strengths:
                output.append(f"✓ {strength.get('cfr_citation', 'N/A')}: {strength.get('description', 'N/A')}")

        # Priority Actions
        priority_actions = results.get("priority_actions", [])
        if priority_actions:
            output.append("\n" + "=" * 60)
            output.append("PRIORITY ACTIONS")
            output.append("=" * 60)
            for action in sorted(priority_actions, key=lambda x: x.get('priority', 999)):
                output.append(f"\nPriority {action.get('priority', 'N/A')} - {action.get('cfr_citation', 'N/A')}")
                output.append(f"Action: {action.get('action', 'N/A')}")
                output.append(f"Effort: {action.get('estimated_effort', 'N/A')} | Impact: {action.get('impact', 'N/A')}")

        return "\n".join(output)


# Convenience function for quick validation
def validate_compliance(
    api_key: str,
    document_text: str,
    regulation: str,
    detail_level: str = "Standard"
) -> Dict:
    """
    Quick validation function

    Args:
        api_key: Anthropic API key
        document_text: Document text to validate
        regulation: CFR regulation to check against
        detail_level: Analysis depth

    Returns:
        Structured validation results
    """
    validator = FDAComplianceValidator(api_key)
    return validator.validate_document(document_text, regulation, detail_level)
