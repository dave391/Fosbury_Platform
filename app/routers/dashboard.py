from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.routers.shared import require_user_id_api_dep
from app.routers.shared import require_user_id_html_dep
from app.routers.shared import templates
from app.services.dashboard_service import DashboardService
from core.database import get_db

router = APIRouter()


def _parse_int(value: str):
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user_id: int = Depends(require_user_id_html_dep),
    db: AsyncSession = Depends(get_db),
):
    strategy_id = _parse_int(request.query_params.get("strategy_id"))
    service = DashboardService(db)
    data = await service.get_dashboard_data(user_id, strategy_id)
    return templates.TemplateResponse("dashboard.html", {"request": request, **data})


@router.get("/dashboard/data")
async def dashboard_data(
    request: Request,
    user_id: int = Depends(require_user_id_api_dep),
    db: AsyncSession = Depends(get_db),
):
    strategy_id = _parse_int(request.query_params.get("strategy_id"))
    service = DashboardService(db)
    data = await service.get_dashboard_data(user_id, strategy_id)
    selected_strategy = data.get("selected_strategy")
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
            "historical_series": data.get("historical_series"),
            "historical_min": data.get("historical_min"),
            "historical_max": data.get("historical_max"),
            "historical_dates": data.get("historical_dates"),
            "selected_strategy": {
                "id": selected_strategy.id,
                "asset": selected_strategy.asset,
            }
            if selected_strategy
            else None,
        }
    )
