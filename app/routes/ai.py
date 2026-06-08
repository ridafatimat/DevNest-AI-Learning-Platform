from fastapi import APIRouter, HTTPException
from ..firebase import db
from ..schemas import Submission, AIReviewResponse, HintResponse,ExplainResponse,StudyPlanResponse
from ..services.ai_client import review_code, call_openai,explain_question,generate_study_plan
# from ..services.rate_limiter import limiter
from app.services.rate_limiter import limiter
from datetime import datetime

router = APIRouter(prefix="/ai")

@router.post("/review", response_model=AIReviewResponse)
def review(sub: Submission):
    limiter.check(sub.userId)

    result = review_code(sub.dict())

    # Save to Firestore (with createdAt)
    db.collection("AIReview").document().set({
        "submissionId": sub.submissionId,
        "summary": result["summary"],
        "issues": result["issues"],
        "suggestions": result["suggestions"],
        "confidence": result["confidence"],
        "modelVersion": result["modelVersion"],
        "createdAt": datetime.utcnow().isoformat()
    })

    return result


@router.post("/hint", response_model=HintResponse)
def hint(sub: Submission):
    limiter.check(sub.userId)

    prompt = f"Give a short hint and hintType for this code:\n{sub.content}"

    res = call_openai(prompt)

    return HintResponse(
        hint=res.get("summary", "Try checking logic."),
        hintType="general"
    )

# ⭐ NEW: Explain Question
@router.post("/explain", response_model=ExplainResponse)
def explain(sub: Submission):
    limiter.check(sub.userId)

    res = explain_question(sub.content)

    return ExplainResponse(
        explanation=res.get("explanation", "No explanation."),
        modelVersion=res.get("modelVersion", "fallback")
    )


# ⭐ NEW: Study Plan Generation
@router.post("/studyplan", response_model=StudyPlanResponse)
def studyplan(sub: Submission):
    limiter.check(sub.userId)

    res = generate_study_plan(sub.content)

    return StudyPlanResponse(
        topics=res.get("topics", []),
        schedule=res.get("schedule", []),
        modelVersion=res.get("modelVersion", "fallback")
    )


# ⭐ NEW: Model List Endpoint
@router.get("/models")
def models():
    return {
        "models": [
            {"name": "gpt-4o-mini", "cost": "cheap, fast"},
            {"name": "gpt-4o", "cost": "higher accuracy"},
            {"name": "mock-v1", "cost": "dev mode (no key)"}
        ]
    }
