# config/messages.py

# --- Booking Prompts (English Templates) ---

PROMPTS = {
    # Initial Prompt to start the booking flow
    "AWAITING_NAME": "I see you want to book! Could you please provide your full name so I can check availability?",

    # After name is received, asking for service
    "AWAITING_SERVICE": "Thank you, {name}. What service are you booking? We offer: {services_list}.",

    # After service is received, asking for time
    "AWAITING_TIME": "Perfect, {service}. What day and time works best for you? Our hours are {hours} (Evening Slot is by Appointment Only).",
    
    # Retry messages
    "RETRY_NAME": "I still need your full name to proceed with the booking.",
    "RETRY_TIME": "I still need a specific date (e.g., YYYY-MM-DD) and time (e.g., HH:MM) to confirm the slot.",
}


# --- Error and Success Messages (English Templates) ---

MESSAGES = {
    # Failures (Used in LLM_FAILURE and Validation)
    "LLM_FAILURE": "⚠️ I apologize, both AI assistants are currently unstable. Please call the clinic directly at {contact} for immediate assistance.",
    "PAST_DATE": "I am sorry, I cannot book an appointment for a date that has already passed. Please select a future date.",
    "TOO_SOON": "I am sorry, you must book at least {minutes} minutes in advance. Please select a slightly later time.",
    "CLOSED_HOURS": "I am sorry, the clinic is closed on weekends (Saturday and Sunday) and outside of our working hours ({hours}). Please select a different day or time.",
    "SERVICE_NOT_FOUND": "I apologize, I didn't recognize that service. Please choose from: {services_list}.",
    
    # Success
    "SUCCESS_BOOKING": "✅ Great news! Your {service} appointment has been tentatively scheduled for {date} at {time} under the name {name}. We'll send you a confirmation message shortly!",
}