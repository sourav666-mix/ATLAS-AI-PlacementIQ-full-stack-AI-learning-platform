# backend/app/schemas/skillpath_v12.py
"""
ATLAS AI 4.0 - v12 SkillPath Reforged: request/response schemas.

Mirrors the locked student flow (v12 spec Section 2):
  Domain cards -> Plan select -> Roadmap -> Learn -> Practice tabs ->
  Arena question -> AI analysis -> next question -> mastery.

The per-question shape is the LOCKED Section 6 format:
  question / examples[2] / difficulty / question_kind /
  model_solution / why_how / common_mistakes
(model_solution, why_how and common_mistakes are NEVER sent before the
 student submits - see ArenaQuestion vs AnalysisResult.)
"""

from typing import List, Optional, Literal

from pydantic import BaseModel, Field, ConfigDict


# ----------------------------------------------------------------------
# Step 1-2: Domain first, THEN plan
# ----------------------------------------------------------------------

class DomainCard(BaseModel):
    """One of the nine locked domain cards."""
    domain_id: Optional[str] = None          # DB id once registered
    key: str                                  # e.g. 'data_science'
    name: str
    tagline: str
    roles: List[str]
    example_companies: List[str]
    topic_count: int
    subtopic_sets: int
    question_bank: int                        # subtopic_sets * 25


class DomainListResponse(BaseModel):
    domains: List[DomainCard]


class SelectRequest(BaseModel):
    """Locked order: the domain key arrives WITH the plan only because the
    plan screen is shown strictly after the domain screen."""
    domain_key: str
    plan_months: Literal[3, 6, 9]


class SelectResponse(BaseModel):
    domain_id: str
    domain_key: str
    plan_months: int
    roadmap_ready: bool


# ----------------------------------------------------------------------
# Step 3: Roadmap + Live Lab view
# ----------------------------------------------------------------------

class RoadmapTopicCard(BaseModel):
    topic_id: str
    title: str
    item_order: int
    phase: str
    est_hours: int
    subtopic_total: int
    subtopics_mastered: int
    progress_pct: int = Field(ge=0, le=100)   # the progress ring
    status: Literal["locked", "current", "complete"]
    viz_kind: str                              # which interactive viz to mount


class RoadmapResponse(BaseModel):
    domain_id: str
    domain_key: str
    domain_name: str
    plan_months: int
    topics: List[RoadmapTopicCard]
    overall_pct: int = Field(ge=0, le=100)


# ----------------------------------------------------------------------
# Step 4: LEARN mode
# ----------------------------------------------------------------------

class WorkedExample(BaseModel):
    title: str
    code: str
    output: str
    why: str


class SubtopicExplainer(BaseModel):
    subtopic_id: str
    name: str
    what_it_is: str
    when_to_use: str
    how_to_use: str
    examples: List[WorkedExample]             # locked at five in Learn mode


class TopicLearnResponse(BaseModel):
    topic_id: str
    title: str
    overview: str
    viz_kind: str
    subtopics: List[SubtopicExplainer]


# ----------------------------------------------------------------------
# Steps 5-6: Practice button -> subtopic tabs
# ----------------------------------------------------------------------

class SubtopicTab(BaseModel):
    subtopic_id: str
    name: str
    tab_order: int
    answered: int
    correct: int
    bank_size: int
    mastered: bool                             # green tick
    mastery_pct: int = Field(ge=0, le=100)


class SubtopicTabsResponse(BaseModel):
    topic_id: str
    topic_title: str
    tabs: List[SubtopicTab]
    all_mastered: bool


# ----------------------------------------------------------------------
# Step 7: the subtopic Code Arena (question + exactly 2 worked examples)
# ----------------------------------------------------------------------

class ArenaExample(BaseModel):
    input: str
    output: str
    why: str


class ArenaQuestion(BaseModel):
    """What the student sees BEFORE answering. No model_solution here."""
    question_id: str
    subtopic_id: str
    position: int                              # 1-based index in the bank
    bank_size: int
    difficulty: Literal["basic", "medium", "advanced"]
    question_kind: Literal["code", "text", "sql", "math"]
    question: str
    examples: List[ArenaExample] = Field(min_length=2, max_length=2)
    starter_code: Optional[str] = None         # only for question_kind='code'
    source: Literal["seed", "auto"] = "seed"


class NextQuestionResponse(BaseModel):
    exhausted_and_regenerated: bool = False    # generate-once-cache fired
    question: ArenaQuestion


# ----------------------------------------------------------------------
# Step 8: AI analysis (Type B - exactly one live AI call)
# ----------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    question_id: str
    answer_text: str = Field(min_length=1, max_length=20_000)
    run_output: Optional[str] = Field(         # stdout from the shared kernel
        default=None, max_length=8_000
    )
    time_taken_seconds: Optional[int] = Field(default=None, ge=0, le=7_200)


class AnalysisResult(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    question_id: str
    score: int = Field(ge=0, le=100)
    verdict: Literal["correct", "partially_correct", "incorrect"]
    good: List[str]
    missing: List[str]
    walkthrough: str                           # model solution with reasoning
    model_solution: str
    next_hint: str
    subtopic_mastered: bool                    # did this tick the tab green?
    topic_complete: bool                       # did the roadmap card go green?
    points_awarded: int


# ----------------------------------------------------------------------
# Subtopic progress strip (Type A)
# ----------------------------------------------------------------------

class SubtopicProgressResponse(BaseModel):
    subtopic_id: str
    answered: int
    correct: int
    bank_size: int
    mastery_pct: int = Field(ge=0, le=100)
    mastered: bool
    next_difficulty: Optional[str] = None
