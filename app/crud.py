# app/crud.py
from app.config import firestore_client
from app.models import make_user_doc
from datetime import datetime

USERS_COLL = "users"


# ------------------ CREATE USER ------------------
def create_user_doc(
    uid: str,
    email: str,
    name: str = None,
    role: str = "student",
    username: str = "",
    email_verified: bool = False
):
    doc_ref = firestore_client.collection(USERS_COLL).document(uid)

    data = {
        "id": uid,
        "email": email,
        "name": name,
        "role": role,
        "username": username,
        "emailVerified": email_verified,

        # default user profile fields
        "bio": "",
        "prefs": {},
        "avatarUrl": None,

        "joinedAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
    }

    doc_ref.set(data)
    return data



# ------------------ GET USER BY FIREBASE UID ------------------
def get_user_doc(uid: str):
    doc = firestore_client.collection(USERS_COLL).document(uid).get()
    if not doc.exists:
        return None
    return doc.to_dict()



# ------------------ UPDATE USER DOCUMENT ------------------
def update_user_doc(uid: str, patch: dict):
    ref = firestore_client.collection(USERS_COLL).document(uid)
    patch["updatedAt"] = datetime.utcnow()
    ref.update(patch)
    return ref.get().to_dict()



# ------------------ GET USER BY USERNAME ------------------
def get_user_by_username(username: str):
    docs = (
        firestore_client.collection(USERS_COLL)
        .where("username", "==", username)
        .limit(1)
        .get()
    )

    if not docs:
        return None
    return docs[0].to_dict()
