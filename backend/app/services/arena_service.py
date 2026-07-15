# arena_service.py - [NEW] serve bank-first; generate-once-cache-forever
# backend/app/services/arena_service.py
"""
Code Arena Pro — hybrid DSA bank (System Understanding: serve-from-bank,
generate-once-cache).

* Browsing/serving a problem is a pure DB read (hidden tests + optimal solution
  are never exposed).
* submit() runs the code (code_runner), does an AI review (fallback-safe), and
  awards points ONLY on the FIRST passing submission — via progress_engine
  (Easy 5 / Medium 10 / Advanced 20). This feeds coding_strength in the profile bar.
"""
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.arena import ArenaProblem, ArenaSubmission
from app.services import ai_provider_router, code_runner, prompts, progress_engine
from app.services.progress_engine import ARENA_POINTS


# --- pure reads -------------------------------------------------------------
async def list_problems(
    db: AsyncSession, category: Optional[str] = None, difficulty: Optional[str] = None, limit: int = 50
) -> list[ArenaProblem]:
    q = select(ArenaProblem).where(ArenaProblem.review_status == "published")
    if category:
        q = q.where(ArenaProblem.category == category)
    if difficulty:
        q = q.where(ArenaProblem.difficulty == difficulty)
    q = q.order_by(ArenaProblem.created_at).limit(limit)
    return list((await db.execute(q)).scalars().all())


async def get_problem(db: AsyncSession, problem_id: str) -> Optional[ArenaProblem]:
    return await db.get(ArenaProblem, problem_id)


def public_view(problem: ArenaProblem) -> dict:
    """Problem detail with hidden tests + optimal solution stripped out."""
    tc = problem.test_cases_json or {}
    visible = tc.get("visible", [])
    return {
        "id": problem.id,
        "category": problem.category,
        "difficulty": problem.difficulty,
        "title": problem.title,
        "topic": problem.topic,
        "pattern_tag": problem.pattern_tag,
        "statement": problem.statement,
        "examples": problem.examples_json or [],
        "constraints": problem.constraints_json or [],
        "hints": problem.hints_json or [],
        "starter_code": problem.starter_code_json or {},
        "visible_tests": visible,
    }


async def next_problem(
    db: AsyncSession, user_id: str, category: str, difficulty: str
) -> Optional[ArenaProblem]:
    """Serve the next unsolved bank problem; generate+cache one if the cell is empty."""
    passed_subq = (
        select(ArenaSubmission.problem_id)
        .where(ArenaSubmission.user_id == user_id, ArenaSubmission.passed.is_(True))
        .subquery()
    )
    prob = (
        await db.execute(
            select(ArenaProblem)
            .where(
                ArenaProblem.category == category,
                ArenaProblem.difficulty == difficulty,
                ArenaProblem.review_status == "published",
                ArenaProblem.id.not_in(select(passed_subq.c.problem_id)),
            )
            .order_by(ArenaProblem.created_at)
            .limit(1)
        )
    ).scalar_one_or_none()
    if prob is not None:
        return prob

    # cell exhausted for this user -> try to generate one (cached with source='auto')
    generated = await _generate_problem(db, category, difficulty)
    if generated is not None:
        return generated

    # no AI available: fall back to any problem in the cell (allow replay)
    return (
        await db.execute(
            select(ArenaProblem)
            .where(ArenaProblem.category == category, ArenaProblem.difficulty == difficulty)
            .order_by(ArenaProblem.created_at)
            .limit(1)
        )
    ).scalar_one_or_none()


def _clip(value, n: int) -> str:
    """Clip AI-generated text to a column's max length (defensive vs DataError)."""
    return str(value)[:n]


async def _generate_problem(db: AsyncSession, category: str, difficulty: str) -> Optional[ArenaProblem]:
    """Generate ONE problem via AI and cache it. Returns None if AI is unavailable."""
    try:
        text = await ai_provider_router.complete(
            prompts.arena_gen_system(), prompts.arena_gen_user(category, difficulty)
        )
        data = ai_provider_router.parse_json(text)
        prob = ArenaProblem(
            category=category,
            difficulty=difficulty,
            title=_clip(data.get("title", "Generated Problem"), 200),
            statement=str(data.get("statement", "")),
            examples_json=data.get("examples", []),
            constraints_json=data.get("constraints", []),
            hints_json=data.get("hints", []),
            starter_code_json=data.get("starter_code", {}),
            test_cases_json=data.get("test_cases", {"entry_point": "solution", "visible": [], "hidden": []}),
            optimal_solution=str(data.get("optimal_solution", "")),
            complexity=_clip(data.get("complexity", ""), 255),
            source="auto",
            review_status="published",
        )
        db.add(prob)
        await db.commit()
        await db.refresh(prob)
        return prob
    except Exception:
        # Never leave the session in a poisoned (pending-rollback) state — the
        # caller falls back to a plain read after this returns None.
        await db.rollback()
        return None


# --- run (visible tests only; no points, no AI, no DB write) ----------------
async def run_visible(db: AsyncSession, problem_id: str, language: str, code: str) -> dict:
    """Run ONLY the visible test cases for fast feedback. No scoring, no AI."""
    problem = await db.get(ArenaProblem, problem_id)
    if problem is None:
        raise ValueError("Problem not found.")
    if language.lower() != "python":
        raise ValueError("Only Python is supported currently.")

    tc = problem.test_cases_json or {}
    entry = tc.get("entry_point", "solution")
    visible = tc.get("visible", []) or []
    if not visible:
        return {"cases": [], "passed_count": 0, "total": 0, "runtime_ms": 0}

    run = await code_runner.run_python(code, entry, visible)
    if run.get("compile_error"):
        return {"error": run["compile_error"], "error_type": "Compile error",
                "runtime_ms": run["runtime_ms"]}

    results = run["results"]
    cases = []
    for i, vc in enumerate(visible):
        r = results[i] if i < len(results) else {}
        actual = r.get("got") if r.get("got") is not None else r.get("error")
        cases.append({
            "input": vc.get("input"),
            "expected": vc.get("output"),
            "actual": actual,
            "passed": bool(r.get("passed")),
        })
    return {
        "cases": cases,
        "passed_count": sum(1 for c in cases if c["passed"]),
        "total": len(cases),
        "runtime_ms": run["runtime_ms"],
    }


# --- submission -------------------------------------------------------------
async def submit(db: AsyncSession, user_id: str, problem_id: str, language: str, code: str) -> dict:
    problem = await db.get(ArenaProblem, problem_id)
    if problem is None:
        raise ValueError("Problem not found.")
    if language.lower() != "python":
        raise ValueError("Only Python is supported currently.")

    tc = problem.test_cases_json or {}
    entry = tc.get("entry_point", "solution")
    visible = tc.get("visible", []) or []
    hidden = tc.get("hidden", []) or []
    all_cases = visible + hidden

    run = await code_runner.run_python(code, entry, all_cases)
    results = run["results"]
    total = len(results)
    tests_passed = sum(1 for r in results if r.get("passed"))
    passed = total > 0 and tests_passed == total

    # only the visible cases are shown back to the student
    visible_results = [
        {"index": i, "passed": results[i].get("passed", False), "error": results[i].get("error")}
        for i in range(min(len(visible), len(results)))
    ]

    # first-pass points only (anti-farming)
    points = 0
    if passed:
        already_passed = (
            await db.execute(
                select(func.count()).select_from(ArenaSubmission).where(
                    ArenaSubmission.user_id == user_id,
                    ArenaSubmission.problem_id == problem_id,
                    ArenaSubmission.passed.is_(True),
                )
            )
        ).scalar() or 0
        if not already_passed:
            points = ARENA_POINTS.get(problem.difficulty, 0)

    review = await _review_code(problem, code, passed)

    sub = ArenaSubmission(
        user_id=user_id,
        problem_id=problem_id,
        language="python",
        code=code,
        passed=passed,
        runtime_ms=run["runtime_ms"],
        ai_review_json=review,
        points_awarded=points,
    )
    db.add(sub)
    await db.flush()

    if points > 0:
        # awards daily arena points + recomputes profile bar (commits)
        await progress_engine.record_event(db, user_id, "arena_solved", {"difficulty": problem.difficulty})
    else:
        await progress_engine.recompute_profile_bar(db, user_id)
        await db.commit()

    return {
        "passed": passed,
        "tests_passed": tests_passed,
        "total_tests": total,
        "visible_results": visible_results,
        "runtime_ms": run["runtime_ms"],
        "points_awarded": points,
        "ai_review": review,
        "compile_error": run.get("compile_error"),
    }


async def _review_code(problem: ArenaProblem, code: str, passed: bool) -> dict:
    try:
        text = await ai_provider_router.complete(
            prompts.arena_review_system(),
            prompts.arena_review_user(problem.title or "", problem.statement or "", code, passed),
        )
        data = ai_provider_router.parse_json(text)
        return {
            "summary": str(data.get("summary", "")),
            "complexity": str(data.get("complexity", "")),
            "suggestions": list(data.get("suggestions", [])),
        }
    except Exception:
        return {
            "summary": "All tests passed. Clean work!" if passed else "Some tests failed — check edge cases and constraints.",
            "complexity": problem.complexity or "",
            "suggestions": [],
        }


__all__ = ["list_problems", "get_problem", "public_view", "next_problem", "run_visible", "submit"]