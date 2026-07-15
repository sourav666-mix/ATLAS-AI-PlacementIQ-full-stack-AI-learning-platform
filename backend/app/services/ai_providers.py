# backend/app/services/ai_providers.py
"""
Individual AI provider callers. Each is an async function (system, user) -> str.

SDK/network imports are done INSIDE each function so the app boots even if a
given SDK isn't installed or a key isn't set — the router only ever calls the
providers that are actually configured.
"""
import asyncio

import httpx

from app.config import settings


async def groq_complete(system: str, user: str) -> str:
    from groq import AsyncGroq  # lazy import

    client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    resp = await client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.3,
        max_tokens=1024,
    )
    return resp.choices[0].message.content or ""


async def gemini_complete(system: str, user: str) -> str:
    import google.generativeai as genai  # lazy import

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(settings.GEMINI_MODEL, system_instruction=system)
    # google-generativeai is sync; run it off the event loop
    resp = await asyncio.to_thread(model.generate_content, user)
    return resp.text or ""


async def _openai_compatible(base_url: str, api_key: str, model: str, system: str, user: str) -> str:
    async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT) as client:
        r = await client.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.3,
            },
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"] or ""


async def cerebras_complete(system: str, user: str) -> str:
    return await _openai_compatible(
        settings.CEREBRAS_BASE_URL, settings.CEREBRAS_API_KEY, settings.CEREBRAS_MODEL, system, user
    )


async def sambanova_complete(system: str, user: str) -> str:
    return await _openai_compatible(
        settings.SAMBANOVA_BASE_URL, settings.SAMBANOVA_API_KEY, settings.SAMBANOVA_MODEL, system, user
    )


# name -> (caller, settings-attr holding the API key)
PROVIDERS = {
    "groq": (groq_complete, "GROQ_API_KEY"),
    "gemini": (gemini_complete, "GEMINI_API_KEY"),
    "cerebras": (cerebras_complete, "CEREBRAS_API_KEY"),
    "sambanova": (sambanova_complete, "SAMBANOVA_API_KEY"),
}

__all__ = ["PROVIDERS"]