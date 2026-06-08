# app/main.py

# ✅ LOAD ENVIRONMENT VARIABLES FIRST (BEFORE ALL OTHER IMPORTS)
from dotenv import load_dotenv
import os
from pathlib import Path

# Get the project root directory (parent of 'app')
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / '.env'

# Load .env file
load_dotenv(dotenv_path=env_path)

# Verify it's loaded (remove this after testing)
print(f"🔑 Loading .env from: {env_path}")
print(f"🔑 .env exists: {env_path.exists()}")
print(f"🔑 OPENAI_API_KEY loaded: {bool(os.getenv('OPENAI_API_KEY'))}")

# -----------------------------
# NOW IMPORT EVERYTHING ELSE
# -----------------------------
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# -----------------------------
# Middleware
# -----------------------------
from app.middleware import SimpleRateLimiter

# -----------------------------
# B1: AUTH ROUTES
# -----------------------------
from app.auth import router as auth_router

# -----------------------------
# B3: JUDGE / CODE EXECUTION
# -----------------------------
from app.judge import router as judge_router

# -----------------------------
# Additional Routes (AI + Analytics)
# -----------------------------
from app.routes.ai import router as ai_router
from app.routes.analytics import router as analytics_router

# -----------------------------
# B2: CHALLENGES & QUIZZES (Routers)
# -----------------------------
from app.challenges.router import router as challenges_router
from app.quizzes.router import router as quizzes_router

# -----------------------------
# CRUD SUBMISSIONS
# -----------------------------
from app.crud_submissions import (
    create_user_submission,
    get_user_submissions_by_name,
    get_user_submission_by_id,
    get_all_user_submissions
)

# ======================================================
#                 MAIN GATEWAY APPLICATION
# ======================================================
app = FastAPI(
    title="DevNest - Gateway (Auth + AI + B2 Challenges and Quizzes + B3 Judge Service)",
    description=(
       
    ),
    version="1.0.0"
)

# ------------------------------------------------------
# CORS CONFIGURATION (FIXED)
# ------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"  # Allow all origins for development (remove in production)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------
# RATE LIMITING
# ------------------------------------------------------
app.add_middleware(SimpleRateLimiter)

# ------------------------------------------------------
# PYDANTIC MODELS FOR USER SUBMISSIONS
# ------------------------------------------------------
class TestResult(BaseModel):
    input: str
    expected: str
    stdout: str
    stderr: str
    compile_output: str
    status: str
    status_id: int
    time: Optional[float] = None
    memory: Optional[int] = None

class UserSubmissionCreate(BaseModel):
    user_name: str
    challenge_id: str
    challenge_title: str
    difficulty: str
    topics: List[str]
    code: str
    language: str
    test_results: List[TestResult]
    all_tests_passed: bool
    submitted_at: str

# ------------------------------------------------------
# USER SUBMISSIONS ENDPOINTS
# ------------------------------------------------------
@app.post("/api/user-submissions", tags=["user-submissions"])
async def submit_user_solution(submission: UserSubmissionCreate):
    """
    User se submissions receive karta hai aur Firestore mein save karta hai
    """
    try:
        # Convert to dict
        submission_data = submission.dict()
        
        # Save to Firestore
        doc_id = create_user_submission(submission_data)
        
        return {
            "success": True,
            "message": "Submission saved successfully",
            "submission_id": doc_id,
            "user_name": submission.user_name,
            "challenge_title": submission.challenge_title,
            "all_tests_passed": submission.all_tests_passed,
            "submitted_at": submission.submitted_at
        }
        
    except Exception as e:
        print(f"❌ Error saving submission: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/user-submissions/{user_name}", tags=["user-submissions"])
async def get_submissions_by_user(user_name: str, limit: int = 50):
    """
    Specific user ki submissions retrieve karta hai
    """
    try:
        submissions = get_user_submissions_by_name(user_name, limit)
        
        return {
            "success": True,
            "count": len(submissions),
            "user_name": user_name,
            "submissions": submissions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/user-submissions/id/{submission_id}", tags=["user-submissions"])
async def get_submission_detail(submission_id: str):
    """
    Specific submission ki details retrieve karta hai
    """
    try:
        submission = get_user_submission_by_id(submission_id)
        
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        return {
            "success": True,
            "submission": submission
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/user-submissions", tags=["user-submissions"])
async def get_all_submissions(limit: int = 100):
    """
    All user submissions retrieve karta hai (admin/analytics ke liye)
    """
    try:
        submissions = get_all_user_submissions(limit)
        
        return {
            "success": True,
            "count": len(submissions),
            "submissions": submissions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------
# REGISTER ROUTERS (Everything in ONE /docs)
# ------------------------------------------------------
# B1 Auth
app.include_router(auth_router, prefix="/auth", tags=["auth"])

# Additional
app.include_router(ai_router, prefix="/ai", tags=["ai"])
app.include_router(analytics_router, prefix="/analytics", tags=["analytics"])

# B2 Services (Challenges + Quizzes)
app.include_router(challenges_router, prefix="/challenges", tags=["challenges"])
app.include_router(quizzes_router, prefix="/quizzes", tags=["quizzes"])

# B3 Judge
app.include_router(judge_router, prefix="/judge", tags=["judge"])

# ------------------------------------------------------
# ROOT ENDPOINT
# ------------------------------------------------------
@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "DevNest Backend",
        "modules": [
            "Auth & User Management (B1)",
            "AI Services",
            "Analytics Services",
            "Challenges API (B2)",
            "Quizzes API (B2)",
            "Judge / Code Execution Service (B3)",
            "User Submissions API"
        ]
    }