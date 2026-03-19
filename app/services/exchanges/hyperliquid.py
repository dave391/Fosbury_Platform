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
        _ = exchange
        _ = currency
        _ = start_ms
        _ = end_ms
        # TODO: implementare con userNonFundingLedgerUpdates
        return []

    async def fetch_strategy_deltas(
        self, exchange, strategy: Any, start_ms: int, end_ms: int
    ) -> Tuple[float, float]:
        _ = exchange
        _ = strategy
        _ = start_ms
        _ = end_ms
        # TODO: implementare quando servono i delta funding/fees
        return 0.0, 0.0

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

        return {
            "liquidation_price": float(liquidation_price or 0.0),
            "margin": float(margin or 0.0),
            "initial_margin": float(initial_margin or 0.0),
            "size": float(size),
            "mark_price": float(mark_price or 0.0),
            "unrealized_pnl": float(unrealized_pnl or 0.0),
            "leverage": float(leverage or 0.0),
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
