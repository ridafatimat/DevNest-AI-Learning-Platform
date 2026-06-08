# app/models.py
from typing import Optional, List, Dict, Any
from datetime import datetime

# Firestore user document structure (for reference)
def make_user_doc(uid: str, email: str, name: Optional[str]=None, role: str="student", username: Optional[str]=None):
    return {
        "id": uid,
        "email": email,
        "name": name or "",
        "role": role,
        "username": username,
        "bio": "",
        "prefs": {},
        "joinedAt": datetime.utcnow(),
    }
# Firestore submission document structure
def make_submission_doc(
    submission_id: str,
    user_id: str,
    challenge_id: str,
    code: str,
    language: str,
    status: str = "queued",
    verdict: Optional[str] = None,
    score: Optional[float] = None,
    results: Optional[List[Dict[str, Any]]] = None,
    execution_time: Optional[float] = None,
    memory_used: Optional[int] = None,
):
    return {
        "id": submission_id,
        "userId": user_id,
        "challengeId": challenge_id,
        "code": code,
        "language": language,
        "status": status,
        "verdict": verdict,
        "score": score,
        "results": results or [],
        "executionTime": execution_time,
        "memoryUsed": memory_used,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
    }
