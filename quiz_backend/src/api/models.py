"""
Lightweight data models representing DB rows for the Quiz backend.

These are plain Python classes/typed dict-like containers to keep the project
simple while using direct mysql-connector queries (no ORM).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Question:
    id: int
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: str  # expected values: "A" | "B" | "C" | "D"
    # category or quiz_id can be added later if needed


@dataclass
class QuizResult:
    id: int
    user_name: str
    score: int
    total_questions: int
    # Optional fields for richer analytics
    time_taken_seconds: Optional[int] = None
