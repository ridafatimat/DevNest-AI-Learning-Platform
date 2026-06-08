# app/utils.py
import time
from datetime import datetime, timedelta
import jwt
from app.config import JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MIN, REFRESH_TOKEN_EXPIRE_DAYS

def create_access_token(subject: str, role: str):
    now = datetime.utcnow()
    exp = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MIN)
    payload = {"sub": subject, "role": role, "exp": exp}
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token, int(exp.timestamp())

def create_refresh_token(subject: str):
    now = datetime.utcnow()
    exp = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": subject, "exp": exp}
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token, int(exp.timestamp())

def decode_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
