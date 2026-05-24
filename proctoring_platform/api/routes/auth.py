from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from proctoring_platform.api.deps import get_request_settings
from proctoring_platform.core.config import Settings
from proctoring_platform.core.security import create_access_token, hash_password, verify_password
from proctoring_platform.db.session import get_db
from proctoring_platform.models import User, UserRole
from proctoring_platform.schemas import LoginRequest, SignupRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_response(user: User, settings: Settings) -> TokenResponse:
    return TokenResponse(access_token=create_access_token(user.id, settings), user=user)


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(
    payload: SignupRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_request_settings),
) -> TokenResponse:
    email = payload.email.strip().lower()
    username = payload.username.strip()
    if not email or not username or len(payload.password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email, username, and 8+ char password required")

    existing = db.query(User).filter((User.email == email) | (User.username == username)).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email or username already exists")

    user = User(
        email=email,
        username=username,
        password_hash=hash_password(payload.password),
        role=UserRole.student,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _token_response(user, settings)


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_request_settings),
) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email.strip().lower()).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return _token_response(user, settings)
