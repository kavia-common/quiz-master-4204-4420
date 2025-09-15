from fastapi import APIRouter
from typing import List, Dict, Any

from src.api.db import get_connection

router = APIRouter(prefix="/quizzes", tags=["Quizzes"])


def _row_to_quiz(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row.get("description"),
        "total_questions": row.get("total_questions"),
    }


# PUBLIC_INTERFACE
@router.get(
    "",
    summary="List quizzes",
    description="Return list of available quizzes with metadata.",
    responses={200: {"description": "List of quizzes"}},
)
def list_quizzes() -> List[Dict[str, Any]]:
    """
    List available quizzes.

    Returns:
        A list of quizzes containing id, title, description and total_questions.
    """
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        # Attempt to read from quizzes table if exists, else fallback to infer from questions
        try:
            cur.execute("SELECT id, title, description, total_questions FROM quizzes")
            rows = cur.fetchall()
            return [_row_to_quiz(r) for r in rows]
        except Exception:
            # Fallback: build a single default quiz if schema lacks quizzes table
            cur.execute("SELECT COUNT(*) AS cnt FROM information_schema.tables WHERE table_name = 'questions'")
            info = cur.fetchone()
            total_questions = 0
            if info and info.get("cnt", 0) > 0:
                cur.execute("SELECT COUNT(*) AS tq FROM questions")
                r = cur.fetchone()
                total_questions = (r or {}).get("tq", 0)
            return [{
                "id": 1,
                "title": "General Quiz",
                "description": "Default quiz comprised of all questions.",
                "total_questions": total_questions,
            }]
    finally:
        conn.close()
