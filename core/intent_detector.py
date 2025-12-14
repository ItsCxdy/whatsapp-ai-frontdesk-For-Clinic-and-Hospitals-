# core/intent_detector.py (Refactored)
import json
import os
from datetime import datetime
from .llm_client import LLMFallbackService # Import the new service

# The LLM_CLIENT is now initialized once
LLM_CLIENT = LLMFallbackService()

# --- Helper function for structured extraction (using the client) ---

def extract_entities_sync(user_input: str, current_state: str, business_data: dict) -> dict:
    
    # ... (Schema definition and System Prompt remain the same as the last successful version) ...
    if current_state in ["START", "AWAITING_NAME"]:
        json_schema = {
            "intent": "string (BOOKING, FAQ, ESCALATION, GREETING, OTHER)",
            "name": "string (Patient's full name, or null)",
            "service_request": "string (The requested service, or null)",
            "detected_language": "string (e.g., 'Hindi', 'English', 'Hinglish')" # NEW FIELD
        }
    elif current_state == "AWAITING_SERVICE":
         json_schema = {
            "service_request": "string (The exact service name from the list, or null)",
         }
    elif current_state == "AWAITING_TIME":
        json_schema = {
            # MODIFIED: Explicitly demand YYYY-MM-DD format resolution
            "date": "string (The extracted date, resolved to YYYY-MM-DD format, or null)",
            # MODIFIED: Explicitly demand 24-hour format resolution
            "time": "string (The extracted time, resolved to HH:MM 24-hour format, or null)",
        }
    else:
        json_schema = {"intent": "string (FALLBACK)"}

    # --- System Prompt Construction (CRITICAL INSTRUCTION FOR DATE/TIME and Multilingual) ---
    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    system_prompt = f"""
    You are a precise data extraction tool for a clinic.
    Your current task is to extract information from the user's message based on the current conversation state ('{current_state}').
    
    **CRITICAL INSTRUCTION FOR DATE/TIME:** If the user uses relative terms like 'tomorrow', 'next week', 'tonight', or '5:30 PM', you MUST resolve them to the current, absolute date and time formats (YYYY-MM-DD and HH:MM 24-hour format) based on the current date: {datetime.now().strftime('%Y-%m-%d')}.
    
    CLINIC DETAILS: {json.dumps(business_data.get('clinic_info', {}))}
    CLINIC SERVICES: {[s['name'] for s in business_data.get('services', [])]}
    
    Output MUST be a single, valid JSON object that strictly follows the REQUIRED JSON SCHEMA.
    Do NOT include any other text, markdown, or reasoning. Return null for missing fields.
    """
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"User Input: '{user_input}'. REQUIRED JSON SCHEMA: {json_schema}"}
    ]

    # Use the Fallback Service to get a structured JSON response
    llm_result = LLM_CLIENT.get_response_sync(messages, structured=True)
    
    print(f"DEBUG: LLM Provider Used: {llm_result['provider']}")

    try:
        # Check for the standardized failure intent before loading JSON
        if '"intent": "LLM_FAILURE"' in llm_result['content']:
            return {"intent": "LLM_FAILURE"}

        return json.loads(llm_result['content'])
        
    except Exception as e:
        print(f"Failed to parse LLM response to JSON from {llm_result['provider']}: {e}")
        return {"intent": "LLM_FAILURE"}

# --- Helper function for FAQ response (using the client) ---

def generate_faq_response_sync(user_input: str, business_data: dict) -> str:
    """Synchronous wrapper for LLM call to generate a natural language response (FAQ/Chat)."""
    
    # ... (System Prompt construction for FAQ remains the same, emphasizing multilingual support) ...
    system_prompt = f"""
    You are Dr. Sharma's professional front desk assistant.
    You must communicate fluently in the language the user uses (English, Hindi, or Hinglish).
    
    Answer the user's question using ONLY the provided CLINIC DETAILS AND FAQs.
    If the question cannot be answered with the provided data, politely escalate by saying:
    'I cannot find that information. Let me connect you with the admin at {business_data['clinic_info']['contact']}.'
    
    CLINIC DETAILS: {json.dumps(business_data)}
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]

    llm_result = LLM_CLIENT.get_response_sync(messages, structured=False)
    
    # Check for the standardized failure intent
    if '"intent": "LLM_FAILURE"' in llm_result['content']:
        return f"⚠️ I apologize, both AI assistants are currently unstable. Please call the clinic directly at {business_data['clinic_info']['contact']} for immediate assistance."

    return llm_result['content']