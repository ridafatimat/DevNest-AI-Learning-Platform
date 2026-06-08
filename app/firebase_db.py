# app/firebase_db.py
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore

# Build absolute path to service account file in project root
BASE_DIR = Path(__file__).resolve().parents[1]
SERVICE_ACCOUNT_FILE = BASE_DIR / "serviceAccountKey.json"   # make sure the file really has .json

# Initialize app only once
if not firebase_admin._apps:
    cred = credentials.Certificate(str(SERVICE_ACCOUNT_FILE))
    firebase_admin.initialize_app(cred)

db = firestore.client()
