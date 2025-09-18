import os
import re
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env if available
load_dotenv()

# Configure the Gemini API client
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Default model
DEFAULT_MODEL = "models/gemini-2.0-flash"  # You can also use "models/gemini-pro"

# Create model instance
model = genai.GenerativeModel(DEFAULT_MODEL)

def strip_markdown_formatting(text: str) -> str:
    """
    Remove markdown formatting symbols to make text look more professional
    """
    # Remove code blocks first (```code``` -> code)
    text = re.sub(r'```[\w]*\s*(.*?)\s*```', r'\1', text, flags=re.DOTALL)
    
    # Remove bold formatting (**text** or __text__)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    
    # Remove italic formatting (*text* or _text_)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'_(.*?)_', r'\1', text)
    
    # Remove inline code formatting (`code`)
    text = re.sub(r'`(.*?)`', r'\1', text)
    
    # Remove headers (## Header -> Header)
    text = re.sub(r'^#{1,6}\s+(.*?)$', r'\1', text, flags=re.MULTILINE)
    
    # Remove strikethrough (~~text~~)
    text = re.sub(r'~~(.*?)~~', r'\1', text)
    
    # Clean up multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

def summarize_contract(text: str) -> str:
    """
    Summarize the entire contract text using Gemini generate_content.
    """
    prompt = (
        "You are a highly skilled legal analyst and contract writer. Your task is to transform the provided contract text into a concise, professional, and legally accurate summary that retains ALL critical details, clauses, and obligations. "
        " Preserve all key legal terms, obligations, timelines, penalties, rights, and responsibilities of each party. "
        " Maintain original meaning and avoid altering legal intent."
        " Use clear, precise, and professional legal language suitable for business executives and lawyers."
        "Organize the output into clearly labeled sections (e.g., Purpose, Parties Involved, Scope of Work, Payment Terms, Confidentiality, Termination, Governing Law, Dispute Resolution)." \
        "For complex clauses, rewrite them in simpler professional language without omitting any facts."
        "Highlight risk points or unusual clauses that may require legal review."
        "Use plain text formatting without markdown symbols, asterisks, or special formatting."
        "If the text is processed in parts (chunks), maintain consistent terminology and merge results into a final unified summary.\n\n"
        f"{text}"
    )
    try:
        response = model.generate_content(prompt)
        # Clean up any markdown formatting that might still appear
        return strip_markdown_formatting(response.text)
    except Exception as e:
        return f"Error during summarization: {str(e)}"

def compare_with_policy(contract_text: str, policy_text: str) -> dict:
    """
    Compare a contract with a policy and highlight differences, gaps or compliance issues.
    Returns a structured JSON object with analysis data.
    """
    prompt = (
        "You are a compliance expert. Compare the following *contract* "
        "against the following internal *policy*. "
        "Provide a detailed analysis including: "
        "1. A summary of overall compliance status "
        "2. Specific violations with references to policy clauses "
        "3. Suggested fixes for compliance issues "
        "4. Metrics about text similarity\n\n"
        f"CONTRACT:\n{contract_text}\n\n"
        f"POLICY:\n{policy_text}\n\n"
        "Return your response as a detailed professional report using plain text formatting without markdown symbols, asterisks, or special formatting. "
        "Use clear section headings and bullet points with standard text characters."
    )
    try:
        response = model.generate_content(prompt)
        result_text = strip_markdown_formatting(response.text)
        
        # Create a structured result that matches the frontend's expected format
        structured_result = {
            "compliance_analysis": {
                "compliance_summary": "Analysis in progress. Please see the full report below.",
                "violations": [
                    {
                        "policy_clause": "General Compliance",
                        "violation": "Automated analysis complete. Please review the detailed report.",
                        "suggested_fix": "See recommendations in the report."
                    }
                ]
            },
            "analysis_metrics": {
                "text_metrics": {
                    "contract": {
                        "original_length": len(contract_text),
                        "normalized_length": len(contract_text.strip()),
                        "characters_cleaned": 0,
                        "dates_standardized": 0
                    },
                    "policy": {
                        "original_length": len(policy_text),
                        "normalized_length": len(policy_text.strip()),
                        "characters_cleaned": 0,
                        "dates_standardized": 0
                    }
                },
                "semantic_similarity": {
                    "overall_similarity": 0.5,  # Default placeholder
                    "matching_sections": [
                        {
                            "policy_text": "See detailed report",
                            "contract_text": "See detailed report",
                            "similarity_score": 0.5
                        }
                    ]
                }
            },
            "full_report": result_text
        }
        
        return structured_result
    except Exception as e:
        # Return a valid structure even in case of error
        return {
            "compliance_analysis": {
                "compliance_summary": f"Error during analysis: {str(e)}",
                "violations": []
            },
            "analysis_metrics": {
                "text_metrics": {
                    "contract": {"original_length": len(contract_text)},
                    "policy": {"original_length": len(policy_text)}
                },
                "semantic_similarity": {
                    "overall_similarity": 0,
                    "matching_sections": []
                }
            }
        }