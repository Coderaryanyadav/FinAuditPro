import os
import json
import secrets
from datetime import datetime, timedelta, timezone

from typing import Generator, Optional, Set
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

import core.config
from database.database import SessionLocal
from database.models import User
from database.repositories.user_repo import UserRepository
from security.security_manager import SecurityManager
from security.auth import SessionToken

ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def _get_crypto():

    """Return an AESCryptoEngine instance for token revocation file encryption."""
    try:
        from security.crypto import AESCryptoEngine
        return AESCryptoEngine()
    except Exception:
        return None


def _get_revoked_file_path() -> str:
    return os.path.join(core.config.config.data_dir, ".revoked_tokens.json")



def _load_revoked_tokens() -> Set[str]:
    """Load revoked tokens set from encrypted file."""
    rev_file = _get_revoked_file_path()
    if not os.path.exists(rev_file):
        return set()
    try:
        with open(rev_file, "rb") as f:
            encrypted = f.read()
        if not encrypted:
            return set()
        crypto = _get_crypto()
        if crypto:
            try:
                decrypted = crypto.decrypt_bytes(encrypted)
                return set(json.loads(decrypted.decode("utf-8")))
            except Exception:
                return set()
        return set(json.loads(encrypted.decode("utf-8")))
    except Exception:
        return set()


def _save_revoked_tokens(revoked_set: Set[str]) -> None:
    """Save revoked tokens set into encrypted file."""
    try:
        rev_file = _get_revoked_file_path()
        os.makedirs(os.path.dirname(rev_file), exist_ok=True)
        raw = json.dumps(list(revoked_set)).encode("utf-8")
        crypto = _get_crypto()
        if crypto:
            encrypted = crypto.encrypt_bytes(raw)
            with open(rev_file, "wb") as f:
                f.write(encrypted)
        else:
            with open(rev_file, "w", encoding="utf-8") as f:
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
    """Create a signed JWT access token with unique JTI claim."""
    to_encode = data.copy()
    expire_mins = core.config.config.session_timeout_minutes * 16
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=expire_mins))
    to_encode.update({
        "exp": expire,
        "jti": secrets.token_hex(16)
    })
    secret = core.config.config.jwt_secret
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
        payload = jwt.decode(token, core.config.config.jwt_secret, algorithms=[ALGORITHM])
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
