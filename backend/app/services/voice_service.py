# voice_service.py - [MOD] text_to_speech(): Chatterbox primary, ElevenLabs fallback
# backend/app/services/voice_service.py
"""text_to_speech(): Chatterbox primary, ElevenLabs fallback. Returns base64.

Per the v10 voice scope: TTS is the self-hosted fine-tuned Chatterbox model
(POST {CHATTERBOX_TTS_URL} {"text": ...} -> MP3 bytes). ElevenLabs is a
config-flag fallback ONLY (TTS_FALLBACK=elevenlabs + ELEVENLABS_API_KEY set) —
never the default. STT never touches the backend (browser Web Speech API).

If both providers are unavailable this returns (None, None) and the caller
proceeds text-only — the frontend falls back to browser speechSynthesis.
Voice must never break the interview.
"""
from __future__ import annotations

import base64
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_TIMEOUT = 15.0
_ELEVENLABS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
_ELEVENLABS_DEFAULT_VOICE = "21m00Tcm4TlvDq8ikWAM"  # "Rachel", free tier


def _cfg(name: str, default: str = "") -> str:
    return str(getattr(settings, name, default) or default)


async def _chatterbox(text: str) -> bytes | None:
    url = _cfg("CHATTERBOX_TTS_URL")
    if not url:
        return None
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(url, json={"text": text})
            if resp.status_code == 200 and resp.content:
                return resp.content  # MP3 bytes
    except Exception as exc:  # noqa: BLE001 — any failure => try fallback
        logger.warning("Chatterbox TTS failed: %s", exc)
    return None


async def _elevenlabs(text: str) -> bytes | None:
    if _cfg("TTS_FALLBACK").lower() != "elevenlabs":
        return None
    api_key = _cfg("ELEVENLABS_API_KEY")
    if not api_key:
        return None
    voice_id = _cfg("ELEVENLABS_VOICE_ID", _ELEVENLABS_DEFAULT_VOICE)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                _ELEVENLABS_URL.format(voice_id=voice_id),
                headers={"xi-api-key": api_key,
                         "Content-Type": "application/json"},
                json={"text": text,
                      "model_id": "eleven_multilingual_v2",
                      "voice_settings": {"stability": 0.5,
                                          "similarity_boost": 0.75}},
            )
            if resp.status_code == 200 and resp.content:
                return resp.content
    except Exception as exc:  # noqa: BLE001
        logger.warning("ElevenLabs TTS failed: %s", exc)
    return None


async def text_to_speech(text: str) -> tuple[str | None, str | None]:
    """Return (audio_base64, provider) or (None, None) if voice is unavailable.

    Long texts are truncated to keep latency + character budgets sane; the full
    text is always delivered in the JSON response regardless.
    """
    text = (text or "").strip()
    if not text:
        return None, None
    if len(text) > 900:
        text = text[:900]

    audio = await _chatterbox(text)
    if audio:
        return base64.b64encode(audio).decode("ascii"), "chatterbox"

    audio = await _elevenlabs(text)
    if audio:
        return base64.b64encode(audio).decode("ascii"), "elevenlabs"

    return None, None