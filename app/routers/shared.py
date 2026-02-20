from typing import Optional

from fastapi import Depends
from fastapi import Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user_service import UserService
from core.database import get_db

templates = Jinja2Templates(directory="app/templates")


def get_current_user_id(request: Request, db: AsyncSession) -> Optional[int]:
    return UserService(db).get_current_user_id(request)


async def get_user_email(user_id: int, db: AsyncSession) -> Optional[str]:
    user = await UserService(db).get_user_by_id(user_id)
    if not user:
        return None
    return user.email


class UnauthorizedHTML(Exception):
    pass


class UnauthorizedAPI(Exception):
    pass


def require_user_id_html_dep(request: Request, db: AsyncSession = Depends(get_db)) -> int:
    user_id = get_current_user_id(request, db)
    if not user_id:
        raise UnauthorizedHTML()
    return user_id


def require_user_id_api_dep(request: Request, db: AsyncSession = Depends(get_db)) -> int:
    user_id = get_current_user_id(request, db)
    if not user_id:
        raise UnauthorizedAPI()
    return user_id
