# backend/app/scripts/seed_arena.py
"""
Seed the Code Arena problem bank with a few Python DSA problems (with visible +
hidden test cases). Idempotent (keys on title). Each problem stores an
"entry_point" — the function name the runner will call.

Run:
    python -m app.scripts.seed_arena
"""
import asyncio

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.arena import ArenaProblem

PROBLEMS = [
    {
        "category": "dsa", "difficulty": "Easy", "title": "Two Sum",
        "topic": "arrays", "pattern_tag": "hash-map",
        "statement": "Given a list of integers `nums` and an integer `target`, return the indices "
                     "of the two numbers that add up to target. Assume exactly one solution.",
        "examples": [{"input": "nums=[2,7,11,15], target=9", "output": "[0, 1]"}],
        "constraints": ["2 <= len(nums) <= 10^4", "Only one valid answer exists."],
        "hints": ["Use a hash map of value -> index.", "Check target - num as you iterate."],
        "starter_code": {"python": "def two_sum(nums, target):\n    # return [i, j]\n    pass"},
        "entry_point": "two_sum",
        "visible": [{"input": [[2, 7, 11, 15], 9], "output": [0, 1]},
                    {"input": [[3, 2, 4], 6], "output": [1, 2]}],
        "hidden": [{"input": [[3, 3], 6], "output": [0, 1]},
                   {"input": [[1, 5, 9, 2], 11], "output": [2, 3]}],
        "optimal_solution": "def two_sum(nums, target):\n    seen = {}\n    for i, n in enumerate(nums):\n        if target - n in seen:\n            return [seen[target - n], i]\n        seen[n] = i",
        "complexity": "O(n) time, O(n) space",
    },
    {
        "category": "dsa", "difficulty": "Easy", "title": "Reverse String",
        "topic": "strings", "pattern_tag": "two-pointer",
        "statement": "Return the reverse of the input string `s`.",
        "examples": [{"input": "s='hello'", "output": "'olleh'"}],
        "constraints": ["0 <= len(s) <= 10^4"],
        "hints": ["Slicing s[::-1] works.", "Or swap with two pointers."],
        "starter_code": {"python": "def reverse_string(s):\n    pass"},
        "entry_point": "reverse_string",
        "visible": [{"input": ["hello"], "output": "olleh"},
                    {"input": [""], "output": ""}],
        "hidden": [{"input": ["ab"], "output": "ba"},
                   {"input": ["racecar"], "output": "racecar"}],
        "optimal_solution": "def reverse_string(s):\n    return s[::-1]",
        "complexity": "O(n) time",
    },
    {
        "category": "dsa", "difficulty": "Easy", "title": "FizzBuzz Count",
        "topic": "math", "pattern_tag": "iteration",
        "statement": "Return how many numbers from 1 to n (inclusive) are divisible by 3 or 5.",
        "examples": [{"input": "n=15", "output": "7"}],
        "constraints": ["1 <= n <= 10^6"],
        "hints": ["Count multiples of 3, 5, subtract multiples of 15."],
        "starter_code": {"python": "def fizzbuzz_count(n):\n    pass"},
        "entry_point": "fizzbuzz_count",
        "visible": [{"input": [15], "output": 7}, {"input": [10], "output": 5}],
        "hidden": [{"input": [1], "output": 0}, {"input": [30], "output": 14}],
        "optimal_solution": "def fizzbuzz_count(n):\n    return sum(1 for i in range(1, n+1) if i%3==0 or i%5==0)",
        "complexity": "O(n) time (O(1) with math)",
    },
    {
        "category": "dsa", "difficulty": "Medium", "title": "Maximum Subarray",
        "topic": "arrays", "pattern_tag": "kadane",
        "statement": "Return the largest sum of any contiguous subarray of `nums`.",
        "examples": [{"input": "nums=[-2,1,-3,4,-1,2,1,-5,4]", "output": "6"}],
        "constraints": ["1 <= len(nums) <= 10^5"],
        "hints": ["Kadane's algorithm.", "Track current and best running sums."],
        "starter_code": {"python": "def max_subarray(nums):\n    pass"},
        "entry_point": "max_subarray",
        "visible": [{"input": [[-2, 1, -3, 4, -1, 2, 1, -5, 4]], "output": 6},
                    {"input": [[1]], "output": 1}],
        "hidden": [{"input": [[5, 4, -1, 7, 8]], "output": 23},
                   {"input": [[-3, -1, -2]], "output": -1}],
        "optimal_solution": "def max_subarray(nums):\n    best = cur = nums[0]\n    for n in nums[1:]:\n        cur = max(n, cur + n)\n        best = max(best, cur)\n    return best",
        "complexity": "O(n) time, O(1) space",
    },
]


async def main() -> None:
    async with AsyncSessionLocal() as db:
        for p in PROBLEMS:
            exists = (
                await db.execute(select(ArenaProblem).where(ArenaProblem.title == p["title"]))
            ).scalar_one_or_none()
            if exists is not None:
                continue
            db.add(ArenaProblem(
                category=p["category"], difficulty=p["difficulty"], title=p["title"],
                topic=p["topic"], pattern_tag=p["pattern_tag"], statement=p["statement"],
                examples_json=p["examples"], constraints_json=p["constraints"], hints_json=p["hints"],
                starter_code_json=p["starter_code"],
                test_cases_json={"entry_point": p["entry_point"], "visible": p["visible"], "hidden": p["hidden"]},
                optimal_solution=p["optimal_solution"], complexity=p["complexity"],
                source="seed", review_status="published",
            ))
        await db.commit()
    print("Seeded Code Arena bank: Two Sum, Reverse String, FizzBuzz Count, Maximum Subarray.")


if __name__ == "__main__":
    asyncio.run(main())