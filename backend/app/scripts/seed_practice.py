# backend/app/scripts/seed_practice.py
"""
Seed concept cards + practice questions for the Data Science Foundation topics
(python, numpy, pandas, statistics) so the learning loop has real content.

Small on purpose (3 questions/topic) — enough to complete a topic and watch the
scoring spine + skill radar react. Idempotent (keys on topic + question order).

Run (after seed_catalog):
    python -m app.scripts.seed_practice
"""
import asyncio

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.domain import RoadmapTopic
from app.models.practice import TopicContent, TopicQuestion

# topic_slug -> (concept_markdown, [ (kind, difficulty, q, model_answer, why, how, example, mistakes) ])
CONTENT = {
    "python": (
        "# Python basics\nVariables, types, and control flow. A `for` loop iterates a sequence; "
        "a `while` loop runs until its condition is False.",
        [
            ("text", "Easy", "What keyword defines a function in Python?",
             "def", "Because `def` introduces a function definition.",
             "Write `def name(args):` then an indented body.",
             "def add(a, b): return a + b", "Using `function` or `func` instead of `def`."),
            ("code", "Medium", "Write a function that returns the sum of a list of numbers.",
             "def total(xs): return sum(xs)", "sum() aggregates an iterable of numbers.",
             "Loop and accumulate, or call the built-in sum().",
             "def total(xs): return sum(xs)", "Forgetting the empty-list case (sum([]) == 0)."),
            ("text", "Advanced", "Why can a `while` loop hang forever?",
             "Because its condition never becomes False (the loop variable is never updated).",
             "An infinite loop happens when the exit condition is never met.",
             "Ensure the loop mutates state that moves toward the exit condition.",
             "i = 0\nwhile i < 5:\n    i += 1", "Forgetting to update the variable used in the condition."),
        ],
    ),
    "numpy": (
        "# NumPy\n`ndarray` is a fast, typed, N-dimensional array. Vectorized ops replace Python loops.",
        [
            ("code", "Easy", "How do you create a NumPy array from [1,2,3]?",
             "np.array([1,2,3])", "np.array() builds an ndarray from a sequence.",
             "Import numpy as np, then call np.array().",
             "import numpy as np; a = np.array([1,2,3])", "Passing separate args instead of one list."),
            ("text", "Medium", "What is broadcasting in NumPy?",
             "Rules that let arrays of different shapes combine in element-wise operations.",
             "Smaller arrays are 'stretched' to match the larger shape without copying.",
             "A (3,1) array plus a (1,3) array yields a (3,3) result.",
             "np.array([[1],[2],[3]]) + np.array([10,20,30])",
             "Assuming shapes must match exactly."),
            ("text", "Advanced", "Why are vectorized NumPy ops faster than Python loops?",
             "They run in optimized C over contiguous memory, avoiding per-element Python overhead.",
             "The heavy lifting happens in compiled code, not the interpreter.",
             "a * 2 processes the whole array in C.",
             "a = np.arange(1_000_000); a * 2",
             "Looping element-by-element in Python instead of vectorizing."),
        ],
    ),
    "pandas": (
        "# Pandas\n`DataFrame` is a labeled 2D table. `Series` is a labeled 1D column.",
        [
            ("code", "Easy", "How do you read a CSV into a DataFrame?",
             "pd.read_csv('file.csv')", "read_csv parses a CSV file into a DataFrame.",
             "Import pandas as pd, call pd.read_csv with the path.",
             "import pandas as pd; df = pd.read_csv('data.csv')",
             "Forgetting the file path or wrong separator."),
            ("text", "Medium", "How do you select rows where column 'age' > 30?",
             "df[df['age'] > 30]", "Boolean indexing filters rows by a condition.",
             "Build a boolean mask, then index the DataFrame with it.",
             "df[df['age'] > 30]", "Using df('age') parentheses instead of brackets."),
            ("text", "Advanced", "What does groupby do?",
             "It splits rows into groups by key, applies an aggregation, and combines results.",
             "Split-apply-combine: group, aggregate, recombine.",
             "df.groupby('city')['sales'].sum()",
             "df.groupby('city')['sales'].sum()",
             "Forgetting to aggregate after grouping."),
        ],
    ),
    "statistics": (
        "# Statistics\nMean, median, variance, and distributions summarize data.",
        [
            ("text", "Easy", "What is the mean of [2, 4, 6]?",
             "4", "The mean is the sum divided by the count: 12/3 = 4.",
             "Add the values and divide by how many there are.",
             "(2+4+6)/3 = 4", "Confusing mean with median."),
            ("text", "Medium", "When is the median preferred over the mean?",
             "When the data is skewed or has outliers, since the median resists extreme values.",
             "Outliers pull the mean but barely move the median.",
             "Incomes: a few huge values inflate the mean.",
             "median([1,2,3,100]) = 2.5", "Using the mean on heavily skewed data."),
            ("text", "Advanced", "What does the standard deviation measure?",
             "The typical spread of values around the mean (square root of the variance).",
             "It quantifies dispersion: how far values typically fall from the mean.",
             "Low std = tightly clustered; high std = widely spread.",
             "std([2,2,2]) = 0", "Confusing variance with standard deviation."),
        ],
    ),
}


async def main() -> None:
    async with AsyncSessionLocal() as db:
        for slug, (concept, questions) in CONTENT.items():
            topic = (
                await db.execute(select(RoadmapTopic).where(RoadmapTopic.slug == slug))
            ).scalar_one_or_none()
            if topic is None:
                continue

            content = (
                await db.execute(select(TopicContent).where(TopicContent.topic_id == topic.id))
            ).scalar_one_or_none()
            if content is None:
                db.add(TopicContent(topic_id=topic.id, concept_markdown=concept, examples_json=[]))

            existing = (
                await db.execute(
                    select(TopicQuestion.order_index).where(TopicQuestion.topic_id == topic.id)
                )
            ).scalars().all()
            existing_orders = set(existing)

            for i, (kind, diff, q, ans, why, how, ex, mistakes) in enumerate(questions):
                if i in existing_orders:
                    continue
                db.add(TopicQuestion(
                    topic_id=topic.id, order_index=i, question_kind=kind, difficulty=diff,
                    question_text=q, model_answer=ans, why_explanation=why, how_explanation=how,
                    example=ex, common_mistakes=mistakes, review_status="published",
                ))
        await db.commit()
    print("Seeded concept cards + 3 questions each for python/numpy/pandas/statistics.")


if __name__ == "__main__":
    asyncio.run(main())