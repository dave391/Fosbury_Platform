import asyncio

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
from app.services.strategy_service import StrategyService
from core.database import get_db
from core.enums import ExchangeName

router = APIRouter()


def _parse_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


async def render_strategy_page(
    request: Request,
    service: StrategyService,
    user_id: int,
    msg: str = None,
    success: bool = None,
    exchange_name: str = ExchangeName.DERIBIT,
    strategy_key: str = None,
    exchange_account_id: int = None,
    user_email: str = None,
):
    if isinstance(exchange_name, ExchangeName):
        exchange_name = exchange_name.value
    exchange_name = str(exchange_name or "").strip().lower()
    connected_exchanges = await service.get_connected_exchange_names(user_id)
    connected_exchanges = [str(name or "").strip().lower() for name in (connected_exchanges or []) if name]
    has_credentials = bool(connected_exchanges)
    data = await service.get_strategy_page_data(
        user_id,
        exchange_name,
        connected_exchanges=connected_exchanges,
        strategy_key=strategy_key,
        exchange_account_id=exchange_account_id,
    )
    strategies = data.get("strategies") or []
    active_count = len(strategies)
    total_allocated = sum(strategy.allocated_capital_usdc for strategy in strategies)
    return templates.TemplateResponse(
        "strategy.html",
        {
            "request": request,
            "msg": msg,
            "success": success,
            "user_id": user_id,
            "user_email": user_email,
            "active_count": active_count,
            "total_allocated": total_allocated,
            "has_strategies": active_count > 0,
            "usdc_balance": data.get("usdc_balance", 0.0),
            "has_credentials": data.get("has_credentials", has_credentials),
            "exchange_name": data.get("exchange_name", exchange_name),
            "exchanges": data.get("exchanges") or [],
            "quote_currency": data.get("quote_currency"),
            "available_strategies": data.get("available_strategies") or service.get_available_strategies(),
            "strategy_key": data.get("strategy_key"),
            "exchange_accounts": data.get("exchange_accounts") or [],
            "exchange_account_id": data.get("exchange_account_id"),
        },
    )


@router.get("/strategy", response_class=HTMLResponse)
async def strategy_page(
    request: Request,
    user_id: int = Depends(require_user_id_html_dep),
    db: AsyncSession = Depends(get_db),
):
    service = StrategyService(db)
    user_email = await get_user_email(user_id, db)
    exchange_name = request.query_params.get("exchange_name") or ExchangeName.DERIBIT
    strategy_key = request.query_params.get("strategy_key")
    exchange_account_id = request.query_params.get("exchange_account_id")
    return await render_strategy_page(
        request,
        service,
        user_id,
        exchange_name=exchange_name,
        strategy_key=strategy_key,
        exchange_account_id=_parse_int(exchange_account_id),
        user_email=user_email,
    )


@router.get("/strategy/data")
async def strategy_data(
    request: Request,
    user_id: int = Depends(require_user_id_api_dep),
    db: AsyncSession = Depends(get_db),
):
    service = StrategyService(db)
    connected_exchanges = await service.get_connected_exchange_names(user_id)
    exchange_name = request.query_params.get("exchange_name") or ""
    if isinstance(exchange_name, ExchangeName):
        exchange_name = exchange_name.value
    exchange_name = str(exchange_name or "").strip().lower()
    connected_exchanges = [str(name or "").strip().lower() for name in (connected_exchanges or []) if name]
    strategy_key = request.query_params.get("strategy_key")
    exchange_account_id = request.query_params.get("exchange_account_id")
    data = await service.get_strategy_page_data(
        user_id,
        exchange_name,
        connected_exchanges=connected_exchanges,
        strategy_key=strategy_key,
        exchange_account_id=_parse_int(exchange_account_id),
    )
    strategies = data.get("strategies") or []
    rows_data = await service.build_active_strategy_rows(user_id, strategies)
    rows = rows_data.get("rows", [])
    return JSONResponse(
        {
            "usdc_balance": data.get("usdc_balance", 0.0),
            "has_credentials": data.get("has_credentials", False),
            "exchange_name": data.get("exchange_name"),
            "allowed_assets": data.get("allowed_assets") or [],
            "min_capital_usd": data.get("min_capital_usd"),
            "quote_currency": data.get("quote_currency"),
            "strategy_key": data.get("strategy_key"),
            "available_strategies": data.get("available_strategies") or [],
            "exchanges": data.get("exchanges") or [],
            "exchange_accounts": data.get("exchange_accounts") or [],
            "exchange_account_id": data.get("exchange_account_id"),
            "active_strategies": rows,
            "active_count": len(rows),
        }
    )


@router.get("/strategy/live-balance")
async def strategy_live_balance(
    exchange_account_id: int,
    strategy_key: str,
    user_id: int = Depends(require_user_id_api_dep),
    db: AsyncSession = Depends(get_db),
):
    service = StrategyService(db)
    quote_currency = "USD"
    account = await service.exchange_service.get_exchange_account(user_id, exchange_account_id)
    if not account:
        return JSONResponse(
            {"balance": 0.0, "quote_currency": quote_currency, "error": "Invalid exchange account."}
        )
    exchange = None
    try:
        strategy_impl = service._get_strategy_impl(strategy_key)
        quote_currency = service._get_quote_currency(strategy_impl, account.exchange_name)
        exchange = await service.exchange_service.get_exchange_client_by_account(account.id)
        if not exchange:
            raise ValueError("Exchange credentials missing.")
        adapter = service.exchange_service.get_exchange_adapter(account.exchange_name)
        balance = await asyncio.wait_for(strategy_impl.fetch_usdc_balance(exchange, adapter), timeout=6)
        return JSONResponse({"balance": float(balance or 0.0), "quote_currency": quote_currency})
    except Exception as exc:
        error = "Exchange timeout." if isinstance(exc, asyncio.TimeoutError) else str(exc)
        return JSONResponse(
            {"balance": 0.0, "quote_currency": quote_currency, "error": error}
        )
    finally:
        if exchange:
            try:
                await exchange.close()
            except Exception:
                pass


@router.post("/strategy/start")
async def start_strategy(
    request: Request,
    capital_usdc: float = Form(...),
    asset: str = Form(...),
    exchange_name: str = Form(...),
    strategy_key: str = Form(None),
    exchange_account_id: int = Form(...),
    user_id: int = Depends(require_user_id_html_dep),
    db: AsyncSession = Depends(get_db),
):
    service = StrategyService(db)
    user_email = await get_user_email(user_id, db)
    try:
        await service.start_strategy(
            user_id,
            asset,
            capital_usdc,
            exchange_name,
            strategy_key=strategy_key,
            exchange_account_id=exchange_account_id,
        )
        return RedirectResponse(url="/strategy", status_code=303)
    except ValueError as e:
        return await render_strategy_page(
            request,
            service,
            user_id,
            str(e),
            False,
            exchange_name=exchange_name,
            strategy_key=strategy_key,
            exchange_account_id=exchange_account_id,
            user_email=user_email,
        )
    except Exception:
        return await render_strategy_page(
            request,
            service,
            user_id,
            "Error starting strategy.",
            False,
            exchange_name=exchange_name,
            strategy_key=strategy_key,
            exchange_account_id=exchange_account_id,
            user_email=user_email,
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
    user_email = await get_user_email(user_id, db)
    try:
        await service.add_capital(user_id, strategy_id, added_amount_usdc)
        return RedirectResponse(url="/strategy", status_code=303)
    except ValueError as e:
        return await render_strategy_page(
            request,
            service,
            user_id,
            str(e),
            False,
            user_email=user_email,
        )
    except Exception:
        return await render_strategy_page(
            request,
            service,
            user_id,
            "Error adding capital.",
            False,
            user_email=user_email,
        )


@router.post("/strategy/remove")
async def remove_strategy_capital(
    request: Request,
    strategy_id: int = Form(...),
    remove_amount_usdc: float = Form(...),
    user_id: int = Depends(require_user_id_html_dep),
    db: AsyncSession = Depends(get_db),
):
    service = StrategyService(db)
    user_email = await get_user_email(user_id, db)
    try:
        await service.remove_capital(user_id, strategy_id, remove_amount_usdc)
        return RedirectResponse(url="/strategy", status_code=303)
    except ValueError as e:
        return await render_strategy_page(
            request,
            service,
            user_id,
            str(e),
            False,
            user_email=user_email,
        )
    except Exception:
        return await render_strategy_page(
            request,
            service,
            user_id,
            "Error removing capital.",
            False,
            user_email=user_email,
        )


@router.post("/strategy/stop")
async def stop_strategy(
    request: Request,
    strategy_id: int = Form(...),
    user_id: int = Depends(require_user_id_html_dep),
    db: AsyncSession = Depends(get_db),
):
    service = StrategyService(db)
    user_email = await get_user_email(user_id, db)
    try:
        await service.stop_strategy(user_id, strategy_id)
        return RedirectResponse(url="/strategy", status_code=303)
    except ValueError as e:
        return await render_strategy_page(
            request,
            service,
            user_id,
            str(e),
            False,
            user_email=user_email,
        )
    except Exception:
        return await render_strategy_page(
            request,
            service,
            user_id,
            "Error stopping strategy.",
            False,
            user_email=user_email,
        )
