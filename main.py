# main.py
import yaml
import os
from datetime import datetime, date, timedelta
from typing import Dict, Any, Union

# Core System Modules
from core.llm_client import LLMFallbackService
from core.conversation_state import ConversationState
from core.intent_detector import extract_entities_sync, generate_faq_response_sync

# Configuration Modules
from config.settings import BOOKING_BUFFER_MINUTES # Constant for validation
from config.messages import MESSAGES, PROMPTS     # All user-facing text

# Initialize the LLM Client once for the entire application lifetime
LLM_CLIENT = LLMFallbackService()

# --- Load Config ---
def load_config(path="config/business_profile.yaml"):
    """Loads the business configuration from YAML."""
    try:
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading config: {e}. Exiting.")
        exit()

# --- Validation Helper (I. Remaining Logical & Validation Checks) ---
def is_clinic_open(booking_date_str: str, booking_time_str: str, business_data: dict) -> Dict[str, Union[bool, str]]:
    """
    Checks if the proposed date/time falls within operating hours, is not in the past,
    and is not too soon for an immediate booking.
    """
    current_datetime = datetime.now()
    
    try:
        booking_datetime = datetime.strptime(f"{booking_date_str} {booking_time_str}", "%Y-%m-%d %H:%M")
        booking_date = booking_datetime.date()
    except ValueError:
        # Catch unexpected date/time format errors from LLM extraction
        return {"valid": False, "reason": "PAST_DATE"}
        
    # Check 1: Is the proposed date in the past?
    if booking_date < current_datetime.date():
        return {"valid": False, "reason": "PAST_DATE"}
        
    # Check 2: If the proposed date is TODAY, is the time too soon?
    if booking_date == current_datetime.date():
        # Require a buffer time (e.g., 30 minutes)
        if booking_datetime < (current_datetime + timedelta(minutes=BOOKING_BUFFER_MINUTES)):
            return {"valid": False, "reason": "TOO_SOON"}

    # Check 3: Is it a weekend (Saturday or Sunday)?
    # Monday is 0, Sunday is 6
    if booking_datetime.weekday() >= 5:
        return {"valid": False, "reason": "CLOSED_HOURS"}
        
    # Note: Phase 3 will add robust time-of-day checks here.
        
    return {"valid": True, "reason": "OK"}

# --- NEW: Helper for Formatting and Translating Validation Errors ---
def _get_translated_error_response(validation_result: Dict[str, Union[bool, str]], biz_data: dict, user_lang: str) -> str:
    """Centralizes the logic for formatting and translating validation failure messages."""
    
    reason = validation_result["reason"]
    hours = biz_data['clinic_info']['hours']
    
    # 1. Select the English message template based on the failure reason
    if reason == "TOO_SOON":
        english_failure = MESSAGES[reason].format(minutes=BOOKING_BUFFER_MINUTES)
    elif reason == "CLOSED_HOURS":
         english_failure = MESSAGES[reason].format(hours=hours)
    else:
        # Catches PAST_DATE and any other unexpected 'reason' codes
        english_failure = MESSAGES[reason]
        
    # 2. Translate the finalized message
    return LLM_CLIENT.translate_prompt_sync(english_failure, user_lang)

# --- Main Controller Logic ---
def run_cli():
    """Runs the command-line interface for the AI Front Desk prototype."""
    
    # 1. Initialization
    biz_data = load_config()
    CLI_USER_ID = "cli_tester_123"
    state_manager = ConversationState(CLI_USER_ID)
    
    # FIX: Ensure a clean state for every new CLI execution.
    state_manager.reset()
    
    print("--- AI Front Desk CLI Prototype (Phase 1 Final) ---")
    print(f"Clinic: {biz_data['clinic_info']['name']}")
    print("Type 'exit' or 'reset' to quit/clear state.\n")

    while True:
        user_msg = input(f"Patient ({state_manager.state}): ")
        if user_msg.lower() in ["exit", "quit"]:
            break
        if user_msg.lower() == "reset":
            state_manager.reset()
            print("Assistant: Conversation state reset.\n")
            continue

        # 2. Extract Entities and Intent (LLM Call)
        llm_output = extract_entities_sync(user_msg, state_manager.state, biz_data)
        
        # Check for LLM Failure (Centralized Error Handling)
        if llm_output.get("intent") == "LLM_FAILURE":
             english_failure = MESSAGES["LLM_FAILURE"].format(contact=biz_data['clinic_info']['contact'])
             response_text = LLM_CLIENT.translate_prompt_sync(english_failure, state_manager.context.get("language", "English"))
             print(f"Assistant: {response_text}\n")
             continue

        # --- Multilingual & Context Setup ---
        user_lang = llm_output.get("detected_language", state_manager.context.get("language", "English"))
        state_manager.context['language'] = user_lang
        
        # Variables for prompt formatting
        services_list = [s['name'] for s in biz_data.get('services', [])]
        name = state_manager.context.get("name", llm_output.get("name"))
        service = state_manager.context.get("service")
        hours = biz_data['clinic_info']['hours']

        # 3. Deterministic State Progression
        response_text = ""
        current_intent = llm_output.get("intent", "OTHER").upper()
        
        # --- START -> AWAITING_NAME ---
        if not state_manager.is_booking_in_progress() and current_intent == "BOOKING":
            state_manager.update_state("AWAITING_NAME")
            english_prompt = PROMPTS["AWAITING_NAME"]
            response_text = LLM_CLIENT.translate_prompt_sync(english_prompt, user_lang)
            
        # --- AWAITING_NAME State ---
        elif state_manager.state == "AWAITING_NAME":
            extracted_name = llm_output.get("name")
            if extracted_name:
                state_manager.update_state("AWAITING_SERVICE", {"name": extracted_name})
                
                english_prompt = PROMPTS["AWAITING_SERVICE"].format(
                    name=extracted_name,
                    services_list=', '.join(services_list)
                )
                response_text = LLM_CLIENT.translate_prompt_sync(english_prompt, user_lang)
            else:
                english_prompt = PROMPTS["RETRY_NAME"]
                response_text = english_prompt

        # --- AWAITING_SERVICE State ---
        elif state_manager.state == "AWAITING_SERVICE":
            service = llm_output.get("service_request")
            valid_services = [s['name'] for s in biz_data.get('services', [])]
            
            if service and service in valid_services:
                state_manager.update_state("AWAITING_TIME", {"service": service})
                
                english_prompt = PROMPTS["AWAITING_TIME"].format(
                    service=service,
                    hours=hours
                )
                response_text = LLM_CLIENT.translate_prompt_sync(english_prompt, user_lang)
            else:
                english_failure = MESSAGES["SERVICE_NOT_FOUND"].format(services_list=', '.join(valid_services))
                response_text = LLM_CLIENT.translate_prompt_sync(english_failure, user_lang)
        
        # --- AWAITING_TIME State (Validation Hub) ---
        elif state_manager.state == "AWAITING_TIME":
            date = llm_output.get("date")
            time = llm_output.get("time")
            
            if date and time:
                validation_result = is_clinic_open(date, time, biz_data)
                
                if validation_result["valid"]:
                    # SUCCESS: Book and Reset
                    state_manager.update_state("BOOKED", {"date": date, "time": time})
                    final_name = state_manager.context.get("name", "Patient")
                    final_service = state_manager.context.get("service", "consultation")
                    
                    english_success = MESSAGES["SUCCESS_BOOKING"].format(
                        service=final_service, date=date, time=time, name=final_name
                    )
                    response_text = LLM_CLIENT.translate_prompt_sync(english_success, user_lang)
                    state_manager.reset()

                else:
                    # FAILURE PATH (Refactored)
                    state_manager.update_state("AWAITING_TIME")
                    
                    response_text = _get_translated_error_response(validation_result, biz_data, user_lang)
                    
            else:
                # If date/time was not extracted, retry the prompt
                english_prompt = PROMPTS["RETRY_TIME"]
                response_text = LLM_CLIENT.translate_prompt_sync(english_prompt, user_lang)

        # --- Default/FAQ Handling ---
        else:
            response_text = generate_faq_response_sync(user_msg, biz_data)
            if not state_manager.is_booking_in_progress():
                 state_manager.update_state("START")
        
        print(f"Assistant: {response_text}\n")


if __name__ == "__main__":
    run_cli()