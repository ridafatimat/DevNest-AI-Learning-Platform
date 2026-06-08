# app/quizzes/__init__.py
from fastapi import FastAPI
from .router import router as quizzes_router

# This is the sub-app for quizzes
app = FastAPI(
    title="DevNest - Quizzes API",
    docs_url="/",              # so Swagger is shown at /quizzes/
    openapi_url="/openapi.json"
)

# Attach the quiz endpoints
app.include_router(quizzes_router)
