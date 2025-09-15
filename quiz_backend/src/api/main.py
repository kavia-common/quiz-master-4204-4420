from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import db
from src.api.routers.quizzes import router as quizzes_router
from src.api.routers.questions import router as questions_router
from src.api.routers.attempts import router as attempts_router
from src.api.routers.leaderboard import router as leaderboard_router

openapi_tags = [
    {"name": "Health", "description": "Health and service status endpoints."},
    {"name": "Database", "description": "Database lifecycle and information (internal)."},
    {"name": "Quizzes", "description": "Quiz discovery and metadata"},
    {"name": "Questions", "description": "Quiz questions retrieval"},
    {"name": "Attempts", "description": "Quiz attempt lifecycle and answering"},
    {"name": "Leaderboard", "description": "Top results and rankings"},
]

app = FastAPI(
    title="Quiz Backend API",
    description="Backend for the Quiz application. Provides endpoints for questions, submissions, and leaderboard.",
    version="0.1.0",
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    """
    Initialize database connection pool at service startup.

    Reads configuration from environment variables:
    - MYSQL_HOST
    - MYSQL_PORT
    - MYSQL_DB
    - MYSQL_USER
    - MYSQL_PASSWORD
    """
    # Initialize the DB pool; will raise if env vars are missing
    db.init_pool()


@app.on_event("shutdown")
async def on_shutdown():
    """
    Close database resources on shutdown.
    """
    db.close_pool()


@app.get("/", tags=["Health"], summary="Health Check", description="Simple health check endpoint to verify service status.")
def health_check():
    """
    Health check endpoint.

    Returns:
        JSON object with a 'message' key indicating health.
    """
    return {"message": "Healthy"}


# Include routers
app.include_router(quizzes_router)
app.include_router(questions_router)
app.include_router(attempts_router)
app.include_router(leaderboard_router)
