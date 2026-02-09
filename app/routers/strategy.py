from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.routers.shared import require_user_id_api_dep
from app.routers.shared import require_user_id_html_dep
from app.routers.shared import templates
from app.services.strategy_service import StrategyService
from app.services.strategies.cash_funding.rules import get_exchange_rules
from core.database import get_db
from core.enums import ExchangeName

router = APIRouter()


async def render_strategy_page(
    request: Request,
    service: StrategyService,
    user_id: int,
    msg: str = None,
    success: bool = None,
    exchange_name: str = ExchangeName.DERIBIT,
):
    if isinstance(exchange_name, ExchangeName):
        exchange_name = exchange_name.value
    connected_exchanges = await service.get_connected_exchange_names(user_id)
    if connected_exchanges and exchange_name not in connected_exchanges:
        exchange_name = connected_exchanges[0]
    exchanges = connected_exchanges if connected_exchanges else [e.value for e in ExchangeName]
    strategies = await service.get_active_strategies(user_id)
    active_count = len(strategies)
    total_allocated = sum(strategy.allocated_capital_usdc for strategy in strategies)
    try:
        quote_currency = (get_exchange_rules(exchange_name) or {}).get("quote") or "USDC"
    except Exception:
        quote_currency = "USDC"
    return templates.TemplateResponse(
        "strategy.html",
        {
            "request": request,
            "msg": msg,
            "success": success,
            "user_id": user_id,
            "active_count": active_count,
            "total_allocated": total_allocated,
            "has_strategies": active_count > 0,
            "usdc_balance": 0.0,
            "has_credentials": None,
            "exchange_name": exchange_name,
            "exchanges": exchanges,
            "quote_currency": quote_currency,
        },
    )


@router.get("/strategy", response_class=HTMLResponse)
async def strategy_page(
    request: Request,
    user_id: int = Depends(require_user_id_html_dep),
    db: AsyncSession = Depends(get_db),
):
    service = StrategyService(db)
    exchange_name = request.query_params.get("exchange_name") or ExchangeName.DERIBIT
    return await render_strategy_page(request, service, user_id, exchange_name=exchange_name)


@router.get("/strategy/data")
async def strategy_data(
    request: Request,
    user_id: int = Depends(require_user_id_api_dep),
    db: AsyncSession = Depends(get_db),
):
    service = StrategyService(db)
    connected_exchanges = await service.get_connected_exchange_names(user_id)
    exchange_name = request.query_params.get("exchange_name") or (
        connected_exchanges[0] if connected_exchanges else ExchangeName.DERIBIT
    )
    if isinstance(exchange_name, ExchangeName):
        exchange_name = exchange_name.value
    if connected_exchanges and exchange_name not in connected_exchanges:
        exchange_name = connected_exchanges[0]
    data = await service.get_strategy_page_data(
        user_id, exchange_name, connected_exchanges=connected_exchanges
    )
    strategies = data.get("strategies") or []
    rows_data = await service.build_active_strategy_rows(user_id, strategies)
    rows = rows_data.get("rows", [])
    total_allocated = sum(row.get("allocated_capital_usdc", 0.0) for row in rows) if rows else 0.0
    return JSONResponse(
        {
            "usdc_balance": data.get("usdc_balance", 0.0),
            "has_credentials": data.get("has_credentials", False),
            "exchange_name": data.get("exchange_name"),
            "allowed_assets": data.get("allowed_assets") or [],
            "min_capital_usd": data.get("min_capital_usd"),
            "quote_currency": data.get("quote_currency"),
            "active_strategies": rows,
            "active_count": len(rows),
            "total_allocated_usdc": total_allocated,
        }
    )


@router.post("/strategy/start")
async def start_strategy(
    request: Request,
    capital_usdc: float = Form(...),
    asset: str = Form(...),
    exchange_name: str = Form(...),
    user_id: int = Depends(require_user_id_html_dep),
    db: AsyncSession = Depends(get_db),
):
    service = StrategyService(db)
    try:
        await service.start_strategy(user_id, asset, capital_usdc, exchange_name)
        return RedirectResponse(url="/strategy", status_code=303)
    except ValueError as e:
        return await render_strategy_page(request, service, user_id, str(e), False, exchange_name=exchange_name)
    except Exception:
        return await render_strategy_page(
            request, service, user_id, "Errore avvio strategia.", False, exchange_name=exchange_name
        )


@router.post("/strategy/add")
async def add_strategy_capital(
    request: Request,
    strategy_id: int = Form(...),
    added_amount_usdc: float = Form(...),
    user_id: int = Depends(require_user_id_html_dep),
    db: AsyncSession = Depends(get_db),
):
    service = StrategyService(db)
    try:
        await service.add_capital(user_id, strategy_id, added_amount_usdc)
        return RedirectResponse(url="/strategy", status_code=303)
    except ValueError as e:
        return await render_strategy_page(request, service, user_id, str(e), False)
    except Exception:
        return await render_strategy_page(request, service, user_id, "Errore aggiunta capitale.", False)


@router.post("/strategy/remove")
async def remove_strategy_capital(
    request: Request,
    strategy_id: int = Form(...),
    remove_amount_usdc: float = Form(...),
    user_id: int = Depends(require_user_id_html_dep),
    db: AsyncSession = Depends(get_db),
):
    service = StrategyService(db)
    try:
        await service.remove_capital(user_id, strategy_id, remove_amount_usdc)
        return RedirectResponse(url="/strategy", status_code=303)
    except ValueError as e:
        return await render_strategy_page(request, service, user_id, str(e), False)
    except Exception:
        return await render_strategy_page(request, service, user_id, "Errore rimozione capitale.", False)


@router.post("/strategy/stop")
async def stop_strategy(
    request: Request,
    strategy_id: int = Form(...),
    user_id: int = Depends(require_user_id_html_dep),
    db: AsyncSession = Depends(get_db),
):
    service = StrategyService(db)
    try:
        await service.stop_strategy(user_id, strategy_id)
        return RedirectResponse(url="/strategy", status_code=303)
    except ValueError as e:
        return await render_strategy_page(request, service, user_id, str(e), False)
    except Exception:
        return await render_strategy_page(request, service, user_id, "Errore stop strategia.", False)
