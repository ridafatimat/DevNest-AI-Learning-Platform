# app/judge.py
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from app.schemas import (
    RunCodeRequest,
    RunCodeResponse,
    SubmitCodeRequest,
    SubmissionResponse,
    SubmissionStatus,
    WebhookPayload,
)
from app.deps import get_current_user
from app.judge_service import judge_service
from app import crud_submissions
from datetime import datetime
import uuid
from typing import Dict, Any

router = APIRouter(prefix="/judge", tags=["judge"])


# --------------------------------------------------------
# NEW: SIMPLE RUN (NO LOGIN, FOR "RUN" BUTTON IN FRONTEND)
# --------------------------------------------------------
@router.post("/simple-run")
async def simple_run(payload: dict):
    """
    A simple run endpoint for the frontend Run button.
    Executes code once and returns raw output.
    No authentication, no expected output, no test cases.
    """
    code = payload.get("code")
    language = payload.get("language", "python")
    stdin = payload.get("stdin", "")

    if not code:
        raise HTTPException(status_code=400, detail="Code is required")

    try:
        result = await judge_service.run_code(
            code=code,
            language=language,
            stdin=stdin,
            expected_output=None
        )

        return {
            "status": result.get("status"),
            "stdout": result.get("stdout"),
            "stderr": result.get("stderr"),
            "time": result.get("time"),
            "memory": result.get("memory"),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Execution failed: {str(e)}"
        )


# ------------------- POST /run -------------------
# AUTH REMOVED: anyone can call this endpoint now
@router.post("/run", response_model=RunCodeResponse)
async def run_code(
    payload: RunCodeRequest,
):
    """
    Run code with Judge service.
    Authentication REMOVED so it can be used freely from the frontend.
    """
    try:
        result = await judge_service.run_code(
            code=payload.code,
            language=payload.language,
            stdin=payload.stdin,
            expected_output=payload.expected_output,
        )

        return RunCodeResponse(
            status=result["status"],
            status_id=result["status_id"],
            stdout=result["stdout"],
            stderr=result["stderr"],
            compile_output=result.get("compile_output"),
            time=result.get("time"),
            memory=result.get("memory"),
            exit_code=result.get("exit_code"),
            passed=result.get("passed"),
            token=result.get("token"),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code execution failed: {str(e)}")


# ------------------- POST /submit -------------------
@router.post("/submit", response_model=SubmissionResponse)
async def submit_code(
    payload: SubmitCodeRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    user_id = current_user["uid"]

    challenge = crud_submissions.get_challenge_doc(payload.challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    visible_test_cases = challenge.get("visibleTestCases", [])
    hidden_test_cases = challenge.get("hiddenTestCases", [])

    if not visible_test_cases and not hidden_test_cases:
        raise HTTPException(status_code=400, detail="Challenge has no test cases")

    submission_id = str(uuid.uuid4())
    submission = crud_submissions.create_submission_doc(
        submission_id=submission_id,
        user_id=user_id,
        challenge_id=payload.challenge_id,
        code=payload.code,
        language=payload.language,
        status=SubmissionStatus.QUEUED.value,
    )

    background_tasks.add_task(
        process_submission,
        submission_id=submission_id,
        code=payload.code,
        language=payload.language,
        visible_test_cases=visible_test_cases,
        hidden_test_cases=hidden_test_cases,
    )

    return SubmissionResponse(
        id=submission["id"],
        user_id=submission["userId"],
        challenge_id=submission["challengeId"],
        code=submission["code"],
        language=submission["language"],
        status=SubmissionStatus(submission["status"]),
        verdict=submission.get("verdict"),
        score=submission.get("score"),
        results=None,
        created_at=submission["createdAt"],
        updated_at=submission["UpdatedAt"] if "UpdatedAt" in submission else submission["updatedAt"],
        execution_time=submission.get("executionTime"),
        memory_used=submission.get("memoryUsed"),
    )


# ------------------- GET /submissions/{id} -------------------
@router.get("/submissions/{submission_id}", response_model=SubmissionResponse)
async def get_submission(
    submission_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    submission = crud_submissions.get_submission_doc(submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if submission["userId"] != current_user["uid"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to view this submission")

    results = submission.get("results", [])
    sanitized_results = []
    for result in results:
        sanitized_result = result.copy()
        if result.get("is_hidden", False):
            sanitized_result["stdout"] = ""
            sanitized_result["stderr"] = ""
            sanitized_result["expected_output"] = None
        sanitized_results.append(sanitized_result)

    return SubmissionResponse(
        id=submission["id"],
        user_id=submission["userId"],
        challenge_id=submission["challengeId"],
        code=submission["code"],
        language=submission["language"],
        status=SubmissionStatus(submission["status"]),
        verdict=submission.get("verdict"),
        score=submission.get("score"),
        results=sanitized_results,
        created_at=submission["createdAt"],
        updated_at=submission["updatedAt"],
        execution_time=submission.get("executionTime"),
        memory_used=submission.get("memoryUsed"),
    )


# ------------------- GET /submissions/user/{user_id} -------------------
@router.get("/submissions/user/{user_id}", response_model=list[SubmissionResponse])
async def get_user_submissions(
    user_id: str,
    challenge_id: str = None,
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_user),
):

    if user_id != current_user["uid"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to view these submissions")

    submissions = crud_submissions.get_user_submissions(
        user_id=user_id,
        limit=limit,
        challenge_id=challenge_id,
    )

    return [
        SubmissionResponse(
            id=sub["id"],
            user_id=sub["userId"],
            challenge_id=sub["challengeId"],
            code=sub["code"],
            language=sub["language"],
            status=SubmissionStatus(sub["status"]),
            verdict=sub.get("verdict"),
            score=sub.get("score"),
            results=None,
            created_at=sub["createdAt"],
            updated_at=sub["updatedAt"],
            execution_time=sub.get("executionTime"),
            memory_used=sub.get("memoryUsed"),
        )
        for sub in submissions
    ]


# ------------------- POST /hooks/submission-result -------------------
@router.post("/hooks/submission-result")
async def submission_result_webhook(
    payload: WebhookPayload,
    background_tasks: BackgroundTasks,
):
    submission_id = payload.submission_id

    update_data = {
        "status": payload.status.value,
        "verdict": payload.verdict,
        "score": payload.score,
        "results": [r.dict() for r in payload.results] if payload.results else [],
    }

    submission = crud_submissions.update_submission_doc(submission_id, update_data)

    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    return {"status": "ok", "submission_id": submission_id}


# ------------------- Background Task: Process Submission -------------------
async def process_submission(
    submission_id: str,
    code: str,
    language: str,
    visible_test_cases: list,
    hidden_test_cases: list,
):
    try:
        crud_submissions.update_submission_doc(submission_id, {"status": SubmissionStatus.RUNNING.value})

        result = await judge_service.judge_submission(
            code=code,
            language=language,
            test_cases=visible_test_cases,
            hidden_test_cases=hidden_test_cases,
        )

        results = result.get("results", [])
        total_time = sum(r.get("time", 0) or 0 for r in results)
        total_memory = sum(r.get("memory", 0) or 0 for r in results)
        avg_time = total_time / len(results) if results else None
        avg_memory = int(total_memory / len(results)) if results else None

        update_data = {
            "status": SubmissionStatus.FINISHED.value,
            "verdict": result["verdict"],
            "score": result["score"],
            "results": [r for r in results],
            "executionTime": avg_time,
            "memoryUsed": avg_memory,
        }

        crud_submissions.update_submission_doc(submission_id, update_data)

    except Exception as e:
        crud_submissions.update_submission_doc(
            submission_id,
            {
                "status": SubmissionStatus.ERROR.value,
                "verdict": "Error",
                "results": [{"error": str(e)}],
            },
        )
        print(f"Error processing submission {submission_id}: {str(e)}")
