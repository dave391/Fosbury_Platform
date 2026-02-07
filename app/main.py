from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.routers.shared import UnauthorizedAPI
from app.routers.shared import UnauthorizedHTML
from app.routes import router
from core.config import settings


docs_enabled = settings.EXPOSE_DOCS
app = FastAPI(
    title="Fosbury Platform",
    docs_url="/docs" if docs_enabled else None,
    redoc_url="/redoc" if docs_enabled else None,
    openapi_url="/openapi.json" if docs_enabled else None,
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(router)


@app.exception_handler(UnauthorizedHTML)
async def unauthorized_html_handler(request: Request, exc: UnauthorizedHTML):
    return RedirectResponse(url="/login", status_code=303)


@app.exception_handler(UnauthorizedAPI)
async def unauthorized_api_handler(request: Request, exc: UnauthorizedAPI):
    return JSONResponse({"error": "unauthorized"}, status_code=401)
