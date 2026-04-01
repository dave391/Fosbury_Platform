import asyncio
from typing import List, Dict, Any, Tuple, Optional
import logging
import ccxt.async_support as ccxt
from app.services.exchanges.base import ExchangeAdapter


logger = logging.getLogger(__name__)


class HyperliquidExchange(ExchangeAdapter):
    async def get_client(self, api_key: str, api_secret: str):
        client = ccxt.hyperliquid(
            {
                "walletAddress": api_key,
                "privateKey": api_secret,
                "enableRateLimit": True,
                "options": {"defaultSlippage": 0.05},
            }
        )
        original_create_order = client.create_order

        async def patched_create_order(symbol, type, side, amount, price=None, params=None):
            safe_params = dict(params or {})
            normalized_type = str(type or "").lower()
            if price is None:
                hinted_price = safe_params.pop("_price_hint", None)
                try:
                    hinted_value = float(hinted_price) if hinted_price is not None else None
                except (TypeError, ValueError):
                    hinted_value = None
                if hinted_value is not None and hinted_value > 0:
                    price = hinted_value
            if normalized_type == "market" and price is None:
                ticker = await client.fetch_ticker(symbol)
                for key in ("last", "close", "bid", "ask", "mark"):
                    value = ticker.get(key) if isinstance(ticker, dict) else None
                    if value is None:
                        continue
                    try:
                        price = float(value)
                        break
                    except (TypeError, ValueError):
                        continue
                if price is None:
                    raise ValueError(f"Cannot fetch price for {symbol}")
            return await original_create_order(symbol, type, side, amount, price, safe_params)

        client.create_order = patched_create_order
        return client

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
            balance = await exchange.fetch_balance({"type": "spot"})
            totals = (balance.get("total") or {}) if isinstance(balance, dict) else {}
            active = []
            for code, value in totals.items():
                try:
                    if float(value or 0) > 0:
                        active.append(code)
                except (TypeError, ValueError):
                    continue
            return active
        except Exception:
            return ["USDC"]

    async def fetch_transaction_logs(
        self, exchange, currency: str, start_ms: int, end_ms: int
    ) -> List[Dict[str, Any]]:
        def to_float(value):
            try:
                return float(value)
            except (TypeError, ValueError):
                return None

        logs: List[Dict[str, Any]] = []
        seen = set()
        since = int(start_ms)
        limit = 500
        attempts = 0
        while since <= end_ms and attempts < 20:
            attempts += 1
            try:
                batch = await exchange.fetch_ledger(
                    currency,
                    since,
                    limit,
                    {"until": end_ms},
                )
            except Exception:
                break
            if not isinstance(batch, list) or not batch:
                break
            max_ts = since
            for entry in batch:
                if not isinstance(entry, dict):
                    continue
                ts = entry.get("timestamp")
                if ts is None:
                    ts = exchange.parse8601(entry.get("datetime"))
                if ts is None:
                    continue
                ts = int(ts)
                if ts < start_ms or ts > end_ms:
                    continue
                if ts > max_ts:
                    max_ts = ts
                info = entry.get("info")
                info = info if isinstance(info, dict) else {}
                entry_type = str(
                    entry.get("type")
                    or info.get("type")
                    or info.get("deltaType")
                    or ""
                ).lower()
                instrument = (
                    entry.get("symbol")
                    or info.get("coin")
                    or info.get("symbol")
                    or currency
                )
                currency_code = entry.get("currency") or info.get("token") or currency
                amount = to_float(entry.get("amount"))
                fee_data = entry.get("fee")
                fee_value = None
                if isinstance(fee_data, dict):
                    fee_value = to_float(fee_data.get("cost"))
                else:
                    fee_value = to_float(fee_data)
                if "funding" in entry_type and amount is not None:
                    key = ("funding", ts, str(instrument), float(amount))
                    if key in seen:
                        continue
                    seen.add(key)
                    logs.append(
                        {
                            "instrument": instrument,
                            "entry_type": "funding",
                            "currency": currency_code,
                            "timestamp": ts,
                            "funding": float(amount),
                            "fee": None,
                        }
                    )
                elif fee_value is not None and ("fee" in entry_type or "trade" in entry_type):
                    key = ("fee", ts, str(instrument), float(fee_value))
                    if key in seen:
                        continue
                    seen.add(key)
                    logs.append(
                        {
                            "instrument": instrument,
                            "entry_type": "fee",
                            "currency": currency_code,
                            "timestamp": ts,
                            "funding": None,
                            "fee": abs(float(fee_value)),
                        }
                    )
            if len(batch) < limit or max_ts <= since:
                break
            since = max_ts + 1
            rate_limit = getattr(exchange, "rateLimit", 0) or 0
            if rate_limit:
                await asyncio.sleep(rate_limit / 1000)
        return logs

    async def fetch_strategy_deltas(
        self, exchange, strategy: Any, start_ms: int, end_ms: int
    ) -> Tuple[float, float]:
        config = strategy.config or {}
        quote = str(config.get("quote") or "USDC")
        spot_id = config.get("spot_symbol") or config.get("spot_id")
        perp_id = config.get("perp_symbol") or config.get("perp_id")
        if not spot_id and not perp_id:
            return 0.0, 0.0

        def to_float(value):
            try:
                return float(value)
            except (TypeError, ValueError):
                return None

        def normalize(value: str) -> str:
            return "".join(ch for ch in str(value or "").upper() if ch.isalnum())

        spot_norm = normalize(spot_id)
        perp_norm = normalize(perp_id)
        quote_norm = normalize(quote)

        def match_symbol(value: str, target: str) -> bool:
            current = normalize(value)
            if not current or not target:
                return False
            return current == target

        def quote_matches(value: str) -> bool:
            current = normalize(value)
            if not current:
                return True
            return current == quote_norm

        funding_delta = 0.0
        fees_delta = 0.0
        funding_count = 0
        fee_count = 0

        if perp_id:
            try:
                funding_items = await exchange.fetch_funding_history(
                    perp_id,
                    int(start_ms),
                    500,
                    {"until": int(end_ms)},
                )
            except Exception:
                funding_items = []
            for item in funding_items or []:
                if not isinstance(item, dict):
                    continue
                symbol = item.get("symbol")
                if symbol and not match_symbol(symbol, perp_norm):
                    continue
                funding = to_float(item.get("amount"))
                if funding is None:
                    info = item.get("info")
                    info = info if isinstance(info, dict) else {}
                    delta = info.get("delta")
                    delta = delta if isinstance(delta, dict) else {}
                    funding = to_float(delta.get("usdc"))
                if funding is None:
                    continue
                funding_delta += float(funding)
                funding_count += 1

        for trade_symbol, target_norm in ((perp_id, perp_norm), (spot_id, spot_norm)):
            if not trade_symbol:
                continue
            try:
                trades = await exchange.fetch_my_trades(
                    trade_symbol,
                    int(start_ms),
                    500,
                    {"until": int(end_ms)},
                )
            except Exception:
                trades = []
            for trade in trades or []:
                if not isinstance(trade, dict):
                    continue
                symbol = trade.get("symbol") or trade_symbol
                if not match_symbol(symbol, target_norm):
                    continue
                fee_entries = trade.get("fees")
                if isinstance(fee_entries, list) and fee_entries:
                    current_fees = fee_entries
                else:
                    single_fee = trade.get("fee")
                    current_fees = [single_fee] if isinstance(single_fee, dict) else []
                if not current_fees:
                    continue
                price = to_float(trade.get("price"))
                base_asset = str(symbol).split("/", 1)[0]
                base_norm = normalize(base_asset)
                for fee_info in current_fees:
                    if not isinstance(fee_info, dict):
                        continue
                    fee_value = to_float(fee_info.get("cost"))
                    if fee_value is None:
                        continue
                    fee_currency = fee_info.get("currency")
                    fee_currency_norm = normalize(fee_currency)
                    fee_usdc = None
                    if quote_matches(fee_currency):
                        fee_usdc = abs(float(fee_value))
                    elif (
                        price is not None
                        and price > 0
                        and fee_currency_norm in (base_norm, f"U{base_norm}")
                    ):
                        fee_usdc = abs(float(fee_value) * float(price))
                    if fee_usdc is None:
                        continue
                    fees_delta += float(fee_usdc)
                    fee_count += 1

        if funding_count == 0 or fee_count == 0:
            logs = await self.fetch_transaction_logs(exchange, quote, start_ms, end_ms)
            for item in logs or []:
                instrument = item.get("instrument")
                entry_type = item.get("entry_type")
                currency_code = item.get("currency")
                if entry_type == "funding" and funding_count == 0:
                    if not match_symbol(instrument, perp_norm):
                        continue
                    funding = item.get("funding")
                    if funding is None:
                        continue
                    funding_delta += float(funding)
                elif entry_type == "fee" and fee_count == 0:
                    matches_spot = match_symbol(instrument, spot_norm)
                    matches_perp = match_symbol(instrument, perp_norm)
                    if not (matches_spot or matches_perp):
                        continue
                    if not quote_matches(currency_code):
                        continue
                    fee = item.get("fee")
                    if fee is None:
                        continue
                    fees_delta += abs(float(fee))
        return funding_delta, fees_delta

    async def fetch_quote_balance(self, exchange, quote: str) -> float:
        balance = await exchange.fetch_balance({"type": "spot"})
        quote_balance = (balance.get(quote) or {}) if isinstance(balance, dict) else {}
        value = quote_balance.get("free")
        if value is None:
            value = quote_balance.get("total")
        if value is None:
            value = (balance.get("free", {}) if isinstance(balance, dict) else {}).get(quote)
        if value is None:
            value = (balance.get("total", {}) if isinstance(balance, dict) else {}).get(quote)
        return float(value or 0)

    async def fetch_position_info(self, exchange, symbol: str) -> Optional[Dict[str, Any]]:
        def to_float(value):
            try:
                return float(value)
            except (TypeError, ValueError):
                return None

        try:
            positions = await exchange.fetch_positions([symbol])
        except Exception:
            return None
        if not isinstance(positions, list) or not positions:
            return None

        position = positions[0]
        if not isinstance(position, dict):
            return None

        size = to_float(position.get("contracts"))
        if size is None or size == 0:
            return None

        liquidation_price = to_float(position.get("liquidationPrice"))
        margin = to_float(position.get("collateral"))
        initial_margin = to_float(position.get("initialMargin"))
        mark_price = to_float(position.get("markPrice"))
        if not mark_price:
            try:
                ticker = await exchange.fetch_ticker(symbol)
                mark_price = to_float(
                    ticker.get("last")
                    or ticker.get("close")
                    or ticker.get("mark")
                )
            except Exception:
                mark_price = None
        unrealized_pnl = to_float(position.get("unrealizedPnl"))
        leverage = to_float(position.get("leverage"))
        collateral_val = float(margin or 0.0)
        leverage_val = float(leverage or 0.0)
        size_val = abs(float(size or 0.0))
        mark_val = float(mark_price or 0.0)
        notional = float(size_val * mark_val) if mark_val > 0 else 0.0
        if leverage_val > 0 and notional > 0:
            required = max(float(notional / leverage_val), float(0.1 * notional))
        else:
            required = collateral_val
        max_withdrawable = max(float(collateral_val - required), 0.0)

        return {
            "liquidation_price": float(liquidation_price or 0.0),
            "margin": float(margin or 0.0),
            "initial_margin": float(initial_margin or 0.0),
            "size": float(size),
            "mark_price": float(mark_price or 0.0),
            "unrealized_pnl": float(unrealized_pnl or 0.0),
            "leverage": float(leverage or 0.0),
            "max_withdrawable": float(max_withdrawable),
        }

    async def ensure_isolated_margin(
        self, exchange, symbol: str, target_leverage: Optional[float] = None
    ) -> Dict[str, Any]:
        leverage = int(target_leverage or 1)
        try:
            await exchange.set_leverage(leverage, symbol, {"marginMode": "isolated"})
            return {"success": True, "margin_mode": "isolated", "leverage": leverage}
        except Exception as exc:
            error = str(exc)
            lowered = error.lower()
            benign_messages = (
                "already",
                "no need",
                "unchanged",
                "same",
                "not modified",
            )
            if any(marker in lowered for marker in benign_messages):
                return {"success": True, "margin_mode": "isolated", "leverage": leverage}
            return {"success": False, "margin_mode": None, "error": error}

    async def add_margin(self, exchange, symbol: str, amount: float) -> Dict[str, Any]:
        try:
            await exchange.add_margin(symbol, float(amount))
            updated = await self.fetch_position_info(exchange, symbol)
            if not updated:
                return {
                    "success": False,
                    "error": "No open position found",
                    "new_margin": None,
                    "liquidation_price": None,
                }
            return {
                "success": True,
                "new_margin": float(updated.get("margin") or 0.0),
                "liquidation_price": updated.get("liquidation_price"),
            }
        except Exception as e:
            logger.error(
                "hyperliquid_add_margin_failed symbol=%s amount=%.8f error=%s",
                symbol,
                float(amount),
                str(e),
            )
            return {
                "success": False,
                "error": str(e),
                "new_margin": None,
                "liquidation_price": None,
            }

    async def remove_margin(self, exchange, symbol: str, amount: float) -> Dict[str, Any]:
        try:
            await exchange.reduce_margin(symbol, float(amount))
            updated = await self.fetch_position_info(exchange, symbol)
            if not updated:
                return {
                    "success": False,
                    "error": "No open position found",
                    "new_margin": None,
                    "liquidation_price": None,
                }
            return {
                "success": True,
                "new_margin": float(updated.get("margin") or 0.0),
                "liquidation_price": updated.get("liquidation_price"),
            }
        except Exception as e:
            logger.error(
                "hyperliquid_remove_margin_failed symbol=%s amount=%.8f error=%s",
                symbol,
                float(amount),
                str(e),
            )
            return {
                "success": False,
                "error": str(e),
                "new_margin": None,
                "liquidation_price": None,
            }
