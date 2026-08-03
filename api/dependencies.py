import os
import json
from datetime import datetime, timedelta, timezone
from typing import Generator, Optional, Set
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from core.config import config
from database.database import SessionLocal
from database.models import User
from database.repositories.user_repo import UserRepository
from security.security_manager import SecurityManager
from security.auth import SessionToken

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = config.session_timeout_minutes * 16  # 8 hours default

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
REVOKED_TOKENS_FILE = os.path.join(config.data_dir, ".revoked_tokens.json")


def _get_crypto():
    """Return an AESCryptoEngine instance for token revocation file encryption."""
    try:
        from security.crypto import AESCryptoEngine
        return AESCryptoEngine()
    except Exception:
        return None


def _load_revoked_tokens() -> Set[str]:
    """Load revoked tokens set from encrypted file."""
    if not os.path.exists(REVOKED_TOKENS_FILE):
        return set()
    try:
        with open(REVOKED_TOKENS_FILE, "rb") as f:
            encrypted = f.read()
        crypto = _get_crypto()
        if crypto and encrypted:
            decrypted = crypto.decrypt_bytes(encrypted)
            return set(json.loads(decrypted.decode("utf-8")))
        with open(REVOKED_TOKENS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def _save_revoked_tokens(revoked_set: Set[str]) -> None:
    """Save revoked tokens set into encrypted file."""
    try:
        os.makedirs(os.path.dirname(REVOKED_TOKENS_FILE), exist_ok=True)
        raw = json.dumps(list(revoked_set)).encode("utf-8")
        crypto = _get_crypto()
        if crypto:
            encrypted = crypto.encrypt_bytes(raw)
            with open(REVOKED_TOKENS_FILE, "wb") as f:
                f.write(encrypted)
        else:
            with open(REVOKED_TOKENS_FILE, "w", encoding="utf-8") as f:
                f.write(json.dumps(list(revoked_set)))
    except Exception:
        pass


def is_token_revoked(token: str) -> bool:
    """Check if token is in persistent revoked set."""
    return token in _load_revoked_tokens()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database session context."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    secret = config.jwt_secret
    return jwt.encode(to_encode, secret, algorithm=ALGORITHM)


def revoke_token(token: str) -> None:
    """Revoke a token on logout."""
    revoked_set = _load_revoked_tokens()
    revoked_set.add(token)
    _save_revoked_tokens(revoked_set)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Validate JWT bearer token and inject security context into SecurityManager."""
    if is_token_revoked(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, config.jwt_secret, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        username: str = payload.get("username")
        role: str = payload.get("role")
        if sub is None or username is None:
            raise credentials_exception
        user_id = int(sub)
    except (JWTError, ValueError, TypeError):
        raise credentials_exception

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if user is None or not user.is_active:
        raise credentials_exception

    # Synchronize current SecurityManager singleton session
    sm = SecurityManager()
    sm.current_session = SessionToken(
        token_str=token,
        user_id=user.id,
        user_email=user.email or user.username,
        role=user.role or "Audit Partner"
    )

    return user
