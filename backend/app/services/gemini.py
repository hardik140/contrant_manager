import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env if available
load_dotenv()

# Configure the Gemini API client
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Default model
DEFAULT_MODEL = "models/gemini-1.5-flash-latest"  # You can also use "models/gemini-pro"

# Create model instance
model = genai.GenerativeModel(DEFAULT_MODEL)

def summarize_contract(text: str) -> str:
    """
    Summarize the entire contract text using Gemini generate_content.
    """
    prompt = f"Please summarize the following contract in clear bullet points:\n\n{text}"
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error during summarization: {str(e)}"

def compare_with_policy(contract_text: str, policy_text: str) -> str:
    """
    Compare a contract with a policy and highlight differences, gaps or compliance issues.
    """
    prompt = (
        "You are a compliance expert. Compare the following *contract* "
        "against the following internal *policy*. "
        "List key areas of alignment, misalignment, and any risks or gaps. "
        "Use bullet points.\n\n"
        f"CONTRACT:\n{contract_text}\n\n"
        f"POLICY:\n{policy_text}"
    )
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error during comparison: {str(e)}"