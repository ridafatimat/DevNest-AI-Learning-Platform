from fastapi import APIRouter, HTTPException
from .schemas import Quiz
from . import service

router = APIRouter(prefix="/quizzes", tags=["quizzes"])


# -----------------------------
# CREATE QUIZ
# -----------------------------
@router.post("/")
def create_quiz(quiz: Quiz):
    return service.create_quiz(quiz.id, quiz.dict())


# -----------------------------
# GET QUIZ BY ID
# -----------------------------
@router.get("/{quiz_id}")
def get_quiz(quiz_id: str):
    result = service.get_quiz(quiz_id)
    if not result:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return result


# -----------------------------
# GET QUIZ BY TITLE
# -----------------------------
@router.get("/title/{title}")
def get_quiz_by_title(title: str):
    result = service.get_quiz_by_title(title)
    if not result:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return result


# -----------------------------
# UPDATE QUIZ BY ID
# -----------------------------
@router.put("/{quiz_id}")
def update_quiz(quiz_id: str, quiz: Quiz):
    updated = service.update_quiz(quiz_id, quiz.dict())
    if not updated:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return updated


# -----------------------------
# DELETE QUIZ BY ID
# -----------------------------
@router.delete("/{quiz_id}")
def delete_quiz(quiz_id: str):
    success = service.delete_quiz(quiz_id)
    if not success:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return {"message": "Quiz deleted successfully"}
