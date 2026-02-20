import base64
import secrets

from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import PlainTextResponse
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.routers.shared import UnauthorizedAPI
from app.routers.shared import UnauthorizedHTML
from app.routes import router
from core.config import settings
from core.security import create_session_token, decode_session_token


docs_enabled = settings.EXPOSE_DOCS
app = FastAPI(
    title="Fosbury Platform",
    docs_url="/docs" if docs_enabled else None,
    redoc_url="/redoc" if docs_enabled else None,
    openapi_url="/openapi.json" if docs_enabled else None,
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(router)


@app.middleware("http")
async def session_refresh_middleware(request: Request, call_next):
    token = request.cookies.get("session")
    user_id = decode_session_token(token) if token else None
    response = await call_next(request)
    if request.url.path in ("/login", "/logout", "/register"):
        if token and not user_id:
            response.delete_cookie("session")
        return response
    if token and user_id:
        refreshed = create_session_token(user_id)
        response.set_cookie(
            key="session",
            value=refreshed,
            httponly=True,
            samesite="lax",
        )
    elif token and not user_id:
        response.delete_cookie("session")
    return response


@app.middleware("http")
async def basic_auth_middleware(request: Request, call_next):
    if not settings.BASIC_AUTH_ENABLED:
        return await call_next(request)
    if request.url.path == "/health":
        return await call_next(request)
    auth_header = request.headers.get("authorization", "")
    if not auth_header.lower().startswith("basic "):
        return PlainTextResponse(
            "Unauthorized",
            status_code=401,
            headers={"WWW-Authenticate": "Basic"},
        )
    token = auth_header.split(" ", 1)[1].strip()
    try:
        decoded = base64.b64decode(token).decode("utf-8")
        username, password = decoded.split(":", 1)
    except Exception:
        return PlainTextResponse(
            "Unauthorized",
            status_code=401,
            headers={"WWW-Authenticate": "Basic"},
        )
    valid_user = secrets.compare_digest(username, settings.BASIC_AUTH_USERNAME)
    valid_pass = secrets.compare_digest(password, settings.BASIC_AUTH_PASSWORD)
    if not (valid_user and valid_pass):
        return PlainTextResponse(
            "Unauthorized",
            status_code=401,
            headers={"WWW-Authenticate": "Basic"},
        )
    return await call_next(request)


@app.get("/health")
async def health_check():
    return JSONResponse({"status": "ok"})


@app.exception_handler(UnauthorizedHTML)
async def unauthorized_html_handler(request: Request, exc: UnauthorizedHTML):
    return RedirectResponse(url="/login", status_code=303)


@app.exception_handler(UnauthorizedAPI)
async def unauthorized_api_handler(request: Request, exc: UnauthorizedAPI):
    return JSONResponse({"error": "unauthorized"}, status_code=401)
