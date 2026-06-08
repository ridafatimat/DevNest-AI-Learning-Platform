from pathlib import Path
from google.cloud import firestore
from google.oauth2 import service_account

BASE_DIR = Path(__file__).resolve().parents[1]
SERVICE_ACCOUNT_FILE = BASE_DIR / "serviceAccountKey.json"

credentials = service_account.Credentials.from_service_account_file(
    str(SERVICE_ACCOUNT_FILE)
)

db = firestore.Client(
    credentials=credentials,
    project=credentials.project_id,
)


# -----------------------------
# CREATE QUIZ
# -----------------------------
def create_quiz(quiz_id: str, data: dict):
    doc_ref = db.collection("quizzes").document(quiz_id)
    doc_ref.set(data)
    return {"id": quiz_id, **data}


# -----------------------------
# GET QUIZ BY ID
# -----------------------------
def get_quiz(quiz_id: str):
    doc = db.collection("quizzes").document(quiz_id).get()
    if not doc.exists:
        return None
    return doc.to_dict()


# -----------------------------
# GET QUIZ BY TITLE
# -----------------------------
def get_quiz_by_title(title: str):
    docs = db.collection("quizzes").where("title", "==", title).stream()

    for doc in docs:
        data = doc.to_dict()
        data["firestore_id"] = doc.id
        return data

    return None


# -----------------------------
# UPDATE QUIZ BY ID
# -----------------------------
def update_quiz(quiz_id: str, data: dict):
    doc_ref = db.collection("quizzes").document(quiz_id)
    if not doc_ref.get().exists:
        return None

    doc_ref.update(data)
    updated = doc_ref.get().to_dict()
    return {"id": quiz_id, **updated}


# -----------------------------
# DELETE QUIZ BY ID
# -----------------------------
def delete_quiz(quiz_id: str):
    doc_ref = db.collection("quizzes").document(quiz_id)
    if not doc_ref.get().exists:
        return False

    doc_ref.delete()
    return True
