# app/crud_submissions.py
from app.config import firestore_client
from app.models import make_submission_doc
from datetime import datetime
from typing import Optional, List, Dict, Any

SUBMISSIONS_COLL = "submissions"
CHALLENGES_COLL = "challenges"
USER_SUBMISSIONS_COLL = "user_submissions"  # NEW COLLECTION


# ------------------ CREATE SUBMISSION ------------------
def create_submission_doc(
    submission_id: str,
    user_id: str,
    challenge_id: str,
    code: str,
    language: str,
    status: str = "queued",
):
    """Create a new submission document in Firestore."""
    doc_ref = firestore_client.collection(SUBMISSIONS_COLL).document(submission_id)
    
    data = make_submission_doc(
        submission_id=submission_id,
        user_id=user_id,
        challenge_id=challenge_id,
        code=code,
        language=language,
        status=status,
    )
    
    doc_ref.set(data)
    return data


# ------------------ GET SUBMISSION BY ID ------------------
def get_submission_doc(submission_id: str):
    """Get a submission document by ID."""
    doc = firestore_client.collection(SUBMISSIONS_COLL).document(submission_id).get()
    if not doc.exists:
        return None
    return doc.to_dict()


# ------------------ UPDATE SUBMISSION ------------------
def update_submission_doc(submission_id: str, patch: Dict[str, Any]):
    """Update a submission document."""
    ref = firestore_client.collection(SUBMISSIONS_COLL).document(submission_id)
    patch["updatedAt"] = datetime.utcnow()
    ref.update(patch)
    return ref.get().to_dict()


# ------------------ GET SUBMISSIONS BY USER ------------------
def get_user_submissions(user_id: str, limit: int = 50, challenge_id: Optional[str] = None):
    """Get submissions by user ID, optionally filtered by challenge."""
    query = firestore_client.collection(SUBMISSIONS_COLL).where("userId", "==", user_id)
    
    if challenge_id:
        query = query.where("challengeId", "==", challenge_id)
    
    try:
        from google.cloud.firestore_v1.base_query import Query
        docs = query.order_by("createdAt", direction=Query.DESCENDING).limit(limit).get()
    except Exception as e:
        # Fallback if order_by fails (e.g., no index)
        print(f"Warning: order_by failed, using simple query: {e}")
        docs = query.limit(limit).get()
    
    return [doc.to_dict() for doc in docs]


# ------------------ GET SUBMISSIONS BY CHALLENGE ------------------
def get_challenge_submissions(challenge_id: str, limit: int = 100):
    """Get all submissions for a specific challenge."""
    try:
        from google.cloud.firestore_v1.base_query import Query
        docs = (
            firestore_client.collection(SUBMISSIONS_COLL)
            .where("challengeId", "==", challenge_id)
            .order_by("createdAt", direction=Query.DESCENDING)
            .limit(limit)
            .get()
        )
    except Exception as e:
        # Fallback if order_by fails (e.g., no index)
        print(f"Warning: order_by failed, using simple query: {e}")
        docs = (
            firestore_client.collection(SUBMISSIONS_COLL)
            .where("challengeId", "==", challenge_id)
            .limit(limit)
            .get()
        )
    return [doc.to_dict() for doc in docs]


# ------------------ GET CHALLENGE WITH TEST CASES ------------------
def get_challenge_doc(challenge_id: str):
    """
    Get a challenge document with test cases.
    Used by B3 to fetch test cases for judging submissions.
    Returns visible and hidden test cases separately.
    """
    doc = firestore_client.collection(CHALLENGES_COLL).document(challenge_id).get()
    if not doc.exists:
        return None
    
    challenge_data = doc.to_dict()
    
    # Separate visible and hidden test cases
    visible_tests = [tc for tc in challenge_data.get("testCases", []) if not tc.get("hidden", False)]
    hidden_tests = [tc for tc in challenge_data.get("testCases", []) if tc.get("hidden", False)]
    
    return {
        **challenge_data,
        "visibleTestCases": visible_tests,
        "hiddenTestCases": hidden_tests,
    }


# ==================== NEW: USER SUBMISSIONS CRUD ====================

def create_user_submission(submission_data: Dict[str, Any]) -> str:
    """
    Create a new user submission document in Firestore.
    Returns the document ID.
    """
    # Add server timestamp
    submission_data['created_at'] = datetime.utcnow()
    submission_data['updated_at'] = datetime.utcnow()
    
    # Add to Firestore
    doc_ref = firestore_client.collection(USER_SUBMISSIONS_COLL).document()
    doc_ref.set(submission_data)
    
    print(f"✅ User submission saved: {doc_ref.id}")
    print(f"👤 User: {submission_data.get('user_name')}")
    print(f"📝 Challenge: {submission_data.get('challenge_title')}")
    print(f"🔤 Language: {submission_data.get('language')}")
    print(f"✔️ Tests Passed: {submission_data.get('all_tests_passed')}")
    
    return doc_ref.id


def get_user_submissions_by_name(user_name: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get all submissions by a specific user name.
    """
    try:
        from google.cloud.firestore_v1.base_query import Query
        docs = (
            firestore_client.collection(USER_SUBMISSIONS_COLL)
            .where("user_name", "==", user_name)
            .order_by("submitted_at", direction=Query.DESCENDING)
            .limit(limit)
            .get()
        )
    except Exception as e:
        print(f"Warning: order_by failed, using simple query: {e}")
        docs = (
            firestore_client.collection(USER_SUBMISSIONS_COLL)
            .where("user_name", "==", user_name)
            .limit(limit)
            .get()
        )
    
    submissions = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        submissions.append(data)
    
    return submissions


def get_user_submission_by_id(submission_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific user submission by ID.
    """
    doc = firestore_client.collection(USER_SUBMISSIONS_COLL).document(submission_id).get()
    if not doc.exists:
        return None
    
    data = doc.to_dict()
    data['id'] = doc.id
    return data


def get_all_user_submissions(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get all user submissions (for admin/analytics).
    """
    try:
        from google.cloud.firestore_v1.base_query import Query
        docs = (
            firestore_client.collection(USER_SUBMISSIONS_COLL)
            .order_by("submitted_at", direction=Query.DESCENDING)
            .limit(limit)
            .get()
        )
    except Exception as e:
        print(f"Warning: order_by failed, using simple query: {e}")
        docs = firestore_client.collection(USER_SUBMISSIONS_COLL).limit(limit).get()
    
    submissions = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        submissions.append(data)
    
    return submissions