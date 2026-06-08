# app/firebase.py

"""
Compatibility wrapper so code like `from app.firebase import db`
works, while the real Firestore setup lives in firebase_db.py.
"""

from .firebase_db import db  # re-export the db from firebase_db
