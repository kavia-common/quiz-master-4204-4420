from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel, Field
from typing import Optional

from src.api.db import get_connection

router = APIRouter(prefix="/attempts", tags=["Attempts"])


class StartAttemptRequest(BaseModel):
    user_name: str = Field(..., description="User's display name")
    quiz_id: int = Field(..., description="Quiz identifier")


class StartAttemptResponse(BaseModel):
    attempt_id: int = Field(..., description="New attempt identifier")


class AnswerRequest(BaseModel):
    question_id: int = Field(..., description="Question identifier")
    selected_option: str = Field(..., description="Selected option letter A/B/C/D")


class AttemptStatusResponse(BaseModel):
    attempt_id: int = Field(..., description="Attempt identifier")
    quiz_id: int = Field(..., description="Quiz identifier")
    user_name: str = Field(..., description="User name")
    answers_count: int = Field(..., description="How many answers recorded so far")
    is_submitted: bool = Field(..., description="Whether the attempt is submitted")
    score: Optional[int] = Field(None, description="Score if submitted")
    total_questions: Optional[int] = Field(None, description="Total questions if submitted")
    time_taken_seconds: Optional[int] = Field(None, description="Time if submitted")


def _table_exists(cur, table_name: str) -> bool:
    cur.execute(
        "SELECT COUNT(*) AS cnt FROM information_schema.tables WHERE table_name = %s",
        (table_name,),
    )
    r = cur.fetchone()
    return (r or {}).get("cnt", 0) > 0


def _ensure_attempt_tables(cur):
    # Create minimal tables if they don't exist; safe-guarded for local dev environments.
    # In production a migration system would manage DDL.
    cur.execute(
        "CREATE TABLE IF NOT EXISTS attempts ("
        "id INT AUTO_INCREMENT PRIMARY KEY,"
        "quiz_id INT NOT NULL,"
        "user_name VARCHAR(255) NOT NULL,"
        "started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "submitted_at TIMESTAMP NULL,"
        "score INT NULL,"
        "total_questions INT NULL,"
        "time_taken_seconds INT NULL"
        ")"
    )
    cur.execute(
        "CREATE TABLE IF NOT EXISTS attempt_answers ("
        "attempt_id INT NOT NULL,"
        "question_id INT NOT NULL,"
        "selected_option CHAR(1) NOT NULL,"
        "PRIMARY KEY (attempt_id, question_id)"
        ")"
    )


# PUBLIC_INTERFACE
@router.post(
    "/start",
    summary="Start a quiz attempt",
    description="Create an attempt record for a user and quiz and return the attempt id.",
    response_model=StartAttemptResponse,
)
def start_attempt(payload: StartAttemptRequest) -> StartAttemptResponse:
    """
    Start a new attempt.

    Args:
        payload: user_name and quiz_id

    Returns:
        StartAttemptResponse containing the generated attempt_id.
    """
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        _ensure_attempt_tables(cur)
        # Validate quiz existence if quizzes table is present
        try:
            cur.execute("SELECT COUNT(*) AS cnt FROM quizzes WHERE id = %s", (payload.quiz_id,))
            r = cur.fetchone()
            if (r or {}).get("cnt", 0) == 0:
                # Allow quiz_id=1 default if no quizzes exists
                cur.execute("SELECT COUNT(*) AS c FROM quizzes")
                allq = cur.fetchone()
                total = (allq or {}).get("c", 0)
                if total > 0:
                    raise HTTPException(status_code=404, detail="Quiz not found")
        except Exception:
            # no quizzes table; accept quiz_id 1 as default
            if payload.quiz_id != 1:
                raise HTTPException(status_code=404, detail="Quiz not found")

        cur.execute(
            "INSERT INTO attempts (quiz_id, user_name) VALUES (%s, %s)",
            (payload.quiz_id, payload.user_name),
        )
        cur.execute("SELECT LAST_INSERT_ID() AS id")
        row = cur.fetchone()
        attempt_id = row["id"]
        return StartAttemptResponse(attempt_id=attempt_id)
    finally:
        conn.close()


# PUBLIC_INTERFACE
@router.post(
    "/{attempt_id}/answer",
    summary="Record an answer",
    description="Save or update user's selected option for a question in an ongoing attempt.",
)
def answer_question(
    attempt_id: int = Path(..., description="Attempt identifier"),
    payload: AnswerRequest = None,
):
    """
    Record or update an answer for a given question in the attempt.

    Returns:
        Simple acknowledgement.
    """
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        _ensure_attempt_tables(cur)

        cur.execute("SELECT id FROM attempts WHERE id = %s", (attempt_id,))
        a = cur.fetchone()
        if not a:
            raise HTTPException(status_code=404, detail="Attempt not found")

        # Upsert behavior: replace any prior answer for this question
        cur.execute(
            "REPLACE INTO attempt_answers (attempt_id, question_id, selected_option) VALUES (%s, %s, %s)",
            (attempt_id, payload.question_id, payload.selected_option[:1]),
        )
        return {"status": "ok"}
    finally:
        conn.close()


class SubmitAttemptRequest(BaseModel):
    time_taken_seconds: Optional[int] = Field(None, description="Time taken in seconds")


class SubmitAttemptResponse(BaseModel):
    attempt_id: int = Field(..., description="Attempt identifier")
    score: int = Field(..., description="Computed score")
    total_questions: int = Field(..., description="Total answered questions")


# PUBLIC_INTERFACE
@router.post(
    "/{attempt_id}/submit",
    summary="Submit attempt",
    description="Compute score for the attempt by comparing answers to correct options and save the result.",
    response_model=SubmitAttemptResponse,
)
def submit_attempt(
    attempt_id: int = Path(..., description="Attempt identifier"),
    payload: SubmitAttemptRequest = None,
) -> SubmitAttemptResponse:
    """
    Submit an attempt and compute score.

    Returns:
        SubmitAttemptResponse containing attempt_id, score, and total_questions.
    """
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        _ensure_attempt_tables(cur)

        cur.execute("SELECT id FROM attempts WHERE id = %s", (attempt_id,))
        a = cur.fetchone()
        if not a:
            raise HTTPException(status_code=404, detail="Attempt not found")

        # Join attempt_answers with questions.correct_option to compute score
        # correct_option column must exist; if not, score 0
        try:
            cur.execute(
                """
                SELECT aa.question_id, aa.selected_option, q.correct_option
                FROM attempt_answers aa
                JOIN questions q ON q.id = aa.question_id
                WHERE aa.attempt_id = %s
                """,
                (attempt_id,),
            )
            rows = cur.fetchall()
            total = len(rows)
            score = sum(1 for r in rows if (r.get("selected_option") or "").upper() == (r.get("correct_option") or "").upper())
        except Exception:
            total = 0
            score = 0

        cur.execute(
            "UPDATE attempts SET submitted_at = NOW(), score = %s, total_questions = %s, time_taken_seconds = %s WHERE id = %s",
            (score, total, payload.time_taken_seconds if payload else None, attempt_id),
        )
        return SubmitAttemptResponse(attempt_id=attempt_id, score=score, total_questions=total)
    finally:
        conn.close()


# PUBLIC_INTERFACE
@router.get(
    "/{attempt_id}",
    summary="Get attempt status",
    description="Retrieve current attempt info including answers count and submission details.",
    response_model=AttemptStatusResponse,
)
def get_attempt(attempt_id: int = Path(..., description="Attempt identifier")) -> AttemptStatusResponse:
    """
    Get attempt details.

    Returns:
        AttemptStatusResponse with attempt progress and submission info.
    """
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        _ensure_attempt_tables(cur)

        cur.execute("SELECT * FROM attempts WHERE id = %s", (attempt_id,))
        a = cur.fetchone()
        if not a:
            raise HTTPException(status_code=404, detail="Attempt not found")

        cur.execute("SELECT COUNT(*) AS cnt FROM attempt_answers WHERE attempt_id = %s", (attempt_id,))
        c = cur.fetchone()
        answers_count = (c or {}).get("cnt", 0)

        return AttemptStatusResponse(
            attempt_id=attempt_id,
            quiz_id=a["quiz_id"],
            user_name=a["user_name"],
            answers_count=answers_count,
            is_submitted=a["submitted_at"] is not None,
            score=a.get("score"),
            total_questions=a.get("total_questions"),
            time_taken_seconds=a.get("time_taken_seconds"),
        )
    finally:
        conn.close()
