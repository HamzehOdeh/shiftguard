"""
JWT Authentication — token creation, validation, password hashing, role enforcement.
"""

from datetime import datetime, timedelta
from typing import Optional
import hashlib
import hmac
import base64
import json
import os

from .config import settings


def hash_password(password: str) -> str:
    """Hash password using PBKDF2-SHA256."""
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
    return base64.b64encode(salt + key).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    decoded = base64.b64decode(hashed.encode())
    salt = decoded[:32]
    stored_key = decoded[32:]
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
    return hmac.compare_digest(key, stored_key)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.JWT_EXPIRATION_MINUTES))
    to_encode["exp"] = int(expire.timestamp())
    to_encode["iat"] = int(datetime.utcnow().timestamp())

    header = base64.urlsafe_b64encode(
        json.dumps({"alg": settings.JWT_ALGORITHM, "typ": "JWT"}).encode()
    ).rstrip(b"=").decode()

    payload = base64.urlsafe_b64encode(
        json.dumps(to_encode).encode()
    ).rstrip(b"=").decode()

    signing_input = f"{header}.{payload}"
    signature = hmac.new(
        settings.SECRET_KEY.encode(), signing_input.encode(), hashlib.sha256
    ).digest()
    sig_encoded = base64.urlsafe_b64encode(signature).rstrip(b"=").decode()

    return f"{header}.{payload}.{sig_encoded}"


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, sig_b64 = parts

        signing_input = f"{header_b64}.{payload_b64}"
        expected_sig = hmac.new(
            settings.SECRET_KEY.encode(), signing_input.encode(), hashlib.sha256
        ).digest()
        expected_encoded = base64.urlsafe_b64encode(expected_sig).rstrip(b"=").decode()

        if not hmac.compare_digest(sig_b64, expected_encoded):
            return None

        padding = 4 - len(payload_b64) % 4
        payload_b64 += "=" * padding
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))

        if payload.get("exp", 0) < int(datetime.utcnow().timestamp()):
            return None

        return payload
    except Exception:
        return None


def create_refresh_token(user_id: str) -> str:
    """Create a refresh token with longer expiration."""
    return create_access_token(
        {"sub": user_id, "type": "refresh"},
        timedelta(days=settings.JWT_REFRESH_EXPIRATION_DAYS)
    )
