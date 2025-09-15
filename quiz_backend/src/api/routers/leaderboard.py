from fastapi import APIRouter, Query

from src.api.db import get_connection
from src.api.schemas import ResultSchema, LeaderboardResponse

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])


# PUBLIC_INTERFACE
@router.get(
    "",
    summary="Get leaderboard",
    description="Return top quiz results sorted by score descending and submitted time ascending.",
    response_model=LeaderboardResponse,
)
def get_leaderboard(limit: int = Query(20, ge=1, le=100, description="Max number of results to return")) -> LeaderboardResponse:
    """
    Get the leaderboard top results.

    Args:
        limit: The maximum number of results to return.

    Returns:
        LeaderboardResponse containing a list of top results.
    """
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        # Prefer attempts table if exists; else fallback to results table if present
        results = []
        try:
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM information_schema.tables WHERE table_name = 'attempts'"
            )
            has_attempts = cur.fetchone()
            if has_attempts and has_attempts.get("cnt", 0) > 0:
                cur.execute(
                    """
                    SELECT id, user_name, score, total_questions, time_taken_seconds
                    FROM attempts
                    WHERE score IS NOT NULL
                    ORDER BY score DESC, submitted_at ASC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
                for r in rows:
                    results.append(
                        ResultSchema(
                            id=r["id"],
                            user_name=r["user_name"],
                            score=r["score"] or 0,
                            total_questions=r.get("total_questions") or 0,
                            time_taken_seconds=r.get("time_taken_seconds"),
                        )
                    )
                return LeaderboardResponse(results=results)
        except Exception:
            pass

        # Fallback to a standalone results table if present
        try:
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM information_schema.tables WHERE table_name = 'results'"
            )
            has_results = cur.fetchone()
            if has_results and has_results.get("cnt", 0) > 0:
                cur.execute(
                    """
                    SELECT id, user_name, score, total_questions, time_taken_seconds
                    FROM results
                    ORDER BY score DESC, id ASC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
                for r in rows:
                    results.append(
                        ResultSchema(
                            id=r["id"],
                            user_name=r["user_name"],
                            score=r["score"] or 0,
                            total_questions=r.get("total_questions") or 0,
                            time_taken_seconds=r.get("time_taken_seconds"),
                        )
                    )
        except Exception:
            pass

        return LeaderboardResponse(results=results)
    finally:
        conn.close()
