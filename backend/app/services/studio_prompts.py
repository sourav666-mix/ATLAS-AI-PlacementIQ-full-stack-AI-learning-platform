# backend/app/services/studio_prompts.py
"""AI Interview Studio — prompt builders.

Kept in a dedicated module (instead of another additive edit to prompts.py) so
your most-edited hot file stays untouched this batch. Three prompts:

  question_set()  — ONE call at session start, generates the whole set
  turn_eval()     — ONE call per answered turn: score + feedback + follow-up decision
  final_report()  — ONE call at finish: strengths/weaknesses/summary
"""
from __future__ import annotations

import json

QUESTION_SET_SYSTEM = (
    "You are a professional technical interviewer for Indian B.Tech campus "
    "placements. You speak questions aloud, so keep each question a single "
    "clear spoken sentence or two — no code blocks, no bullet lists. "
    "Respond with STRICT JSON only, no prose, no markdown fences."
)


def question_set(domain_name: str, focus: str, level: str, count: int) -> tuple[str, str]:
    message = (
        f"Generate exactly {count} interview questions for a live spoken interview.\n"
        f"Domain: {domain_name}\n"
        f"Focus areas: {focus}\n"
        f"Difficulty: {level}\n\n"
        "Rules: each question must be answerable verbally in 1-3 minutes; mix "
        "conceptual, applied, and one behavioral question; order from warm-up "
        "to hardest.\n\n"
        'Return: {"questions": ["question 1", "question 2", ...]}\n'
        "Output JSON only."
    )
    return QUESTION_SET_SYSTEM, message


TURN_SYSTEM = (
    "You are a live technical interviewer evaluating a spoken answer that was "
    "transcribed by speech-to-text (expect minor transcription noise — do not "
    "penalize it). Be encouraging but honest. Respond with STRICT JSON only."
)


def turn_eval(domain_name: str, level: str, question: str,
              transcript: str, remaining: int) -> tuple[str, str]:
    message = (
        f"Domain: {domain_name} | Level: {level}\n"
        f"Question asked: {question}\n"
        f'Candidate\'s spoken answer (STT transcript): "{transcript}"\n'
        f"Questions remaining in the set: {remaining}\n\n"
        "Evaluate the answer and decide whether a short follow-up probe is "
        "warranted (only if the answer was interesting-but-incomplete AND "
        "remaining > 0; never more than one follow-up per question).\n\n"
        "Return JSON:\n"
        "{\n"
        '  "score": 0-10,\n'
        '  "feedback": "2-3 spoken sentences: what was good, what was missing",\n'
        '  "model_answer_hint": "one-sentence hint at the ideal answer",\n'
        '  "ask_follow_up": true|false,\n'
        '  "follow_up_question": "the probe (empty string if ask_follow_up is false)",\n'
        '  "weakness_tag": "one short skill tag if the answer was weak, else empty, '
        'e.g. \\"SQL joins\\", \\"system design\\", \\"communication\\""\n'
        "}\n"
        "Output JSON only."
    )
    return TURN_SYSTEM, message


REPORT_SYSTEM = (
    "You are writing the final report of a spoken mock interview. Be specific, "
    "constructive, and reference the candidate's actual answers. "
    "Respond with STRICT JSON only."
)


def final_report(domain_name: str, level: str,
                 turns: list[dict]) -> tuple[str, str]:
    compact = [
        {"q": t.get("question", "")[:120],
         "score": t.get("score"),
         "weak": t.get("weakness_tag", "")}
        for t in turns
    ]
    message = (
        f"Domain: {domain_name} | Level: {level}\n"
        f"Per-question results: {json.dumps(compact)}\n\n"
        "Write the final report. Return JSON:\n"
        "{\n"
        '  "strengths": ["2-4 specific strengths"],\n'
        '  "weaknesses": ["2-4 specific, skill-named weaknesses"],\n'
        '  "summary": "3-4 sentence overall narrative addressed to the candidate"\n'
        "}\n"
        "Output JSON only."
    )
    return REPORT_SYSTEM, message