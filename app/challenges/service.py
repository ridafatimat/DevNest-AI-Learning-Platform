# app/challenges/service.py
from pathlib import Path
from google.cloud import firestore
from google.oauth2 import service_account

# Base directory of the project (…/devnest-backend)
BASE_DIR = Path(__file__).resolve().parents[1]
SERVICE_ACCOUNT_FILE = BASE_DIR / "serviceAccountKey.json"

credentials = service_account.Credentials.from_service_account_file(
    str(SERVICE_ACCOUNT_FILE)
)

db = firestore.Client(
    credentials=credentials,
    project=credentials.project_id,
)


# ---------------------------------------------------------
# CREATE CHALLENGE
# ---------------------------------------------------------
def create_challenge(challenge_id: int, data: dict):
    doc_ref = db.collection("challenges").document(str(challenge_id))
    doc_ref.set(data)
    return data


# ---------------------------------------------------------
# GET CHALLENGE BY ID
# ---------------------------------------------------------
def get_challenge_by_id(challenge_id: int):
    doc = db.collection("challenges").document(str(challenge_id)).get()
    if not doc.exists:
        return None
    return doc.to_dict()


# ---------------------------------------------------------
# UPDATE CHALLENGE
# ---------------------------------------------------------
def update_challenge(challenge_id: int, data: dict):
    doc_ref = db.collection("challenges").document(str(challenge_id))
    if not doc_ref.get().exists:
        return None
    doc_ref.update(data)
    return data


# ---------------------------------------------------------
# DELETE CHALLENGE
# ---------------------------------------------------------
def delete_challenge(challenge_id: int):
    doc_ref = db.collection("challenges").document(str(challenge_id))
    if not doc_ref.get().exists:
        return False
    doc_ref.delete()
    return True


# ---------------------------------------------------------
# SEARCH BY TITLE
# ---------------------------------------------------------
def get_challenge_by_title(title: str):
    docs = db.collection("challenges").where("title", "==", title).stream()
    for doc in docs:
        return doc.to_dict()
    return None


# ---------------------------------------------------------
# LIST CHALLENGES
# ---------------------------------------------------------
def list_challenges(limit: int = 50, topic: str | None = None,
                    difficulty: str | None = None):
    query = db.collection("challenges")

    if topic:
        query = query.where("topics", "array_contains", topic)

    if difficulty:
        query = query.where("difficulty", "==", difficulty)

    query = query.limit(limit)

    results = []
    for doc in query.stream():
        data = doc.to_dict()
        results.append(data)

    return results
