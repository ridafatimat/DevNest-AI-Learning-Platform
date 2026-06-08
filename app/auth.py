# app/auth.py

from fastapi import APIRouter, HTTPException, Depends
from app.schemas import UserCreate, Token, UserOut, UserUpdate
from app.config import firestore_client
from firebase_admin import auth as fb_auth
from app.utils import create_access_token, create_refresh_token, decode_token
from app.deps import get_current_user
from pydantic import BaseModel
import os
import httpx
from app import crud
import time
import random
import string
from urllib.parse import urlparse, parse_qs


# ------------------- USERNAME GENERATOR -------------------
def generate_unique_username(name: str) -> str:
    base = (name or "user").lower().replace(" ", "")

    # Try 5 random numeric suffixes
    for _ in range(5):
        suffix = "".join(random.choices(string.digits, k=4))
        username = f"{base}{suffix}"

        exists = (
            firestore_client.collection("users")
            .where("username", "==", username)
            .limit(1)
            .get()
        )

        if not exists:
            return username

    # Fallback for heavy collisions
    return f"{base}{int(time.time())}"


class LoginInput(BaseModel):
    email: str
    password: str


router = APIRouter(prefix="/auth", tags=["auth"])


# ------------------- SIGNUP -------------------
@router.post("/signup", response_model=UserOut)
async def signup(payload: UserCreate):
    try:
        user = fb_auth.create_user(
            email=payload.email,
            password=payload.password,
            display_name=payload.name,
        )

        username = generate_unique_username(user.display_name)

        crud.create_user_doc(
            uid=user.uid,
            email=user.email,
            name=user.display_name,
            role="student",
            username=username,
            email_verified=False,
        )

        # Default role
        fb_auth.set_custom_user_claims(user.uid, {"role": "student"})

    except fb_auth.EmailAlreadyExistsError:
        raise HTTPException(status_code=400, detail="Email already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return crud.get_user_doc(user.uid)


# ------------------- LOGIN -------------------
@router.post("/login", response_model=Token)
async def login(payload: LoginInput):
    FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")
    if not FIREBASE_API_KEY:
        raise HTTPException(status_code=500, detail="FIREBASE_API_KEY missing")

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            json={
                "email": payload.email,
                "password": payload.password,
                "returnSecureToken": True,
            },
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    data = resp.json()
    uid = data["localId"]

    user = fb_auth.get_user(uid)
    role = (user.custom_claims or {}).get("role", "student")

    access_token, access_exp = create_access_token(uid, role)
    refresh_token, refresh_exp = create_refresh_token(uid)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=access_exp,
    )


# ------------------- REFRESH TOKEN -------------------
@router.post("/refresh", response_model=Token)
async def refresh(refresh_token: str):
    payload = decode_token(refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    uid = payload.get("sub")
    user = fb_auth.get_user(uid)
    role = (user.custom_claims or {}).get("role", "student")

    access_token, access_exp = create_access_token(uid, role)
    new_refresh, refresh_exp = create_refresh_token(uid)

    return Token(
        access_token=access_token,
        refresh_token=new_refresh,
        expires_in=access_exp,
    )


# ------------------- CURRENT USER -------------------
@router.get("/me", response_model=UserOut)
async def me(current_user=Depends(get_current_user)):
    uid = current_user["uid"]
    profile = crud.get_user_doc(uid)

    if not profile:
        raise HTTPException(status_code=404, detail="User not found")

    return profile


# ------------------- GET USER BY USERNAME -------------------
@router.get("/users/{username}", response_model=UserOut)
async def get_user(username: str, current_user=Depends(get_current_user)):
    profile = crud.get_user_by_username(username)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    return profile


# ------------------- UPDATE USER -------------------
@router.put("/users/{username}", response_model=UserOut)
async def update_user(username: str, payload: UserUpdate, current_user=Depends(get_current_user)):
    profile = crud.get_user_by_username(username)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")

    # Owner OR admin only
    if profile["id"] != current_user["uid"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not allowed to edit this user")

    updated = crud.update_user_doc(
        profile["id"], payload.dict(exclude_unset=True)
    )
    return updated


# ------------------- SEND VERIFICATION EMAIL -------------------
@router.get("/send_verification_email")
async def send_verification_email(email: str):
    try:
        link = fb_auth.generate_email_verification_link(email)
        return {"verification_link": link}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------- CONFIRM EMAIL VERIFICATION -------------------
@router.post("/confirm_email")
async def confirm_email(oob_code: str):
    FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")
    if not FIREBASE_API_KEY:
        raise HTTPException(status_code=500, detail="FIREBASE_API_KEY missing")

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={FIREBASE_API_KEY}"

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json={"oobCode": oob_code})

    data = resp.json()

    if resp.status_code != 200:
        message = data.get("error", {}).get("message", "Invalid OOB code")
        raise HTTPException(status_code=400, detail=message)

    return {"message": "Email verified successfully"}


# ------------------- REQUEST PASSWORD RESET -------------------
@router.post("/request_password_reset")
async def request_password_reset(email: str):
    try:
        link = fb_auth.generate_password_reset_link(email)
        return {"reset_link": link}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------- CONFIRM PASSWORD RESET (NEW API ENDPOINT) -------------------
@router.post("/confirm_password_reset")
async def confirm_password_reset(reset_url: str, new_password: str):
    # Extract oobCode from full URL
    query = parse_qs(urlparse(reset_url).query)
    oob_code = query.get("oobCode", [None])[0]

    if not oob_code:
        raise HTTPException(status_code=400, detail="Invalid reset URL")

    FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")
    if not FIREBASE_API_KEY:
        raise HTTPException(status_code=500, detail="FIREBASE_API_KEY missing")

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={FIREBASE_API_KEY}"

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            json={"oobCode": oob_code, "password": new_password},
        )

    if resp.status_code != 200:
        data = resp.json()
        message = data.get("error", {}).get("message", "Invalid OOB code")
        raise HTTPException(status_code=400, detail=message)

    return {"message": "Password updated successfully"}
