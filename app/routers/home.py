from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import HTMLResponse

from app.routers.shared import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="home.html", context={"request": request})
