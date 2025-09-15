from fastapi import APIRouter, HTTPException, Path

from src.api.db import get_connection
from src.api.schemas import QuestionSchema, QuestionsResponse

router = APIRouter(prefix="/quizzes", tags=["Questions"])


def _validate_quiz_exists(quiz_id: int, cur) -> bool:
    # Try checking quizzes table if available; if not, treat quiz_id 1 as default/valid.
    try:
        cur.execute("SELECT COUNT(*) AS cnt FROM information_schema.tables WHERE table_name = 'quizzes'")
        tinfo = cur.fetchone()
        if tinfo and tinfo.get("cnt", 0) > 0:
            cur.execute("SELECT id FROM quizzes WHERE id = %s", (quiz_id,))
            r = cur.fetchone()
            return r is not None
    except Exception:
        pass
    return quiz_id == 1


# PUBLIC_INTERFACE
@router.get(
    "/{quiz_id}/questions",
    summary="Get questions for a quiz",
    description="Return the list of questions for the specified quiz.",
    response_model=QuestionsResponse,
    responses={404: {"description": "Quiz not found"}},
)
def get_quiz_questions(
    quiz_id: int = Path(..., description="Quiz identifier")
) -> QuestionsResponse:
    """
    Retrieve questions for a given quiz.

    Args:
        quiz_id: Identifier of the quiz.

    Returns:
        QuestionsResponse containing a list of QuestionSchema.

    Raises:
        HTTPException 404 if quiz does not exist.
    """
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        if not _validate_quiz_exists(quiz_id, cur):
            raise HTTPException(status_code=404, detail="Quiz not found")

        # If quiz-specific relation exists, use it; else return all questions as default quiz.
        try:
            cur.execute("SELECT COUNT(*) AS cnt FROM information_schema.tables WHERE table_name = 'quiz_questions'")
            has_map = cur.fetchone()
            if has_map and has_map.get("cnt", 0) > 0:
                cur.execute(
                    """
                    SELECT q.id, q.text, q.option_a, q.option_b, q.option_c, q.option_d
                    FROM questions q
                    JOIN quiz_questions qq ON qq.question_id = q.id
                    WHERE qq.quiz_id = %s
                    ORDER BY q.id ASC
                    """,
                    (quiz_id,),
                )
            else:
                cur.execute(
                    """
                    SELECT id, text, option_a, option_b, option_c, option_d
                    FROM questions
                    ORDER BY id ASC
                    """
                )
            rows = cur.fetchall()
        except Exception:
            cur.execute(
                """
                SELECT id, text, option_a, option_b, option_c, option_d
                FROM questions
                ORDER BY id ASC
                """
            )
            rows = cur.fetchall()

        questions = [
            QuestionSchema(
                id=r["id"],
                text=r["text"],
                option_a=r["option_a"],
                option_b=r["option_b"],
                option_c=r["option_c"],
                option_d=r["option_d"],
            )
            for r in rows
        ]
        return QuestionsResponse(questions=questions)
    finally:
        conn.close()
