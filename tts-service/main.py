# FILE: tts-service/main.py
# BATCH 19 - Chatterbox TTS wrapper (v10 Guide §10): a tiny FastAPI service,
# POST /speak {text} -> MP3 bytes (WAV fallback if no mp3 encoder), /health
# for the backend's fallback flag. Lazy model load; clear 503 while loading
# fails so the backend flips to the ElevenLabs fallback cleanly.

from __future__ import annotations

import io
import logging
import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chatterbox-tts")

app = FastAPI(title="ATLAS Chatterbox TTS", version="1.0")
_model = None
_load_error = None


def _get_model():
    global _model, _load_error
    if _model is not None:
        return _model
    try:
        from chatterbox.tts import ChatterboxTTS
        device = os.getenv("TTS_DEVICE", "cpu")
        ckpt = os.getenv("TTS_CHECKPOINT", "")  # path to your fine-tuned ckpt
        _model = (ChatterboxTTS.from_local(ckpt, device=device) if ckpt
                  else ChatterboxTTS.from_pretrained(device=device))
        logger.info("Chatterbox loaded on %s (ckpt=%r)", device, ckpt or "hub")
        return _model
    except Exception as exc:
        _load_error = str(exc)
        logger.error("Chatterbox load failed: %s", exc)
        raise HTTPException(status_code=503,
                            detail=f"TTS model unavailable: {exc}")


class SpeakRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": _model is not None,
            "load_error": _load_error}


@app.post("/speak")
def speak(body: SpeakRequest):
    model = _get_model()
    try:
        import torch, torchaudio  # noqa: E401
        wav = model.generate(body.text)
        buf = io.BytesIO()
        try:
            torchaudio.save(buf, wav.cpu(), model.sr, format="mp3")
            media = "audio/mpeg"
        except Exception:
            buf = io.BytesIO()
            torchaudio.save(buf, wav.cpu(), model.sr, format="wav")
            media = "audio/wav"
        _ = torch
        return Response(content=buf.getvalue(), media_type=media)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("speak failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"TTS failed: {exc}")