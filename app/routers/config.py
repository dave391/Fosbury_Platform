from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.routers.shared import get_user_email
from app.routers.shared import require_user_id_api_dep
from app.routers.shared import require_user_id_html_dep
from app.routers.shared import templates
from app.services.exchange_service import ExchangeService
from core.database import get_db
from core.enums import ExchangeName

router = APIRouter()


@router.get("/config", response_class=HTMLResponse)
async def config_page(
    request: Request,
    user_id: int = Depends(require_user_id_html_dep),
    db: AsyncSession = Depends(get_db),
):
    service = ExchangeService(db)
    user_email = await get_user_email(user_id, db)
    credentials = await service.get_configured_exchanges(user_id)
    return templates.TemplateResponse(
        "config.html",
        {
            "request": request,
            "user_id": user_id,
            "user_email": user_email,
            "has_credentials": bool(credentials),
            "credentials": [],
            "exchanges": [e.value for e in ExchangeName],
        },
    )


@router.get("/config/data")
async def config_data(
    request: Request,
    user_id: int = Depends(require_user_id_api_dep),
    db: AsyncSession = Depends(get_db),
):
    service = ExchangeService(db)
    credentials = await service.get_configured_exchanges(user_id)
    return JSONResponse({"credentials": credentials})


@router.post("/config")
async def save_config(
    request: Request,
    api_key: str = Form(...),
    api_secret: str = Form(...),
    exchange_name: str = Form(...),
    label: str = Form(...),
    user_id: int = Depends(require_user_id_html_dep),
    db: AsyncSession = Depends(get_db),
):
    service = ExchangeService(db)
    user_email = await get_user_email(user_id, db)
    try:
        await service.save_credentials(user_id, api_key, api_secret, exchange_name, label=label)
        msg = "Keys verified and saved successfully!"
        success = True
    except ValueError as e:
        msg = str(e)
        success = False
    except Exception:
        msg = "Error saving credentials."
        success = False

    return templates.TemplateResponse(
        "config.html",
        {
            "request": request,
            "msg": msg,
            "success": success,
            "user_email": user_email,
            "has_credentials": bool(await service.get_configured_exchanges(user_id)),
            "credentials": [],
            "exchanges": [e.value for e in ExchangeName],
        },
    )


@router.post("/config/disconnect")
async def disconnect_credentials(
    request: Request,
    credentials_id: int = Form(...),
    user_id: int = Depends(require_user_id_html_dep),
    db: AsyncSession = Depends(get_db),
):
    service = ExchangeService(db)
    await service.delete_credentials(user_id, credentials_id)

    return RedirectResponse(url="/config", status_code=303)
