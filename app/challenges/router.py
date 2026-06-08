# app/challenges/router.py

from fastapi import APIRouter, HTTPException, Query
from .schemas import ChallengeCreate, ChallengeResponse
from . import service

router = APIRouter(
    prefix="/challenges",
    tags=["challenges"],
)


# ---------------------------------------------------------
# LIST CHALLENGES
# ---------------------------------------------------------
@router.get("/", response_model=list[ChallengeResponse])
async def get_all_challenges(
    topic: str | None = None,
    difficulty: str | None = None,
    limit: int = Query(50, ge=1, le=100),
):
    return service.list_challenges(topic=topic, difficulty=difficulty, limit=limit)


# ---------------------------------------------------------
# CREATE CHALLENGE
# ---------------------------------------------------------
@router.post("/", response_model=ChallengeResponse)
async def create_new_challenge(payload: ChallengeCreate):
    data = payload.model_dump()
    created = service.create_challenge(payload.id, data)
    return created


# ---------------------------------------------------------
# GET BY ID
# ---------------------------------------------------------
@router.get("/{challenge_id}", response_model=ChallengeResponse)
async def get_challenge(challenge_id: int):
    result = service.get_challenge_by_id(challenge_id)
    if not result:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return result


# ---------------------------------------------------------
# UPDATE CHALLENGE
# ---------------------------------------------------------
@router.put("/{challenge_id}", response_model=ChallengeResponse)
async def update_challenge(challenge_id: int, payload: ChallengeCreate):
    data = payload.model_dump()

    updated = service.update_challenge(challenge_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Challenge not found")

    return updated


# ---------------------------------------------------------
# DELETE CHALLENGE
# ---------------------------------------------------------
@router.delete("/{challenge_id}")
async def delete_challenge(challenge_id: int):
    success = service.delete_challenge(challenge_id)
    if not success:
        raise HTTPException(status_code=404, detail="Challenge not found")

    return {"message": "Challenge deleted successfully"}


# ---------------------------------------------------------
# GET BY TITLE
# ---------------------------------------------------------
@router.get("/title/{title}", response_model=ChallengeResponse)
async def get_challenge_by_title(title: str):
    challenge = service.get_challenge_by_title(title)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return challenge
