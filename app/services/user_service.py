from fastapi import Request
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from core.models import User
from core.security import get_password_hash, verify_password, create_session_token, decode_session_token
from typing import Optional, Tuple

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    def _password_error(self, password: str, confirm_password: str) -> Optional[str]:
        if password != confirm_password:
            return "Passwords do not match"
        if len(password) < 8:
            return "Password must be at least 8 characters and include uppercase, lowercase, number, and special character"
        if not re.search(r"[A-Z]", password):
            return "Password must be at least 8 characters and include uppercase, lowercase, number, and special character"
        if not re.search(r"[a-z]", password):
            return "Password must be at least 8 characters and include uppercase, lowercase, number, and special character"
        if not re.search(r"[0-9]", password):
            return "Password must be at least 8 characters and include uppercase, lowercase, number, and special character"
        if not re.search(r"[^A-Za-z0-9]", password):
            return "Password must be at least 8 characters and include uppercase, lowercase, number, and special character"
        return None

    async def create_user(self, email: str, password: str, confirm_password: str) -> Tuple[Optional[User], str]:
        """
        Creates a new user. Returns (User, error_message).
        If successful, error_message is None.
        """
        password_error = self._password_error(password, confirm_password)
        if password_error:
            return None, password_error
        existing_user = await self.get_user_by_email(email)
        if existing_user:
            return None, "Email already registered"

        hashed_pwd = get_password_hash(password)
        new_user = User(email=email, hashed_password=hashed_pwd)
        self.db.add(new_user)

        try:
            await self.db.commit()
            return new_user, None
        except IntegrityError:
            await self.db.rollback()
            return None, "Error creating account"

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = await self.get_user_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user

    def create_session_token(self, user_id: int) -> str:
        return create_session_token(user_id)

    def get_user_id_from_token(self, token: str) -> Optional[int]:
        return decode_session_token(token)

    def get_current_user_id(self, request: Request) -> Optional[int]:
        token = request.cookies.get("session")
        return self.get_user_id_from_token(token)
