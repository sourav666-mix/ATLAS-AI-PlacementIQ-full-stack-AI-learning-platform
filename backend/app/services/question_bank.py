# backend/app/services/question_bank.py
"""
Offline fallback content for the Assessment Center.

Used when no AI provider is configured (or generation fails), so Aptitude and
Mock Interview always work. When AI is enabled, assessment_service prefers
freshly generated questions and only falls back here.
"""
from typing import List

# category -> list of {question, options[4], correct_index, explanation}
APTITUDE_BANK: dict[str, List[dict]] = {
    "quant": [
        {"question": "What is 15% of 200?", "options": ["25", "30", "35", "40"],
         "correct_index": 1, "explanation": "15% of 200 = 0.15 * 200 = 30."},
        {"question": "A train travels 60 km in 45 minutes. Its speed in km/h?",
         "options": ["70", "75", "80", "85"], "correct_index": 2,
         "explanation": "60 km in 0.75 h = 80 km/h."},
        {"question": "If 3x = 27, then x = ?", "options": ["6", "7", "8", "9"],
         "correct_index": 3, "explanation": "27 / 3 = 9."},
        {"question": "The average of 4, 8, and 12 is:", "options": ["6", "7", "8", "9"],
         "correct_index": 2, "explanation": "(4+8+12)/3 = 24/3 = 8."},
        {"question": "A shirt costs 800 after a 20% discount. Original price?",
         "options": ["950", "1000", "1050", "1100"], "correct_index": 1,
         "explanation": "800 / 0.8 = 1000."},
    ],
    "logical": [
        {"question": "Find the next number: 2, 6, 12, 20, ?",
         "options": ["28", "30", "32", "36"], "correct_index": 1,
         "explanation": "Differences 4,6,8,10 -> 20+10 = 30."},
        {"question": "If all Bloops are Razzies and all Razzies are Lazzies, then all Bloops are:",
         "options": ["Lazzies", "Not Lazzies", "Razzies only", "None"], "correct_index": 0,
         "explanation": "Transitivity: Bloops -> Razzies -> Lazzies."},
        {"question": "Odd one out: Circle, Square, Triangle, Cube",
         "options": ["Circle", "Square", "Triangle", "Cube"], "correct_index": 3,
         "explanation": "Cube is 3D; the rest are 2D shapes."},
        {"question": "CAT is to 24 as DOG is to ? (A=1..Z=26, sum letters)",
         "options": ["26", "24", "22", "20"], "correct_index": 0,
         "explanation": "D(4)+O(15)+G(7) = 26."},
        {"question": "Complete: AZ, BY, CX, ?", "options": ["DW", "DV", "EW", "DX"],
         "correct_index": 0, "explanation": "Forward/backward pairing: D with W."},
    ],
    "verbal": [
        {"question": "Choose the synonym of 'concise':",
         "options": ["Wordy", "Brief", "Vague", "Complex"], "correct_index": 1,
         "explanation": "Concise means brief and to the point."},
        {"question": "Choose the antonym of 'scarce':",
         "options": ["Rare", "Abundant", "Limited", "Meager"], "correct_index": 1,
         "explanation": "Scarce's opposite is abundant."},
        {"question": "Fill in: She is good ___ mathematics.",
         "options": ["in", "on", "at", "of"], "correct_index": 2,
         "explanation": "'Good at' is the correct collocation."},
        {"question": "Which is spelled correctly?",
         "options": ["Recieve", "Receive", "Receeve", "Receve"], "correct_index": 1,
         "explanation": "'I before E except after C' -> receive."},
        {"question": "Pick the correctly punctuated sentence:",
         "options": ["Its raining.", "It's raining.", "Its' raining.", "It raining."],
         "correct_index": 1, "explanation": "It's = it is."},
    ],
    "data_interpretation": [
        {"question": "Sales: Q1=100, Q2=150. Percentage growth Q1->Q2?",
         "options": ["25%", "40%", "50%", "60%"], "correct_index": 2,
         "explanation": "(150-100)/100 = 50%."},
        {"question": "If a pie chart shows 90 degrees for 'Rent', what % is Rent?",
         "options": ["20%", "25%", "30%", "45%"], "correct_index": 1,
         "explanation": "90/360 = 25%."},
        {"question": "Mean of dataset [10, 20, 30, 40]?",
         "options": ["20", "25", "30", "35"], "correct_index": 1,
         "explanation": "(10+20+30+40)/4 = 25."},
        {"question": "A bar is 3x taller than a 20-unit bar. Its value?",
         "options": ["40", "50", "60", "80"], "correct_index": 2,
         "explanation": "3 * 20 = 60."},
        {"question": "Ratio of 40 to 100 as a percentage?",
         "options": ["25%", "40%", "60%", "80%"], "correct_index": 1,
         "explanation": "40/100 = 40%."},
    ],
}

# domain -> list of open-ended interview question templates
MOCK_TEMPLATES: dict[str, List[str]] = {
    "data_science": [
        "Explain the bias-variance tradeoff.",
        "How would you handle missing data in a dataset?",
        "What is the difference between supervised and unsupervised learning?",
        "Describe how a decision tree makes a split.",
        "How do you evaluate a classification model beyond accuracy?",
    ],
    "software_engineer": [
        "Explain the difference between a process and a thread.",
        "What is the time complexity of binary search and why?",
        "How does a hash map work under the hood?",
        "Describe REST and how it differs from RPC.",
        "How would you design a URL shortener at a high level?",
    ],
}

GENERIC_BEHAVIORAL = [
    "Tell me about a challenging project and how you handled it.",
    "Describe a time you disagreed with a teammate. What did you do?",
    "Where do you see the biggest gap in your current skills?",
]


def aptitude(category: str, count: int) -> List[dict]:
    pool = APTITUDE_BANK.get(category) or APTITUDE_BANK["quant"]
    # cycle if count exceeds pool size
    out = [pool[i % len(pool)] for i in range(max(1, count))]
    return out


def mock(domain: str, count: int) -> List[str]:
    pool = list(MOCK_TEMPLATES.get(domain, [])) + GENERIC_BEHAVIORAL
    if not pool:
        pool = GENERIC_BEHAVIORAL
    return [pool[i % len(pool)] for i in range(max(1, count))]


__all__ = ["aptitude", "mock", "APTITUDE_BANK", "MOCK_TEMPLATES"]