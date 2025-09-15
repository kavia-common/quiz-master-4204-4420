"""
Pydantic schemas for request/response payloads with API documentation metadata.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# PUBLIC_INTERFACE
class QuestionSchema(BaseModel):
    """Question data returned via API."""
    id: int = Field(..., description="Unique identifier of the question")
    text: str = Field(..., description="Question text")
    option_a: str = Field(..., description="Option A")
    option_b: str = Field(..., description="Option B")
    option_c: str = Field(..., description="Option C")
    option_d: str = Field(..., description="Option D")


# PUBLIC_INTERFACE
class QuestionsResponse(BaseModel):
    """List of questions returned by the backend."""
    questions: List[QuestionSchema] = Field(..., description="Collection of quiz questions")


# PUBLIC_INTERFACE
class QuizSchema(BaseModel):
    """Quiz metadata."""
    id: int = Field(..., description="Quiz identifier")
    title: str = Field(..., description="Quiz title")
    description: Optional[str] = Field(None, description="Quiz description")
    total_questions: Optional[int] = Field(None, description="Number of questions in quiz")


# PUBLIC_INTERFACE
class SubmitAnswerRequest(BaseModel):
    """Payload for submitting an answer during a quiz."""
    question_id: int = Field(..., description="Question identifier")
    selected_option: str = Field(..., description="Selected option letter: A/B/C/D")
    user_name: str = Field(..., description="User's display name")


# PUBLIC_INTERFACE
class SubmitResultRequest(BaseModel):
    """Payload for submitting final quiz results."""
    user_name: str = Field(..., description="User's display name")
    score: int = Field(..., description="Number of correct answers")
    total_questions: int = Field(..., description="Total number of questions answered")
    time_taken_seconds: Optional[int] = Field(None, description="Time taken in seconds")


# PUBLIC_INTERFACE
class ResultSchema(BaseModel):
    """Single quiz result entry."""
    id: int = Field(..., description="Result identifier")
    user_name: str = Field(..., description="User's display name")
    score: int = Field(..., description="Score achieved")
    total_questions: int = Field(..., description="Total questions for the quiz")
    time_taken_seconds: Optional[int] = Field(None, description="Time taken in seconds")


# PUBLIC_INTERFACE
class LeaderboardResponse(BaseModel):
    """Leaderboard response sorted by top scores."""
    results: list[ResultSchema] = Field(..., description="Top quiz results ordered by score descending")
