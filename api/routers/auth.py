from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_db, get_current_user, create_access_token, oauth2_scheme, revoke_token
from api.schemas.auth import LoginRequest, TokenResponse, UserProfile
from database.models import User
from database.repositories.user_repo import UserRepository
from services.auth_service import AuthenticationService
from core.exceptions import AuthenticationError, ValidationError

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user credentials and issue signed JWT access token."""
    user_repo = UserRepository(db)
    auth_service = AuthenticationService(user_repo)
    try:
        user = auth_service.login(username=request.username, password=request.password)
    except (AuthenticationError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={
        "sub": str(user.id),
        "username": user.username,
        "role": user.role or "Audit Partner"
    })

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_minutes=480,
        user_id=user.id,
        username=user.username,
        role=user.role or "Audit Partner"
    )


@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme), current_user: User = Depends(get_current_user)):
    """Revoke current active JWT token."""
    revoke_token(token)
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserProfile)
def get_profile(current_user: User = Depends(get_current_user)):
    """Retrieve active user profile details."""
    return current_user
