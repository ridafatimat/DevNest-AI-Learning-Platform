# app/config.py
from pathlib import Path
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, auth, storage, firestore

load_dotenv()

FIREBASE_SERVICE_ACCOUNT = os.getenv("FIREBASE_SERVICE_ACCOUNT")
FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MIN = int(os.getenv("ACCESS_TOKEN_EXPIRE_MIN", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))
RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "60"))

# Initialize Firebase Admin SDK once
if not firebase_admin._apps:
    if not FIREBASE_SERVICE_ACCOUNT:
        raise RuntimeError("FIREBASE_SERVICE_ACCOUNT env var not set")
    cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT)
    firebase_admin.initialize_app(cred, {
        "storageBucket": FIREBASE_STORAGE_BUCKET,
        "projectId": "devnest-99574"
    })

firestore_client = firestore.client()
bucket = storage.bucket()
