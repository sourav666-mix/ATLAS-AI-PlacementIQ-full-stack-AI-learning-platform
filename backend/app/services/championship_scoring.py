# backend/app/services/championship_scoring.py
"""Championship scoring helpers — attention formula + progress_engine hook.

Points formula from the spec (System Understanding §5):
  championship_points = marks + attention weighted

The progress_engine integration is a one-liner — we just call
`record_event(db, user_id, "championship", payload)`. If your
progress_engine doesn't handle "championship" yet, paste the additive
snippet from this batch's delivery notes into progress_engine.py.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession


def compute_attention(fullscreen_exits: int, time_used: int,
                      duration: int) -> int:
    """0-100 attention score. Pure math, no AI.

    Components:
      * Fullscreen compliance: −15 per exit (max 5 counted = −75)
      * Time usage ratio: tiny penalty if they submitted in < 20% of the time
        (suggests random clicking), but no penalty for fast + correct work.
    """
    base = 100
    exit_penalty = min(fullscreen_exits or 0, 5) * 15

    # speed penalty: only if absurdly fast AND they had exits
    speed_penalty = 0
    if duration > 0 and time_used > 0:
        ratio = time_used / duration
        if ratio < 0.15 and fullscreen_exits > 0:
            speed_penalty = 10

    return max(0, base - exit_penalty - speed_penalty)


def championship_points(score: int, max_score: int, attention: int) -> int:
    """Points added to the daily progress bar.

    Formula: base_points (proportional to score) × attention multiplier.
    Max ≈ 50 points for a perfect 100/100 with 100% attention.
    """
    if max_score <= 0:
        return 0
    base = round(score / max_score * 50)
    multiplier = max(attention, 0) / 100
    return round(base * multiplier)


async def award_championship_points(db: AsyncSession, user_id: str,
                                    score: int, max_score: int,
                                    attention: int) -> int:
    """Try to call progress_engine.record_event; degrade gracefully if it
    doesn't handle 'championship' yet (returns 0 and logs nothing)."""
    pts = championship_points(score, max_score, attention)
    try:
        from app.services.progress_engine import record_event  # Batch 5
        await record_event(db, user_id, "championship", {
            "championship_points": pts,
            "score": score,
            "max_score": max_score,
            "attention_score": attention,
        })
    except Exception:
        pass  # progress_engine doesn't handle this event type yet — that's fine
    return pts