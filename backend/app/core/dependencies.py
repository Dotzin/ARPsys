from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.models import User
from app.services.auth_service import AuthService
from app.core.container import container

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_auth_service() -> AuthService:
    return container.auth_service()


def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    auth_service = get_auth_service()
    username = auth_service.verify_token(token)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = auth_service.get_user_by_username(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
