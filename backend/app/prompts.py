# backend/app/prompts.py
"""
Authoring prompt templates for the v12 SkillPath seeders.

Kept in one file so all authoring copy (Learn Cards + practice question banks)
lives in a single place. The seeders format these with .format(...) and send
them to the AI gateway, expecting STRICT JSON back.
"""

LEARN_CARD_SYSTEM = (
    "You are a senior CS educator authoring Type-A learning content for ATLAS AI, "
    "a placement-prep platform for Indian B.Tech students. Return STRICT JSON only, "
    "no prose, no code fences."
)

LEARN_CARD_PROMPT = (
    "Write a Learn Card for the subtopic '{subtopic}' (parent topic: '{topic}', "
    "domain: '{domain}'). Return JSON with keys: "
    '{{"what_is_it": str, "when_to_use": str, "how_to_use": str, '
    '"examples": [5 items of {{"prompt": str, "solution": str}}], '
    '"visualization_config": {{"type": "flow_diagram|interactive_plot|table|code_trace", '
    '"params": []}} }}. Exactly 5 worked examples. Keep each field tight and student-friendly."'
)

PRACTICE_QUESTION_SYSTEM = (
    "You author practice question banks for ATLAS AI. Return STRICT JSON only, "
    "no prose, no code fences."
)

PRACTICE_QUESTION_PROMPT = (
    "Create ONE {tier}-difficulty practice question for subtopic '{subtopic}' "
    "(domain: '{domain}'), position {position} of 25. Include EXACTLY 2 worked examples. "
    "Return JSON: {{\"statement\": str, \"constraints\": str, "
    "\"question_kind\": \"text|code|math|sql\", \"model_answer\": str, "
    "\"why_explanation\": str, \"how_explanation\": str, \"example\": str, "
    "\"common_mistakes\": str, "
    "\"examples\": [2 items of {{\"prompt\": str, \"solution\": str}}]}}"
)
# --- v12 SkillPath Reforged -------------------------------------------------

GENERATE_QUESTION_SYSTEM = (
    "You are a placement-preparation question author for Indian B.Tech "
    "students. You write ONE practice question in strict JSON. Return ONLY "
    "JSON, no prose, no markdown fences."
)

GENERATE_QUESTION_USER = (
    "Write one {difficulty} practice question for topic '{topic}', "
    "subtopic '{subtopic}'.\n"
    "Return ONLY this JSON shape:\n"
    "{{\n"
    '  "question": "clear task tied to the subtopic",\n'
    '  "examples": [ {{"input":"","output":"","why":""}}, '
    '{{"input":"","output":"","why":""}} ],\n'
    '  "question_kind": "code | text | sql | math",\n'
    '  "starter_code": "only if question_kind is code, else empty string",\n'
    '  "model_solution": "reference answer with reasoning",\n'
    '  "why_how": "why this approach + how to derive it",\n'
    '  "common_mistakes": ["...", "..."]\n'
    "}}\n"
    "Exactly 2 examples. Interview-realistic, unambiguous, self-contained."
)

ANALYZE_ATTEMPT_SYSTEM = (
    "You are a strict-but-fair coding interviewer analyzing a student's "
    "attempt. Be lenient on style, strict on concept. Return ONLY JSON, "
    "no prose, no markdown fences."
)

ANALYZE_ATTEMPT_USER = (
    "QUESTION ({question_kind}):\n{question}\n\n"
    "MODEL SOLUTION:\n{model_solution}\n\n"
    "STUDENT ATTEMPT:\n{student_attempt}\n\n"
    "STUDENT RUN OUTPUT (from their local kernel):\n{run_output}\n\n"
    "Return ONLY this JSON shape:\n"
    "{{\n"
    '  "score": 0-100,\n'
    '  "verdict": "correct | partially_correct | incorrect",\n'
    '  "good": ["what the student did well", "..."],\n'
    '  "missing": ["what was missed or wrong", "..."],\n'
    '  "walkthrough": "the model solution explained step by step",\n'
    '  "next_hint": "one concrete next step for this student"\n'
    "}}"
)

# --- v12 Live Lab Pro --------------------------------------------------

LABPRO_COPILOT_SYSTEM = (
    "You are a coding copilot inside a student's live lab. Be concise and "
    "educational. Return ONLY JSON, no prose, no markdown fences."
)

LABPRO_COPILOT_USER = (
    "ACTION: {action}\nENVIRONMENT: {env}\nGOAL: {goal}\n\n"
    "CODE:\n{code}\n\nERROR (if any):\n{error_text}\n\n"
    "Return ONLY this JSON shape:\n"
    "{{\n"
    '  "explanation": "plain-English explanation tuned to a student",\n'
    '  "suggestion": "the single best next step",\n'
    '  "fixed_code": "corrected code ONLY if action is fix, else null"\n'
    "}}"
)


# --- v12 seeding pipeline ------------------------------------------------

SEED_QUESTION_SYSTEM = (
    "You are a seed question author building a permanent practice bank "
    "for Indian B.Tech placement preparation. Return ONLY JSON."
)

SEED_QUESTION_USER = (
    "Write one {difficulty} {kind} practice question for topic '{topic}', "
    "subtopic '{subtopic}'.\n\n"
    "QUESTIONS ALREADY IN THIS SET (yours MUST test something different - "
    "a different operation, concept, edge case or scenario):\n{existing}\n\n"
    "Return ONLY this JSON shape:\n"
    "{{\n"
    '  "question": "...", "examples": [{{"input":"","output":"","why":""}},'
    '{{"input":"","output":"","why":""}}],\n'
    '  "question_kind": "code | text | sql | math",\n'
    '  "starter_code": "only if code, else empty",\n'
    '  "model_solution": "...", "why_how": "...",\n'
    '  "common_mistakes": ["...", "..."]\n'
    "}}"
)

SEED_LEARN_SYSTEM = (
    "You are a learn explainer author for placement preparation. "
    "Return ONLY JSON."
)

SEED_LEARN_USER = (
    "Write the Learn explainer for topic '{topic}', subtopic '{subtopic}' "
    "({kind}).\nReturn ONLY this JSON shape:\n"
    "{{\n"
    '  "what_it_is": "...", "when_to_use": "...", "how_to_use": "...",\n'
    '  "examples": [ exactly 5 of {{"title":"","code":"","output":"","why":""}} ]\n'
    "}}"
)
