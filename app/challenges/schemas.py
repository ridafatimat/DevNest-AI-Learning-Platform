# app/challenges/schemas.py

from pydantic import BaseModel
from typing import List


# -------------------------------------------------
# SHARED FIELDS
# -------------------------------------------------
class ChallengeBase(BaseModel):
    title: str
    description: str
    publicTests: List[str]
    hiddenTestsId: List[str]
    topics: List[str]
    difficulty: str
    hints: List[str]


# -------------------------------------------------
# CREATE: USER PROVIDES THE ID
# -------------------------------------------------
class ChallengeCreate(ChallengeBase):
    id: int   # user sends 1, 2, 3, ...


# -------------------------------------------------
# UPDATE: SAME FIELDS AS BASE (NO ID IN BODY)
# -------------------------------------------------
class ChallengeUpdate(ChallengeBase):
    pass


# -------------------------------------------------
# RESPONSE MODEL: WHAT WE RETURN TO CLIENT
# -------------------------------------------------
class ChallengeResponse(ChallengeBase):
    id: int
