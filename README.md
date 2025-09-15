# quiz-master-4204-4420

## Quiz Backend (FastAPI)

This service exposes REST APIs used by the React frontend. It connects to the MySQL database started by the database container.

### Environment configuration

Copy `quiz_backend/.env.example` to `quiz_backend/.env` and adjust if needed:

- MYSQL_HOST: MySQL host (default: localhost)
- MYSQL_PORT: MySQL port (default: 5000)
- MYSQL_DB: Database name (default: myapp)
- MYSQL_USER: Database user (default: appuser)
- MYSQL_PASSWORD: Database password (default: dbuser123)

These variables are read by `src/api/db.py` to initialize a MySQL connection pool at startup.

### Install and run locally

1) Navigate to the backend folder:
   cd quiz_backend

2) Install dependencies:
   pip install -r requirements.txt

3) Run the API (dev mode):
   uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

OpenAPI docs will be available at:
- Swagger UI: http://localhost:8000/docs
- JSON schema: http://localhost:8000/openapi.json

### Expected database state

Run the database container’s `startup.sh`, then apply `schema.sql` and `seed.sql` from the database workspace to populate sample data before starting the backend.

### API overview

Main endpoints consumed by the frontend:
- GET /quizzes
- GET /quizzes/{quiz_id}/questions
- POST /attempts/start
- POST /attempts/{attempt_id}/answer
- POST /attempts/{attempt_id}/submit
- GET /attempts/{attempt_id}
- GET /leaderboard