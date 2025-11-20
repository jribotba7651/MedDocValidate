# Overview

This is an FDA Compliance Validator application built with Streamlit that helps validate medical device documentation against FDA regulations. The application allows users to upload PDF documents containing medical device information, extracts text from these documents, and uses AI-powered analysis (via Anthropic's Claude Sonnet 4 model) to assess compliance against various FDA regulations including 21 CFR Part 820, 21 CFR Part 11, ISO 13485, and device classification requirements.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Framework**: Streamlit web application framework
- **Rationale**: Streamlit provides rapid development for data-centric applications with minimal boilerplate code, making it ideal for document processing and analysis tools
- **Layout**: Wide layout configuration for better document viewing and report display
- **Components**: 
  - Main content area for document upload and compliance results
  - Sidebar for application information and regulatory reference documentation

## Backend Architecture
- **Language**: Python 3
- **Entry Point**: `app.py` serves as the main application file
- **Document Processing**: Uses pdfplumber library for PDF text extraction
- **Rationale**: pdfplumber offers reliable text extraction from complex PDF layouts common in regulatory documentation
- **AI Integration**: Anthropic API (Claude Sonnet 4 model) for compliance analysis
- **Rationale**: Large language models excel at understanding regulatory language and identifying compliance gaps in technical documentation

## Data Storage
- **Configuration Storage**: Environment variables for sensitive credentials
- **Session Management**: Streamlit's built-in session state for temporary data persistence during user sessions
- **File Handling**: In-memory processing of uploaded PDF files without permanent storage
- **Rationale**: Compliance documents often contain sensitive information; avoiding persistent storage reduces security risks

## Authentication and Authorization
- **API Authentication**: Anthropic API key stored in environment variables (ANTHROPIC_API_KEY)
- **Access Control**: Application requires valid Anthropic API key to function; stops execution if key is missing
- **Rationale**: Prevents unauthorized API usage and ensures proper error handling for missing credentials

## Design Patterns
- **Error Handling**: Early validation pattern - checks for required API keys before application initialization
- **Separation of Concerns**: Document processing logic separated into dedicated function (`extract_text_from_pdf`)
- **Configuration Management**: Environment-based configuration for deployment flexibility

# External Dependencies

## Third-Party Libraries
- **Streamlit**: Web application framework for the user interface
- **pdfplumber**: PDF text extraction and parsing
- **Anthropic Python SDK**: Client library for Anthropic API integration

## External APIs
- **Anthropic API**: 
  - Purpose: AI-powered compliance analysis using Claude Sonnet 4 model
  - Model: claude-sonnet-4-20250514 (released May 14, 2025)
  - Authentication: API key via environment variable
  - Note: Model version should not be changed unless explicitly requested

## Environment Configuration
- **ANTHROPIC_API_KEY**: Required environment variable for Anthropic API authentication
- **Deployment Platform**: Designed for Replit deployment (references Replit Secrets for API key management)

## Regulatory Reference Data
The application validates against the following FDA regulations (embedded knowledge):
- 21 CFR Part 820 (Quality System Regulation)
- 21 CFR Part 11 (Electronic Records; Electronic Signatures)
- ISO 13485 (Medical devices quality management)
- FDA device classification requirements
- Pre-market submission requirements (510(k), PMA)