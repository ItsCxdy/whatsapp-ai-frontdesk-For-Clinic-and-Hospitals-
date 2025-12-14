# 🏥 WhatsApp AI Frontdesk - Conversational Automation for Healthcare

<div align="center">
  <img src="https://img.shields.io/badge/Status-Phase%201%20Complete-brightgreen?style=for-the-badge" alt="Phase 1 Complete">
  <img src="https://img.shields.io/badge/Framework-FastAPI-009688?style=for-the-badge&logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/Language-Python%203.11%2B-blue?style=for-the-badge&logo=python" alt="Python">
</div>

## 💡 Overview

The WhatsApp AI Frontdesk is a modular, multi-lingual conversational AI agent designed to automate the initial patient engagement, scheduling, and FAQ handling for clinics and hospitals via the WhatsApp Business API.

Built on a robust, deterministic state machine and featuring an Asynchronous Triple-Fallback system for reliability, this project demonstrates best practices in combining Large Language Models (LLMs) with strict business logic.

## 🎯 Key Features

- **24/7 Booking Automation**: Full multi-turn appointment scheduling flow (Name → Service → Date/Time).
- **Multilingual Support (Hinglish Ready)**: Uses the LLM to dynamically translate prompts while maintaining conversation context and tone.
- **Business Rule Validation**: Enforces critical healthcare constraints (no past bookings, 30-minute buffer for immediate appointments, and out-of-hours/weekend closure checks).
- **LLM Failover Architecture**: Implements a Primary/Fallback/Emergency system to guarantee a response, even during API downtime (Chutes → OpenRouter → Hardcoded Message).
- **Zero-Downtime Updates**: All user-facing content is externalized into `config/messages.py`, allowing content changes without touching core Python logic.

## 🛠️ Architecture and Stack

The system utilizes a Modular Controller-Service Pattern for high maintainability and testability.

### Technology Stack

| Component          | Technology              | Role                                      |
|--------------------|------------------------|-------------------------------------------|
| Backend           | Python 3.11+          | Core language                            |
| Web Framework     | FastAPI               | Asynchronous Webhook handling (Phase 2) |
| LLMs              | Chutes AI, OpenRouter | Intent Classification, Entity Extraction, Translation |
| Validation        | Custom Python Logic   | Business rule enforcement (Time, Date, Constraints) |
| Configuration     | YAML (business_profile.yaml) | Clinic data and FAQ knowledge base |

### Folder Structure (Phase 1 Final)

```
whatsapp-ai-frontdesk/
├── 📂 config/                 # Centralized Configuration
│   ├── business_profile.yaml   # Clinic hours, services, and FAQs
│   ├── settings.py             # App-wide constants (e.g., buffer time)
│   └── messages.py             # All UI text and conversation prompts
├── 📂 core/                   # Core Logic Controllers
│   ├── llm_client.py           # LLM API interface with Fallback Logic
│   ├── conversation_state.py   # Manages user session memory (State Machine)
│   └── intent_detector.py      # Transforms user message into structured JSON intent
├── 📄 main.py                 # CLI Entry Point (Controller Logic)
└── 📄 .env                    # Environment variables (API Keys, etc.)
```

## 🚀 Getting Started (Phase 1: CLI Testing)

The project is currently configured to run as a Command Line Interface (CLI) application for easy, isolated testing of the core logic and state machine.

### Prerequisites

- Python 3.11+
- pip (Python package installer)
- API keys for your chosen LLM providers (set in `.env`).

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/whatsapp-ai-frontdesk.git
   cd whatsapp-ai-frontdesk
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Linux/macOS
   # .\venv\Scripts\activate  # On Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure Environment Variables:
   Create a file named `.env` in the root directory and add your keys (e.g., for OpenRouter, Chutes, etc.):
   ```bash
   # .env
   CHUTES_API_KEY="your_chutes_key"
   CHUTES_MODEL="chutes-fast-model"
   CHUTES_BASE_URL="https://api.chutes.ai/v1"

   OPENROUTER_API_KEY="your_openrouter_key"
   OR_MODEL="meta-llama/llama-3.2-3b-instruct:free"
   OR_BASE_URL="https://openrouter.ai/api/v1"
   ```

5. Run the CLI Prototype:
   ```bash
   python main.py
   ```

## 💬 Example Interaction

The CLI will guide you through the booking process, demonstrating the state transitions and validation:

```
--- AI Front Desk CLI Prototype (Phase 1 Final) ---
Clinic: City Clinic
Type 'exit' or 'reset' to quit/clear state.

Patient (START): I need a checkup
Assistant: Hello there! I'd be happy to help you with your booking. Could you please share your full name so I can check availability for you?

Patient (AWAITING_NAME): John Doe
Assistant: Thank you, John Doe. What service are you booking? We offer: General Consultation, Pediatric Checkup, Vaccination.

Patient (AWAITING_SERVICE): General Consultation
Assistant: Perfect, General Consultation. What day and time works best for you? Our hours are Mon-Fri from 10:00 AM to 8:00 PM (Evening Slot is by Appointment Only).

Patient (AWAITING_TIME): Today at 10:15 AM
Assistant: I am sorry, you must book at least 30 minutes in advance. Please select a slightly later time.

Patient (AWAITING_TIME): Tomorrow at 11 AM
Assistant: ✅ Great news! Your General Consultation appointment has been tentatively scheduled for 2025-12-15 at 11:00 AM under the name John Doe. We'll send you a confirmation message shortly!
```

## 🛣️ Project Roadmap

We have successfully completed the core logic (Phase 1). The immediate focus is moving this robust controller to a live environment.

### ✅ Phase 1: CLI Prototype & Core Logic (Complete)

- [x] Set up modular folder structure (`core/`, `config/`).
- [x] Implemented `conversation_state.py` (Deterministic State Machine).
- [x] Implemented Asynchronous Triple-Fallback in `llm_client.py`.
- [x] Integrated `config/messages.py` for centralized, editable text.
- [x] Implemented Full Validation Layer (`is_clinic_open` function).

### 🚀 Phase 2: WhatsApp Webhook Integration (In Progress)

This is the current priority.

- [ ] FastAPI application setup and `/webhook` endpoint.
- [ ] Implement verification token security check.
- [ ] Create `services/whatsapp_service.py` for sending and receiving messages.
- [ ] Migrate the `main.py` controller logic into an asynchronous handler function.

### 🔮 Phase 3: Advanced Features & Deployment

- [ ] Implement Audio Handling (Whisper integration for voice messages).
- [ ] Integrate Calendar API (Google Calendar/Outlook) for real-time slot checking.
- [ ] Implement a simple Human Handoff mechanism.
- [ ] Dockerize the application for easy production deployment.

## 🤝 Contributing

We welcome contributions! Whether you're fixing a bug, adding a new feature (like a third LLM fallback), or improving documentation, please feel free to:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Created by [github.com/ItsCxdy, talha.ovais5@gmail.com]  
Built with Python, FastAPI, and the power of LLMs.
