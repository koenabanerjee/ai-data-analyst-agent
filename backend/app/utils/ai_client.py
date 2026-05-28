"""
app/utils/ai_client.py — unified AI client (Gemini primary, OpenAI fallback)
"""
from __future__ import annotations

import json
from typing import Any

import google.generativeai as genai
import httpx

from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class AIClient:
    """Thin async wrapper around Gemini (primary) and OpenAI (fallback)."""

    def __init__(self) -> None:
        self.provider = settings.ai_provider
        self._openai_url = "https://api.openai.com/v1/chat/completions"

        # Configure Gemini once
        if settings.google_api_key:
            genai.configure(api_key=settings.google_api_key)

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        response_format: str = "text",  # "text" | "json"
    ) -> str:

        if self.provider == "gemini" and settings.google_api_key:
            return await self._gemini(
                system_prompt,
                user_prompt,
                temperature,
                max_tokens,
                response_format,
            )

        if settings.openai_api_key:
            return await self._openai(
                system_prompt,
                user_prompt,
                temperature,
                max_tokens,
                response_format,
            )

        raise RuntimeError(
            "No AI API key configured. Set GOOGLE_API_KEY or OPENAI_API_KEY in .env"
        )

    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        """Convenience wrapper that always returns parsed JSON."""

        raw = await self.complete(
            system_prompt,
            user_prompt,
            temperature=temperature,
            response_format="json",
        )

        raw = raw.strip()

        # Strip markdown code blocks if model wraps response
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        return json.loads(raw.strip())

    # ── Gemini ─────────────────────────────────────────────

    async def _gemini(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        response_format: str,
    ) -> str:

        prompt = f"""
System:
{system_prompt}

User:
{user_prompt}
"""

        if response_format == "json":
            prompt += "\n\nRespond ONLY with valid JSON. No markdown, no explanation."

        try:
            model = genai.GenerativeModel("gemini-2.5-flash")

            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )

            return response.text

        except Exception as exc:
            logger.error("Gemini API error: %s", exc)
            raise RuntimeError(f"Gemini failed: {str(exc)}") from exc

    # ── OpenAI ─────────────────────────────────────────────

    async def _openai(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        response_format: str,
    ) -> str:

        payload: dict[str, Any] = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format == "json":
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                self._openai_url,
                json=payload,
                headers=headers,
            )

            resp.raise_for_status()
            data = resp.json()

        return data["choices"][0]["message"]["content"]


# Singleton
_client: AIClient | None = None


def get_ai_client() -> AIClient:
    global _client

    if _client is None:
        _client = AIClient()

    return _client