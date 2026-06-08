from pydantic import BaseModel
from typing import List

class Quiz(BaseModel):
    id: str
    title: str
    description: str
    difficulty: str
    questions: List[str]
    answers: List[str]
    hints: List[str]
