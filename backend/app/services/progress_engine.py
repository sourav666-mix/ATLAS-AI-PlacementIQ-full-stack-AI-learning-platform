# progress_engine.py - [NEW] THE single scoring spine: all points + profile bar (pure math)
# backend/app/services/progress_engine.py
"""
THE SCORING SPINE — the single, pure-math place where all points are computed.

No AI. No module invents its own scoring; every point-awarding service calls
record_event(). This is what keeps the Profile Improvement Bar honest and the
leaderboard fair (System Understanding §5).

Formulas (exact):
    daily_points = attempts*2 + avg_score*1.5 + topics_completed*15
                 + arena_points + interview_points + championship_points
                 + min(streak_days, 10)*2

    profile_bar  = 25% skill_mastery + 20% assessment_history + 20% coding_strength
                 + 15% interview_readiness + 10% resume_completeness + 10% consistency

Rules honored here:
    * first-attempt scores only count toward mastery (handled in practice_service);
    * a per-module daily cap prevents grinding one feature;
    * streak += 1 once per active calendar day, and RESETS TO 1 after a missed day.
"""
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.arena import ArenaProblem, ArenaSubmission
from app.models.daily_activity import DailyActivity
from app.models.interview_studio import InterviewStudioSession
from app.models.resume_doc import ResumeDocument
from app.models.session import AptitudeSession, MockSession
from app.models.skill_progress import SkillRadarScore
from app.models.user import User

# --- tunable constants (weights are per-spec; caps/sub-scores are tunable) ----
ARENA_POINTS = {"Easy": 5, "Medium": 10, "Advanced": 20}
CODING_WEIGHT = {"Easy": 1, "Medium": 2, "Advanced": 3}

# per-module daily caps (points) — anti-grind
DAILY_CAPS = {"arena": 120, "interview": 60, "championship": 200}

# profile-bar component weights (MUST stay per the spec)
BAR_WEIGHTS = {
    "skill_mastery": 0.25,
    "assessment_history": 0.20,
    "coding_strength": 0.20,
    "interview_readiness": 0.15,
    "resume_completeness": 0.10,
    "consistency": 0.10,
}


def _utc_today() -> date:
    return datetime.now(timezone.utc).date()


# ============================================================================
# record_event — the ONE public entry point every other service calls
# ============================================================================
async def record_event(
    db: AsyncSession, user_id: str, event_type: str, payload: Optional[dict] = None
) -> DailyActivity:
    """
    Apply one scoring event to today's row, recompute daily_points, and refresh
    the user's profile bar. Commits once.

    event_type / payload:
      "question_attempted"  -> {"score": 0-10, "is_first_attempt": bool}
      "topic_completed"     -> {}
      "arena_solved"        -> {"difficulty": "Easy|Medium|Advanced"}
      "interview_completed" -> {"score": 0-100}
      "championship_scored" -> {"points": int}   # already marks+attention weighted
    """
    payload = payload or {}
    row = await _get_or_create_today(db, user_id)

    if event_type == "question_attempted":
        score = float(payload.get("score", 0))
        prev = row.questions_attempted
        row.questions_attempted = prev + 1
        # running mean of scored attempts today
        row.avg_score = ((row.avg_score * prev) + score) / row.questions_attempted

    elif event_type == "topic_completed":
        row.topics_completed += 1

    elif event_type == "arena_solved":
        pts = ARENA_POINTS.get(payload.get("difficulty", ""), 0)
        row.arena_points = min(row.arena_points + pts, DAILY_CAPS["arena"])

    elif event_type == "interview_completed":
        score = float(payload.get("score", 0))          # 0-100
        pts = round(15 * (score / 100.0))                # 15 * score_weight
        row.interview_points = min(row.interview_points + pts, DAILY_CAPS["interview"])

    elif event_type == "championship_scored":
        pts = int(payload.get("points", 0))
        row.championship_points = min(row.championship_points + pts, DAILY_CAPS["championship"])

    else:
        raise ValueError(f"Unknown event_type: {event_type!r}")

    row.daily_points = _recompute_daily_points(row)
    await db.flush()

    await recompute_profile_bar(db, user_id)  # keeps users.profile_bar_score fresh
    await db.commit()
    await db.refresh(row)
    return row


def _recompute_daily_points(row: DailyActivity) -> int:
    total = (
        row.questions_attempted * 2
        + row.avg_score * 1.5
        + row.topics_completed * 15
        + row.arena_points
        + row.interview_points
        + row.championship_points
        + min(row.streak_days, 10) * 2
    )
    return int(round(total))


async def _get_or_create_today(db: AsyncSession, user_id: str) -> DailyActivity:
    today = _utc_today()
    row = (
        await db.execute(
            select(DailyActivity).where(
                DailyActivity.user_id == user_id,
                DailyActivity.activity_date == today,
            )
        )
    ).scalar_one_or_none()
    if row is not None:
        return row

    streak = await _compute_streak(db, user_id, today)
    row = DailyActivity(user_id=user_id, activity_date=today, streak_days=streak)
    db.add(row)
    await db.flush()
    return row


async def _compute_streak(db: AsyncSession, user_id: str, today: date) -> int:
    """+1 if there was activity yesterday, else reset to 1 (never 0)."""
    yesterday = today - timedelta(days=1)
    prev = (
        await db.execute(
            select(DailyActivity.streak_days).where(
                DailyActivity.user_id == user_id,
                DailyActivity.activity_date == yesterday,
            )
        )
    ).scalar_one_or_none()
    return (prev + 1) if prev else 1


# ============================================================================
# profile bar (0-100 composite) — weighted per the spec
# ============================================================================
async def recompute_profile_bar(db: AsyncSession, user_id: str) -> int:
    components = {
        "skill_mastery": await _skill_mastery(db, user_id),
        "assessment_history": await _assessment_history(db, user_id),
        "coding_strength": await _coding_strength(db, user_id),
        "interview_readiness": await _interview_readiness(db, user_id),
        "resume_completeness": await _resume_completeness(db, user_id),
        "consistency": await _consistency(db, user_id),
    }
    bar = sum(BAR_WEIGHTS[k] * v for k, v in components.items())
    bar = int(round(max(0.0, min(100.0, bar))))

    user = await db.get(User, user_id)
    if user is not None:
        user.profile_bar_score = bar
        await db.flush()
    return bar


async def _skill_mastery(db: AsyncSession, user_id: str) -> float:
    avg = (
        await db.execute(
            select(func.avg(SkillRadarScore.score)).where(SkillRadarScore.user_id == user_id)
        )
    ).scalar()
    return float(avg or 0.0)


async def _assessment_history(db: AsyncSession, user_id: str) -> float:
    apt_avg = (
        await db.execute(
            select(func.avg(AptitudeSession.score)).where(
                AptitudeSession.user_id == user_id, AptitudeSession.status == "completed"
            )
        )
    ).scalar()
    mock_avg = (
        await db.execute(
            select(func.avg(MockSession.overall_score)).where(
                MockSession.user_id == user_id, MockSession.status == "completed"
            )
        )
    ).scalar()
    count = (
        await db.execute(
            select(func.count()).select_from(AptitudeSession).where(AptitudeSession.user_id == user_id)
        )
    ).scalar() or 0

    scores = [s for s in (apt_avg, mock_avg) if s is not None]
    if not scores:
        return 0.0
    base = sum(scores) / len(scores)                 # 0-100
    volume_factor = min(count / 10.0, 1.0)           # ramps up over ~10 sessions
    return float(base) * volume_factor


async def _coding_strength(db: AsyncSession, user_id: str) -> float:
    rows = (
        await db.execute(
            select(ArenaProblem.difficulty, func.count())
            .select_from(ArenaSubmission)
            .join(ArenaProblem, ArenaSubmission.problem_id == ArenaProblem.id)
            .where(ArenaSubmission.user_id == user_id, ArenaSubmission.passed.is_(True))
            .group_by(ArenaProblem.difficulty)
        )
    ).all()
    weighted = sum(CODING_WEIGHT.get(diff, 1) * n for diff, n in rows)
    return float(min(weighted * 5, 100))             # ~20 weighted solves -> 100


async def _interview_readiness(db: AsyncSession, user_id: str) -> float:
    avg = (
        await db.execute(
            select(func.avg(InterviewStudioSession.overall_score)).where(
                InterviewStudioSession.user_id == user_id
            )
        )
    ).scalar()
    return float(avg or 0.0)


async def _resume_completeness(db: AsyncSession, user_id: str) -> float:
    modes = set(
        (
            await db.execute(
                select(ResumeDocument.mode).where(ResumeDocument.user_id == user_id)
            )
        ).scalars().all()
    )
    if "built" in modes:
        return 100.0
    if "analyzed" in modes:
        return 50.0
    return 0.0


async def _consistency(db: AsyncSession, user_id: str) -> float:
    latest_streak = (
        await db.execute(
            select(DailyActivity.streak_days)
            .where(DailyActivity.user_id == user_id)
            .order_by(DailyActivity.activity_date.desc())
            .limit(1)
        )
    ).scalar() or 0
    week_ago = _utc_today() - timedelta(days=7)
    active_days = (
        await db.execute(
            select(func.count()).select_from(DailyActivity).where(
                DailyActivity.user_id == user_id,
                DailyActivity.activity_date >= week_ago,
                DailyActivity.questions_attempted > 0,
            )
        )
    ).scalar() or 0
    streak_part = min(latest_streak, 10) / 10.0 * 100.0
    week_part = active_days / 7.0 * 100.0
    return 0.5 * streak_part + 0.5 * week_part


# ============================================================================
# read model for GET /progress/summary
# ============================================================================
async def get_summary(db: AsyncSession, user_id: str) -> dict:
    today = _utc_today()
    today_row = (
        await db.execute(
            select(DailyActivity).where(
                DailyActivity.user_id == user_id, DailyActivity.activity_date == today
            )
        )
    ).scalar_one_or_none()

    radar = (
        await db.execute(
            select(SkillRadarScore).where(SkillRadarScore.user_id == user_id)
        )
    ).scalars().all()

    user = await db.get(User, user_id)
    latest_streak = today_row.streak_days if today_row else (
        (
            await db.execute(
                select(DailyActivity.streak_days)
                .where(DailyActivity.user_id == user_id)
                .order_by(DailyActivity.activity_date.desc())
                .limit(1)
            )
        ).scalar()
        or 0
    )

    return {
        "profile_bar_score": user.profile_bar_score if user else 0,
        "streak_days": latest_streak,
        "today_points": today_row.daily_points if today_row else 0,
        "today": today_row,
        "radar": radar,
    }


__all__ = ["record_event", "recompute_profile_bar", "get_summary"]