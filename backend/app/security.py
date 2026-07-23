import os
import hmac
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-me-now")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
TOKEN_HOURS = int(os.getenv("TOKEN_HOURS", "8"))

bearer = HTTPBearer(auto_error=False)


def verify_admin(username: str, password: str) -> bool:
    """Constant-time comparison so timing can't leak the credentials."""
    ok_user = hmac.compare_digest(username or "", ADMIN_USERNAME)
    ok_pass = hmac.compare_digest(password or "", ADMIN_PASSWORD)
    return ok_user and ok_pass


def create_token(username: str) -> str:
    payload = {
        "sub": username,
        "role": "admin",
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def require_admin(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> str:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sign in to continue.")
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired. Sign in again.")
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid session. Sign in again.")
    if payload.get("role") != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access only.")
    return payload.get("sub")
