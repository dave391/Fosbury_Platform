from typing import List, Dict, Any, Tuple, Optional
import asyncio
import logging
import ccxt.async_support as ccxt
from app.services.exchanges.base import ExchangeAdapter


logger = logging.getLogger(__name__)


def _raw_error(exc: Exception):
    response = getattr(exc, "response", None)
    if response is not None:
        return response
    body = getattr(exc, "body", None)
    if body is not None:
        return body
    if getattr(exc, "args", None):
        return exc.args
    return str(exc)


class BitmexExchange(ExchangeAdapter):
    async def get_client(self, api_key: str, api_secret: str):
        return ccxt.bitmex({"apiKey": api_key, "secret": api_secret, "enableRateLimit": True})

    async def validate_credentials(self, api_key: str, api_secret: str) -> None:
        exchange = None
        try:
            exchange = await self.get_client(api_key, api_secret)
            await exchange.fetch_balance()
        finally:
            if exchange is not None:
                await exchange.close()

    async def fetch_active_currencies(self, exchange) -> List[str]:
        try:
            balance = await exchange.fetch_balance()
            totals = balance.get("total") or {}
            active = [code for code, value in totals.items() if value and float(value) != 0]
            return active or list(totals.keys())
        except Exception:
            return []

    async def fetch_transaction_logs(
        self, exchange, currency: str, start_ms: int, end_ms: int
    ) -> List[Dict[str, Any]]:
        try:
            entries = await exchange.fetch_ledger(currency, start_ms)
        except Exception:
            return []
        items = []
        for entry in entries or []:
            timestamp = entry.get("timestamp")
            if timestamp is None or timestamp < start_ms or timestamp > end_ms:
                continue
            entry_type = entry.get("type")
            symbol = entry.get("symbol") or entry.get("info", {}).get("symbol") or currency
            currency_code = entry.get("currency") or currency
            if entry_type in ("funding", "swap", "settlement"):
                funding = entry.get("amount")
                if funding is None:
                    continue
                items.append(
                    {
                        "instrument": symbol,
                        "entry_type": "funding",
                        "currency": currency_code,
                        "timestamp": timestamp,
                        "funding": float(funding),
                        "fee": None,
                    }
                )
            elif entry_type in ("fee", "trade"):
                fee = None
                entry_fee = entry.get("fee")
                if isinstance(entry_fee, dict):
                    fee = entry_fee.get("cost")
                if fee is None:
                    fee = entry.get("amount")
                if fee is None:
                    continue
                items.append(
                    {
                        "instrument": symbol,
                        "entry_type": "fee",
                        "currency": currency_code,
                        "timestamp": timestamp,
                        "funding": None,
                        "fee": float(fee),
                    }
                )
        return items

    async def fetch_quote_balance(self, exchange, quote: str) -> float:
        balance = await exchange.fetch_balance()
        info = balance.get("info")
        info_items = info if isinstance(info, list) else [info]
        for item in info_items:
            if not isinstance(item, dict):
                continue
            wallet = item.get("walletBalance")
            currency = item.get("currency")
            if wallet is None:
                continue
            currency_code = str(currency or "").upper()
            quote_code = str(quote or "").upper()
            if currency_code == quote_code:
                currency_info = (getattr(exchange, "currencies", {}) or {}).get(quote_code)
                precision = currency_info.get("precision") if isinstance(currency_info, dict) else None
                if precision is not None and int(precision) > 0:
                    try:
                        return float(wallet) / (10 ** int(precision))
                    except Exception:
                        pass
                if quote_code == "USDT":
                    return float(wallet) / 1_000_000
                return float(wallet)
        free = balance.get("free", {})
        total = balance.get("total", {})
        value = free.get(quote)
        if value is None:
            value = total.get(quote)
        return float(value or 0)

    async def fetch_strategy_deltas(
        self, exchange, strategy, start_ms: int, end_ms: int
    ) -> Tuple[float, float]:
        config = strategy.config or {}
        quote = config.get("quote") or "USDT"
        asset = strategy.asset
        spot_id = config.get("spot_id")
        perp_id = config.get("perp_id")
        def to_float(value):
            try:
                return float(value)
            except (TypeError, ValueError):
                return None

        def normalize_amount(value, currency):
            number = to_float(value)
            if number is None:
                return None
            currency_code = str(currency or "")
            if currency_code == "XBt":
                return number / 100000000
            if currency_code in ("USDt", "USDT"):
                return number / 1000000
            return number

        def normalize_value(value: str) -> str:
            return "".join(ch for ch in str(value or "").upper() if ch.isalnum())

        quote_code = "".join(ch for ch in str(quote or "").upper() if ch.isalnum())
        def quote_matches(value: str) -> bool:
            value_norm = normalize_value(value)
            if not value_norm:
                return False
            if value_norm == quote_code:
                return True
            return False

        candidates = [c for c in (spot_id, perp_id, asset) if c]
        candidate_norms = [normalize_value(c) for c in candidates if c]
        def symbol_matches(value: str) -> bool:
            value_norm = normalize_value(value)
            if not value_norm:
                return False
            for candidate in candidate_norms:
                if candidate and candidate in value_norm:
                    return True
            return False

        funding_delta = 0.0
        fees_delta = 0.0
        start_index = 0
        limit = 500
        keep_fetching = True
        while keep_fetching:
            params = {
                "reverse": True,
                "count": limit,
                "start": start_index,
            }
            try:
                batch = await exchange.request("execution/tradeHistory", "private", "GET", params)
            except Exception:
                break
            rows = batch if isinstance(batch, list) else []
            if not rows:
                break
            for item in rows:
                ts_str = item.get("timestamp") or item.get("execTime") or item.get("transactTime")
                ts = exchange.parse8601(ts_str)
                if ts is None:
                    continue
                if ts < start_ms:
                    keep_fetching = False
                    break
                if ts > end_ms:
                    continue
                symbol = item.get("symbol")
                if candidate_norms and not symbol_matches(symbol):
                    continue
                exec_comm_ccy = item.get("execCommCcy") or item.get("settlCurrency") or item.get("currency")
                if not quote_matches(exec_comm_ccy):
                    continue
                exec_type = item.get("execType")
                fee_type = item.get("feeType")
                is_funding = exec_type == "Funding" or fee_type == "Funding"
                realised_pnl = normalize_amount(item.get("realisedPnl"), exec_comm_ccy)
                if is_funding and realised_pnl is not None:
                    funding_delta += float(realised_pnl)
                if not is_funding:
                    fee_cost = normalize_amount(item.get("execComm"), exec_comm_ccy)
                    if fee_cost is not None:
                        fees_delta += float(fee_cost)
            if len(rows) < limit:
                break
            start_index += limit
            rate_limit = getattr(exchange, "rateLimit", 0) or 0
            if rate_limit:
                await asyncio.sleep(rate_limit / 1000)
        return funding_delta, fees_delta

    async def fetch_position_info(self, exchange, symbol: str) -> Optional[Dict[str, Any]]:
        def to_float(value):
            try:
                return float(value)
            except (TypeError, ValueError):
                return None

        def normalize_amount(value, currency):
            number = to_float(value)
            if number is None:
                return None
            currency_code = str(currency or "")
            if currency_code == "XBt":
                return number / 100000000
            if currency_code in ("USDt", "USDT"):
                return number / 1000000
            return number

        def normalize(value: str) -> str:
            return "".join(ch for ch in str(value or "").upper() if ch.isalnum())

        positions = None
        try:
            positions = await exchange.fetch_positions([symbol])
        except Exception:
            try:
                positions = await exchange.fetch_positions()
            except Exception:
                return None
        if not isinstance(positions, list) or not positions:
            return None

        symbol_norm = normalize(symbol)
        position = None
        for item in positions:
            if not isinstance(item, dict):
                continue
            info = item.get("info") if isinstance(item.get("info"), dict) else {}
            candidate = item.get("symbol") or info.get("symbol")
            candidate_norm = normalize(candidate)
            if symbol_norm and candidate_norm and (
                symbol_norm == candidate_norm
                or symbol_norm in candidate_norm
                or candidate_norm in symbol_norm
            ):
                position = item
                break
        if position is None:
            position = positions[0] if len(positions) == 1 else None
        if not isinstance(position, dict):
            return None

        data = position.get("info") if isinstance(position.get("info"), dict) else {}
        current_qty = to_float(data.get("currentQty"))
        contracts = to_float(position.get("contracts"))
        size = current_qty if current_qty is not None else contracts
        if size is None:
            size = to_float(position.get("size"))
        side = str(position.get("side") or data.get("side") or "").lower()
        if current_qty is None and size is not None and side == "short" and size > 0:
            size = -size
        if size is None or size == 0:
            return None
        contract_size = None
        try:
            if not exchange.markets:
                await exchange.load_markets()
            market = exchange.markets.get(symbol)
            if not market:
                market = exchange.market(symbol)
            if isinstance(market, dict):
                contract_size = to_float(market.get("contractSize"))
        except Exception:
            contract_size = None
        if contract_size and contract_size > 0:
            size = size * contract_size
        else:
            logger.warning("Missing contractSize for symbol %s on bitmex, using raw size", symbol)

        liquidation_price = to_float(position.get("liquidationPrice"))
        if liquidation_price is None:
            liquidation_price = to_float(data.get("liquidationPrice"))
        margin_currency = data.get("currency") or data.get("quoteCurrency") or "USDT"
        initial_margin = normalize_amount(data.get("posInit"), margin_currency)
        if initial_margin is None:
            initial_margin = normalize_amount(data.get("initMargin"), margin_currency)
        if initial_margin is None:
            initial_margin = to_float(data.get("posInit"))
        if initial_margin is None:
            initial_margin = to_float(data.get("initMargin"))
        margin = to_float(position.get("collateral"))
        if margin is None:
            margin = to_float(position.get("initialMargin"))
        pos_margin = normalize_amount(data.get("posMargin"), margin_currency)
        if pos_margin is not None and pos_margin > 0:
            margin = pos_margin
        if margin is None:
            pos_init = normalize_amount(data.get("posInit"), margin_currency)
            if pos_init is not None and pos_init > 0:
                margin = pos_init
        if margin is None:
            init_margin = normalize_amount(data.get("initMargin"), margin_currency)
            if init_margin is not None and init_margin > 0:
                margin = init_margin
        if margin is None:
            margin = to_float(position.get("maintenanceMargin"))
        if margin is None:
            maint_margin = normalize_amount(data.get("maintMargin"), margin_currency)
            margin = maint_margin if maint_margin is not None else to_float(data.get("maintMargin"))
        if margin is None:
            maintenance_margin = normalize_amount(data.get("maintenanceMargin"), margin_currency)
            margin = maintenance_margin if maintenance_margin is not None else to_float(data.get("maintenanceMargin"))
        maintenance_margin = normalize_amount(data.get("maintMargin"), margin_currency)
        if maintenance_margin is None:
            maintenance_margin = to_float(data.get("maintMargin"))
        if maintenance_margin is None:
            maintenance_margin = normalize_amount(data.get("maintenanceMargin"), margin_currency)
        if maintenance_margin is None:
            maintenance_margin = to_float(data.get("maintenanceMargin"))
        mark_price = to_float(position.get("markPrice"))
        if mark_price is None:
            mark_price = to_float(data.get("markPrice"))
        unrealized_pnl = to_float(position.get("unrealizedPnl"))
        if unrealized_pnl is None:
            unrealized_pnl = to_float(data.get("unrealisedPnl"))
        if unrealized_pnl is None:
            unrealized_pnl = to_float(data.get("unrealizedPnl"))
        leverage = to_float(position.get("leverage"))
        if leverage is None:
            leverage = to_float(data.get("leverage"))

        return {
            "liquidation_price": liquidation_price,
            "margin": float(margin or 0.0),
            "initial_margin": float(initial_margin) if initial_margin is not None else None,
            "size": float(size),
            "mark_price": float(mark_price or 0.0),
            "unrealized_pnl": float(unrealized_pnl or 0.0),
            "leverage": leverage,
            "maintenance_margin": float(maintenance_margin) if maintenance_margin is not None else None,
        }

    async def _transfer_isolated_margin(self, exchange, symbol: str, amount: float):
        if not exchange.markets:
            await exchange.load_markets()
        market = exchange.market(symbol)
        market_id = market.get("id") or symbol
        settle = market.get("settle") or market.get("quote") or "USDT"
        currencies = getattr(exchange, "currencies", {}) or {}
        currency = currencies.get(settle) if isinstance(currencies, dict) else None
        precision = currency.get("precision") if isinstance(currency, dict) else None
        if precision is not None and int(precision) > 0:
            amount_units = int(round(float(amount) * (10 ** int(precision))))
        elif str(settle).upper() == "USDT":
            amount_units = int(round(float(amount) * 1_000_000))
        else:
            amount_units = int(round(float(amount)))
        response = await exchange.request(
            "position/transferMargin",
            "private",
            "POST",
            {"symbol": market_id, "amount": amount_units},
        )
        logger.info(
            "bitmex_transfer_margin symbol=%s market_id=%s amount=%.8f amount_units=%s raw=%s",
            symbol,
            market_id,
            float(amount),
            amount_units,
            response,
        )
        return response

    async def ensure_isolated_margin(
        self, exchange, symbol: str, target_leverage: Optional[float] = None
    ) -> Dict[str, Any]:
        if not exchange.markets:
            await exchange.load_markets()
        market = exchange.market(symbol)
        market_symbol = market.get("symbol") or symbol
        market_id = market.get("id") or symbol
        leverage = float(target_leverage or 1.0)
        errors = []

        try:
            if hasattr(exchange, "set_margin_mode"):
                await exchange.set_margin_mode("isolated", market_symbol, {"leverage": leverage})
                return {"success": True, "margin_mode": "isolated", "leverage": leverage}
        except Exception as exc:
            errors.append(str(exc))

        try:
            if hasattr(exchange, "set_leverage"):
                await exchange.set_leverage(leverage, market_symbol)
                return {"success": True, "margin_mode": "isolated", "leverage": leverage}
        except Exception as exc:
            errors.append(str(exc))

        try:
            await exchange.request(
                "position/leverage",
                "private",
                "POST",
                {"symbol": market_id, "leverage": leverage},
            )
            return {"success": True, "margin_mode": "isolated", "leverage": leverage}
        except Exception as exc:
            errors.append(str(exc))

        return {
            "success": False,
            "margin_mode": None,
            "error": " | ".join([message for message in errors if message]) or "cannot set isolated margin",
        }

    async def add_margin(self, exchange, symbol: str, amount: float) -> Dict[str, Any]:
        try:
            transfer_raw = await self._transfer_isolated_margin(exchange, symbol, abs(float(amount)))
            updated = await self.fetch_position_info(exchange, symbol)
            if not updated:
                return {"success": False, "error": "No open position found", "new_margin": None, "liquidation_price": None, "raw_response": transfer_raw}
            return {"success": True, "new_margin": float(updated.get("margin") or 0.0), "liquidation_price": updated.get("liquidation_price"), "raw_response": transfer_raw}
        except Exception as e:
            error_raw = _raw_error(e)
            logger.error("bitmex_add_margin_failed symbol=%s amount=%.8f raw=%s", symbol, float(amount), error_raw)
            return {"success": False, "error": str(e), "new_margin": None, "liquidation_price": None, "raw_response": error_raw}

    async def remove_margin(self, exchange, symbol: str, amount: float) -> Dict[str, Any]:
        try:
            transfer_raw = await self._transfer_isolated_margin(exchange, symbol, -abs(float(amount)))
            updated = await self.fetch_position_info(exchange, symbol)
            if not updated:
                return {"success": False, "error": "No open position found", "new_margin": None, "liquidation_price": None, "raw_response": transfer_raw}
            return {"success": True, "new_margin": float(updated.get("margin") or 0.0), "liquidation_price": updated.get("liquidation_price"), "raw_response": transfer_raw}
        except Exception as e:
            error_raw = _raw_error(e)
            logger.error("bitmex_remove_margin_failed symbol=%s amount=%.8f raw=%s", symbol, float(amount), error_raw)
            return {"success": False, "error": str(e), "new_margin": None, "liquidation_price": None, "raw_response": error_raw}
