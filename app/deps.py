# app/deps.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils import decode_token
from app import crud

bearer_scheme = HTTPBearer(auto_error=True)  # <-- tells Swagger this is auth

from jwt import ExpiredSignatureError, InvalidTokenError

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        print("Unexpected decode error:", e)
        raise HTTPException(status_code=401, detail="Invalid token")

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    uid = payload.get("sub")
    role = payload.get("role")

    try:
        user = crud.get_user_doc(uid)
    except Exception as e:
        print("Database error:", e)
        raise HTTPException(status_code=500, detail="Internal server error")

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"uid": uid, "role": role}





async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    try:
        token = credentials.credentials
        payload = decode_token(token)
        if not payload:
            return None
        return {"uid": payload.get("sub")}
    except:
        return None
    
    # ------------------- ADMIN-ONLY DEPENDENCY -------------------
async def get_admin_user(current_user=Depends(get_current_user)):
    """
    Dependency to allow only admin users.
    Raises 403 if the user is not admin.
    """
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

