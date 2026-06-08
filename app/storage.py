# app/storage.py
from app.config import bucket
import uuid

def upload_avatar(file_bytes: bytes, filename: str, content_type: str):
    """
    Uploads bytes to Firebase Storage and returns a public URL (if bucket is public or via signed URL).
    For production consider signed URLs and security rules.
    """
    blob_name = f"avatars/{uuid.uuid4()}_{filename}"
    blob = bucket.blob(blob_name)
    blob.upload_from_string(file_bytes, content_type=content_type)
    # Make public (optional). In prod, manage with security rules and signed URLs.
    try:
        blob.make_public()
        return blob.public_url
    except Exception:
        # fallback: return storage path for generating signed URL elsewhere
        return f"gs://{bucket.name}/{blob_name}"
