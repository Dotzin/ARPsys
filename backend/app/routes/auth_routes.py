from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse, RedirectResponse
from app.models import User, UserCreate, UserUpdate, Token
from app.services.auth_service import AuthService
from app.core.container import container
from app.core.exceptions import AuthenticationException, UserNotFoundException
import logging
import os
from typing import Optional

router = APIRouter()
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# Dependency functions
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


def get_optional_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[User]:
    if token is None:
        return None
    auth_service = get_auth_service()
    username = auth_service.verify_token(token)
    if username is None:
        return None
    user = auth_service.get_user_by_username(username)
    return user


@router.post("/register", response_model=User)
async def register(user_data: UserCreate, auth_service: AuthService = Depends(get_auth_service)):
    try:
        # Check if user already exists
        existing_user = auth_service.get_user_by_username(user_data.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already registered")

        user = auth_service.create_user(user_data)
        logger.info(f"User {user.username} registered successfully")
        return user
    except AuthenticationException as e:
        logger.exception(f"Registration failed for {user_data.username}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error during registration: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        print(f"Login attempt for {form_data.username}", flush=True)
        user = auth_service.authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = auth_service.create_access_token(data={"sub": user.username})
        logger.info(f"User {user.username} logged in successfully")
        return Token(access_token=access_token, token_type="bearer")
    except AuthenticationException as e:
        logger.exception(f"Login failed for {form_data.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.exception(f"Unexpected error during login: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.put("/me", response_model=User)
async def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        updates = user_update.dict(exclude_unset=True)
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        updated_user = auth_service.update_user(current_user.id, updates)
        logger.info(f"User {current_user.username} updated successfully")
        return updated_user
    except AuthenticationException as e:
        logger.exception(f"Update failed for {current_user.username}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error during update: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/")
async def root(current_user: Optional[User] = Depends(get_optional_current_user)):
    if current_user:
        return FileResponse(os.path.join("static", "index.html"))
    else:
        return FileResponse(os.path.join("static", "login.html"))


@router.get("/login")
async def login_page():
    return FileResponse(os.path.join("static", "login.html"))


@router.get("/register")
async def register_page():
    return FileResponse(os.path.join("static", "register.html"))


@router.get("/settings")
async def settings_page(current_user: Optional[User] = Depends(get_optional_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    return FileResponse(os.path.join("static", "settings.html"))


@router.get("/integrations")
async def integrations_page(current_user: Optional[User] = Depends(get_optional_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    return FileResponse(os.path.join("static", "integrations.html"))


@router.get("/daily")
async def daily_page(current_user: Optional[User] = Depends(get_optional_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    return FileResponse(os.path.join("static", "daily.html"))
