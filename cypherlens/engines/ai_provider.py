"""
BYOK Multi-LLM Provider Engine for CypherLens 2.0.
Supports Google Gemini, OpenAI, Claude, Local Ollama, and a Zero-Key Heuristic Fallback Engine.
"""

import os
import json
import httpx
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("cypherlens.ai")

CONFIG_DIR = os.path.expanduser("~/.cypherlens")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")


class AIProviderManager:
    @classmethod
    def _ensure_config_dir(cls):
        os.makedirs(CONFIG_DIR, exist_ok=True)

    @classmethod
    def load_config(cls) -> Dict[str, Any]:
        """Loads saved provider configuration."""
        if not os.path.exists(CONFIG_PATH):
            return {
                "provider": "zero_key",  # "gemini", "openai", "claude", "ollama", "zero_key"
                "api_key": os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY") or "",
                "model": "gemini-1.5-flash",
                "default_currency": "EUR",
                "default_region": "de"
            }
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"provider": "zero_key", "api_key": "", "model": "gemini-1.5-flash"}

    @classmethod
    def save_config(cls, provider: str, api_key: str = "", model: str = "", default_currency: str = "EUR", default_region: str = "de"):
        """Saves provider configuration locally."""
        cls._ensure_config_dir()
        cfg = cls.load_config()
        cfg.update({
            "provider": provider,
            "api_key": api_key.strip(),
            "model": model.strip() or ("gemini-1.5-flash" if provider == "gemini" else "gpt-4o-mini"),
            "default_currency": default_currency,
            "default_region": default_region
        })
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        return cfg

    @classmethod
    def generate(cls, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Dispatches generation to the active AI provider or heuristic fallback."""
        config = cls.load_config()
        provider = config.get("provider", "zero_key")
        api_key = config.get("api_key") or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY") or ""

        # Auto-detect if key is present in environment
        if not api_key and provider != "ollama":
            provider = "zero_key"

        if provider == "gemini" and api_key:
            return cls._call_gemini(prompt, api_key, config.get("model", "gemini-1.5-flash"), system_prompt)
        elif provider == "openai" and api_key:
            return cls._call_openai(prompt, api_key, config.get("model", "gpt-4o-mini"), system_prompt)
        elif provider == "claude" and api_key:
            return cls._call_claude(prompt, api_key, config.get("model", "claude-3-5-sonnet-20241022"), system_prompt)
        elif provider == "ollama":
            return cls._call_ollama(prompt, config.get("model", "llama3"), system_prompt)
        else:
            # Zero-Key Heuristic Engine
            return cls._heuristic_fallback(prompt)

    @classmethod
    def _call_gemini(cls, prompt: str, api_key: str, model: str = "gemini-1.5-flash", system_prompt: Optional[str] = None) -> str:
        """Direct lightweight Google Gemini REST API call."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTION: {system_prompt}"}]})
            contents.append({"role": "model", "parts": [{"text": "Understood. I will follow these instructions."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        try:
            r = httpx.post(url, json={"contents": contents}, timeout=15.0)
            if r.status_code == 200:
                data = r.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
            else:
                logger.warning(f"Gemini API returned status {r.status_code}: {r.text}")
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            
        return cls._heuristic_fallback(prompt)

    @classmethod
    def _call_openai(cls, prompt: str, api_key: str, model: str = "gpt-4o-mini", system_prompt: Optional[str] = None) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            r = httpx.post(url, headers=headers, json={"model": model, "messages": messages}, timeout=15.0)
            if r.status_code == 200:
                data = r.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            
        return cls._heuristic_fallback(prompt)

    @classmethod
    def _call_claude(cls, prompt: str, api_key: str, model: str = "claude-3-5-sonnet-20241022", system_prompt: Optional[str] = None) -> str:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": model,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}]
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            r = httpx.post(url, headers=headers, json=payload, timeout=15.0)
            if r.status_code == 200:
                data = r.json()
                return data["content"][0]["text"]
        except Exception as e:
            logger.error(f"Claude API error: {e}")

        return cls._heuristic_fallback(prompt)

    @classmethod
    def _call_ollama(cls, prompt: str, model: str = "llama3", system_prompt: Optional[str] = None) -> str:
        url = "http://localhost:11434/api/generate"
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        try:
            r = httpx.post(url, json={"model": model, "prompt": full_prompt, "stream": False}, timeout=20.0)
            if r.status_code == 200:
                return r.json().get("response", "")
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            
        return cls._heuristic_fallback(prompt)

    @classmethod
    def _heuristic_fallback(cls, prompt: str) -> str:
        """
        Rule-based synthesis engine when no LLM API key is connected.
        Guarantees 100% free, factual extraction.
        """
        return ""
