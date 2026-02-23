from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.routers.shared import get_user_email
from app.routers.shared import require_user_id_api_dep
from app.routers.shared import require_user_id_html_dep
from app.routers.shared import templates
from app.services.dashboard_service import DashboardService
from core.database import get_db

router = APIRouter()


def _parse_str(value: str):
    if value is None:
        return None
    value = value.strip()
    return value or None


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user_id: int = Depends(require_user_id_html_dep),
    db: AsyncSession = Depends(get_db),
):
    strategy_type = _parse_str(request.query_params.get("strategy_type"))
    exchange = _parse_str(request.query_params.get("exchange"))
    asset = _parse_str(request.query_params.get("asset"))
    service = DashboardService(db)
    data = await service.get_dashboard_data(
        user_id,
        strategy_type,
        exchange,
        asset,
        include_equity_series=False,
        include_historical_series=False,
    )
    user_email = await get_user_email(user_id, db)
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user_email": user_email, **data},
    )


@router.get("/dashboard/data")
async def dashboard_data(
    request: Request,
    user_id: int = Depends(require_user_id_api_dep),
    db: AsyncSession = Depends(get_db),
):
    strategy_type = _parse_str(request.query_params.get("strategy_type"))
    exchange = _parse_str(request.query_params.get("exchange"))
    asset = _parse_str(request.query_params.get("asset"))
    service = DashboardService(db)
    data = await service.get_dashboard_data(
        user_id,
        strategy_type,
        exchange,
        asset,
        include_equity_series=True,
        include_historical_series=False,
    )
    return JSONResponse(
        {
            "metrics": data.get("metrics"),
            "total_balance_usdc": data.get("total_balance_usdc"),
            "current_balance_usdc": data.get("current_balance_usdc"),
            "equity_series": data.get("equity_series"),
            "equity_min": data.get("equity_min"),
            "equity_max": data.get("equity_max"),
            "equity_dates": data.get("equity_dates"),
            "historical_metrics": data.get("historical_metrics"),
        }
    )
