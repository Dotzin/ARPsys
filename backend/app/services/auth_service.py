import logging
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.models import User, UserCreate, pwd_context
from app.repositories.database_repository import Database
from app.config.settings import settings
from app.core.exceptions import AuthenticationException, UserNotFoundException


class AuthService:
    def __init__(self, database: Database):
        self.database = database
        self.logger = logging.getLogger(__name__)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        password = password[:72]  # Truncate to 72 bytes as bcrypt limit
        return pwd_context.hash(password)

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        try:
            print(f"Authenticating {username}")
            cursor = self.database.cursor
            assert cursor is not None
            cursor.execute(
                "SELECT id, username, email, hashed_password, full_name, is_active, api_session_token, created_at, updated_at FROM users WHERE username = ?",
                (username,)
            )
            row = cursor.fetchone()
            print(f"Row: {row}")
            if not row:
                return None

            user_dict = {
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "hashed_password": row[3],
                "full_name": row[4],
                "is_active": bool(row[5]),
                "api_session_token": row[6],
                "created_at": datetime.fromisoformat(row[7]),
                "updated_at": datetime.fromisoformat(row[8])
            }

            print(f"Hashed: {row[3]}")
            verify_result = self.verify_password(password, user_dict["hashed_password"])
            print(f"Verify result: {verify_result}")
            if not verify_result:
                return None

            return User(**user_dict)
        except Exception as e:
            print(f"Exception in authenticate_user: {e}")
            self.logger.exception(f"Error authenticating user {username}: {e}")
            raise AuthenticationException("Authentication failed") from e

    def create_user(self, user: UserCreate) -> User:
        try:
            hashed_password = self.get_password_hash(user.password)
            cursor = self.database.cursor
            assert cursor is not None
            cursor.execute(
                """
                INSERT INTO users (username, email, hashed_password, full_name)
                VALUES (?, ?, ?, ?)
                """,
                (user.username, user.email, hashed_password, user.full_name)
            )
            self.database.commit()

            # Get the created user
            user_id = cursor.lastrowid
            return User(
                id=user_id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                is_active=True,
                api_session_token=None,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        except Exception as e:
            self.logger.exception(f"Error creating user {user.username}: {e}")
            raise AuthenticationException("User creation failed") from e

    def get_user_by_username(self, username: str) -> Optional[User]:
        try:
            cursor = self.database.cursor
            assert cursor is not None
            cursor.execute(
                "SELECT id, username, email, hashed_password, full_name, is_active, api_session_token, created_at, updated_at FROM users WHERE username = ?",
                (username,)
            )
            row = cursor.fetchone()
            if not row:
                return None

            return User(
                id=row[0],
                username=row[1],
                email=row[2],
                hashed_password=row[3],
                full_name=row[4],
                is_active=bool(row[5]),
                api_session_token=row[6],
                created_at=datetime.fromisoformat(row[7]),
                updated_at=datetime.fromisoformat(row[8])
            )
        except Exception as e:
            self.logger.exception(f"Error getting user {username}: {e}")
            raise UserNotFoundException(f"User {username} not found") from e

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[str]:
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            username: str = payload.get("sub")
            if username is None:
                return None
            return username
        except JWTError:
            return None

    def update_user(self, user_id: int, updates: dict) -> User:
        try:
            cursor = self.database.cursor
            assert cursor is not None
            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [user_id]
            cursor.execute(
                f"UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                values
            )
            self.database.commit()

            # Get updated user
            return self.get_user_by_id(user_id)
        except Exception as e:
            self.logger.exception(f"Error updating user {user_id}: {e}")
            raise AuthenticationException("User update failed") from e

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        try:
            cursor = self.database.cursor
            assert cursor is not None
            cursor.execute(
                "SELECT id, username, email, hashed_password, full_name, is_active, api_session_token, created_at, updated_at FROM users WHERE id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None

            return User(
                id=row[0],
                username=row[1],
                email=row[2],
                hashed_password=row[3],
                full_name=row[4],
                is_active=bool(row[5]),
                api_session_token=row[6],
                created_at=datetime.fromisoformat(row[7]),
                updated_at=datetime.fromisoformat(row[8])
            )
        except Exception as e:
            self.logger.exception(f"Error getting user {user_id}: {e}")
            raise UserNotFoundException(f"User {user_id} not found") from e
