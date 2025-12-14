# core/llm_client.py
import os
import asyncio
import json
import aiohttp
from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAI
from typing import Dict, Any

load_dotenv()

# --- Configuration ---
# Primary (Chutes)
CHUTES_API_KEY = os.getenv("CHUTES_API_KEY")
CHUTES_MODEL = os.getenv("CHUTES_MODEL")
CHUTES_BASE_URL = os.getenv("CHUTES_BASE_URL").replace("/chat/completions", "") # Openai clients expect the base URL

# Fallback (OpenRouter)
OR_API_KEY = os.getenv("OPENROUTER_API_KEY")
OR_MODEL = os.getenv("OPENROUTER_MODEL")
OR_BASE_URL = os.getenv("OPENROUTER_BASE_URL")

# --- LLM Client Class ---

class LLMFallbackService:
    def __init__(self):
        # 1. Primary Client (Chutes/aiohttp) - Uses low-level aiohttp for current Chutes endpoint format
        self.primary_config = {
            "key": CHUTES_API_KEY,
            "url": os.getenv("CHUTES_BASE_URL"),
            "model": CHUTES_MODEL,
            "name": "Chutes AI (Primary)"
        }
        
        # 2. Fallback Client (OpenRouter/AsyncOpenAI) - Use ASYNC client
        self.fallback_client = AsyncOpenAI(
            base_url=OR_BASE_URL,
            api_key=OR_API_KEY,
        )
        self.fallback_model = OR_MODEL
        self.fallback_name = "OpenRouter (Fallback)"

    async def _call_chutes_async(self, messages: list, response_format: Dict[str, Any] = None) -> str:
        """Low-level aiohttp call to Chutes API (Primary)."""
        headers = {
            "Authorization": f"Bearer {self.primary_config['key']}",
            "Content-Type": "application/json"
        }
        body = {
            "model": self.primary_config['model'],
            "messages": messages,
            "temperature": 0.1,  
            "max_tokens": 1024,
        }
        if response_format:
            body["response_format"] = response_format

        async with aiohttp.ClientSession() as session:
            # ssl=False for testing environment stability
            async with session.post(self.primary_config['url'], headers=headers, json=body, ssl=False) as response:
                if response.status != 200:
                    data = await response.json()
                    error_msg = data.get("error", {}).get("message", "Unknown API error")
                    raise Exception(f"Chutes HTTP Error ({response.status}): {error_msg}")
                
                data = await response.json()
                if 'choices' in data and data['choices'] and 'message' in data['choices'][0]:
                    return data['choices'][0]['message']['content']
                else:
                    raise Exception(f"Chutes Response Structure Missing.")

    async def _call_openrouter_async(self, messages: list, response_format: Dict[str, Any] = None) -> str:
        """Standard ASYNC SDK call to OpenRouter (Fallback)."""
        completion = await self.fallback_client.chat.completions.create(
            model=self.fallback_model,
            messages=messages,
            temperature=0.1,
            max_tokens=1024,
            response_format=response_format if response_format else None
        )
        return completion.choices[0].message.content

    # --- SYNCHRONOUS WRAPPER FOR CLI (Only used by main.py) ---
    
    def get_response_sync(self, messages: list, structured: bool = False) -> Dict[str, Any]:
        """
        Synchronous wrapper implementing Primary-Fallback logic using asyncio.run().
        DO NOT USE THIS IN FASTAPI.
        """
        return asyncio.run(self.get_response_async(messages, structured=structured))

    # --- CORE ASYNC LOGIC (To be used in FastAPI/Phase 2) ---
    async def get_response_async(self, messages: list, structured: bool = False) -> Dict[str, Any]:
        """
        Asynchronous method implementing Primary-Fallback logic.
        Returns a dict: {"content": response_string, "provider": provider_name}
        """
        response_format = {"type": "json_object"} if structured else None
        
        # 1. Attempt Primary (Chutes AI)
        try:
            print("INFO: Attempting Primary LLM (Chutes AI)...")
            content = await self._call_chutes_async(messages, response_format)
            return {"content": content, "provider": self.primary_config['name']}
        except Exception as e:
            print(f"WARN: Primary LLM failed ({e}). Falling back to OpenRouter.")
            
        # 2. Attempt Fallback 1 (OpenRouter)
        try:
            print("INFO: Attempting Fallback LLM 1 (OpenRouter)...")
            content = await self._call_openrouter_async(messages, response_format)
            return {"content": content, "provider": self.fallback_name}
        except Exception as e:
            print(f"ERROR: Fallback LLM 1 also failed: {e}")
            
        # 3. Final Failure
        return {"content": json.dumps({"intent": "LLM_FAILURE"}), "provider": "NONE"}

    def translate_prompt_sync(self, required_prompt: str, user_language: str) -> str:
        """Uses LLM to translate or localize a fixed prompt, preserving Hinglish style."""
        
        # NEW SYSTEM PROMPT: Explicitly instructs the LLM to adapt to Hinglish
        messages = [
            {"role": "system", "content": f"You are a professional translator and receptionist. Translate the following English prompt into a conversational, polite {user_language} response. If the requested language is 'Hinglish' or 'Hindi', use the Devanagari script for pure Hindi words, but retain English words (e.g., 'booking,' 'service') in Roman script, maintaining a conversational Hinglish style. Do NOT add extra context, just the translated prompt."},
            {"role": "user", "content": required_prompt}
        ]
        
        # Use the same fallback logic for high reliability
        llm_result = self.get_response_sync(messages, structured=False)
        
        if '"intent": "LLM_FAILURE"' in llm_result['content']:
            # Return the original English prompt as the ultimate fallback
            return required_prompt 
        
        return llm_result['content']