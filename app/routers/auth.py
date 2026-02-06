from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.routers.shared import templates
from app.services.user_service import UserService
from core.database import get_db

router = APIRouter()


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
async def register_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    _, error = await service.create_user(email, password)

    if error:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": error},
        )

    return RedirectResponse(url="/login", status_code=303)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    user = await service.authenticate_user(email, password)

    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid credentials"},
        )

    response = RedirectResponse(url="/dashboard", status_code=303)
    session_token = service.create_session_token(user.id)
    response.set_cookie(
        key="session",
        value=session_token,
        httponly=True,
        samesite="lax",
    )
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("session")
    return response

