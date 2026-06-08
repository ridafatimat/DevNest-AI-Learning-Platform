# app/schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# ---------------------------------
# AUTH / USER SCHEMAS (YOUR EXISTING CODE)
# ---------------------------------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    prefs: Optional[dict] = None


class UserOut(BaseModel):
    id: str
    email: EmailStr
    name: Optional[str] = None
    username: Optional[str] = None
    role: str
    bio: Optional[str] = None
    prefs: Optional[dict] = None
    joinedAt: Optional[datetime] = None


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    sub: str
    exp: int
    role: Optional[str] = None


# ---------------------------------
# AI / REVIEW SCHEMAS (UPDATED TO MATCH FRONTEND)
# ---------------------------------
class Submission(BaseModel):
    userId: str
    code: str = Field(default="# No code submitted")
    language: str = "python"
    question: str = Field(default="No question provided")
    submissionId: Optional[str] = None
    includeHints: bool = False
    includeExplain: bool = False
    includeStudyPlan: bool = False


class AIReviewResponse(BaseModel):
    summary: str  # ✅ Changed from reviewedCode
    issues: List[str]  # ✅ Changed from feedback
    suggestions: List[str]  # ✅ Added
    confidence: float
    modelVersion: str  # ✅ Added


class HintResponse(BaseModel):
    hint: str  # ✅ Changed from hints: List[str]
    hintType: str  # ✅ Added


class ExplainResponse(BaseModel):
    explanation: str
    modelVersion: str  # ✅ Added


class StudyPlanResponse(BaseModel):
    topics: List[str]  # ✅ Changed from steps
    schedule: List[str]  # ✅ Added
    modelVersion: str  # ✅ Added


# Judge/Submission Schemas

class SubmissionStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    FINISHED = "finished"
    ERROR = "error"

class RunCodeRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=100000)
    language: str = Field(..., description="Programming language (python, java, javascript, cpp, etc.)")
    stdin: Optional[str] = None
    expected_output: Optional[str] = None

class TestCaseResult(BaseModel):
    test_case_id: str
    passed: bool
    status: str
    status_id: int
    stdout: str
    stderr: str
    expected_output: Optional[str] = None
    compile_output: Optional[str] = None
    time: Optional[float] = None
    memory: Optional[int] = None
    exit_code: Optional[int] = None
    is_hidden: bool = False

class RunCodeResponse(BaseModel):
    status: str
    status_id: int
    stdout: str
    stderr: str
    compile_output: Optional[str] = None
    time: Optional[float] = None
    memory: Optional[int] = None
    exit_code: Optional[int] = None
    passed: Optional[bool] = None
    token: Optional[str] = None

class SubmitCodeRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=100000)
    language: str = Field(..., description="Programming language (python, java, javascript, cpp, etc.)")
    challenge_id: str = Field(..., description="ID of the challenge being submitted")

class SubmissionResult(BaseModel):
    verdict: str
    score: float
    passed_tests: int
    total_tests: int
    results: List[TestCaseResult]

class SubmissionResponse(BaseModel):
    id: str
    user_id: str
    challenge_id: str
    code: str
    language: str
    status: SubmissionStatus
    verdict: Optional[str] = None
    score: Optional[float] = None
    results: Optional[List[TestCaseResult]] = None
    created_at: datetime
    updated_at: datetime
    execution_time: Optional[float] = None
    memory_used: Optional[int] = None

class WebhookPayload(BaseModel):
    submission_id: str
    status: SubmissionStatus
    verdict: Optional[str] = None
    score: Optional[float] = None
    results: Optional[List[TestCaseResult]] = None