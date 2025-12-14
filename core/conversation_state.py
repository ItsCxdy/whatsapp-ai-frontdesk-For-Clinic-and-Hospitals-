# core/conversation_state.py
import json
import os
from datetime import datetime
from typing import Dict, Any

# Define the location for state files (one file per user/phone number)
STATE_DIR = "data/conversations"
os.makedirs(STATE_DIR, exist_ok=True)
STATE_FILE_PATH = os.path.join(STATE_DIR, "{user_id}.json")

class ConversationState:
    
    # Define States for the Booking Workflow
    STATES = ["START", "AWAITING_NAME", "AWAITING_SERVICE", "AWAITING_TIME", 
              "CONFIRMATION", "BOOKED", "FAQ_MODE", "ESCALATED"]

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.state: str = "START"
        # Context stores extracted data: name, service, date, etc.
        self.context: Dict[str, Any] = {}
        self._load_state()

    def _get_file_path(self):
        return STATE_FILE_PATH.format(user_id=self.user_id)

    def _load_state(self):
        try:
            with open(self._get_file_path(), 'r') as f:
                data = json.load(f)
                self.state = data.get("state", "START")
                self.context = data.get("context", {})
        except (FileNotFoundError, json.JSONDecodeError):
            # State file doesn't exist or is invalid, start fresh
            pass

    def save_state(self):
        data = {
            "state": self.state,
            "last_updated": datetime.now().isoformat(),
            "context": self.context
        }
        with open(self._get_file_path(), 'w') as f:
            json.dump(data, f, indent=4)

    def update_state(self, new_state: str, context_updates: Dict[str, Any] = None):
        if new_state not in self.STATES:
            print(f"ERROR: Invalid state '{new_state}' requested.")
            return

        print(f"DEBUG: State transition: {self.state} -> {new_state}")
        self.state = new_state
        if context_updates:
            self.context.update(context_updates)
        self.save_state()

    def is_booking_in_progress(self) -> bool:
        return self.state in ["AWAITING_NAME", "AWAITING_SERVICE", "AWAITING_TIME", "CONFIRMATION"]

    def reset(self):
        """Resets the state, typically after booking or timeout."""
        self.update_state("START", context_updates={})