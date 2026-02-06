import asyncio
from typing import List, Dict, Any, Tuple
import ccxt.async_support as ccxt
from app.services.exchanges.base import ExchangeAdapter


class DeribitExchange(ExchangeAdapter):
    async def get_client(self, api_key: str, api_secret: str):
        return ccxt.deribit({"apiKey": api_key, "secret": api_secret, "enableRateLimit": True})

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
            currencies_resp = await exchange.request("get_currencies", "public", "GET", {})
            currencies = [
                c.get("currency")
                for c in (currencies_resp.get("result") or [])
                if c.get("currency")
            ]
        except Exception:
            currencies = []
        active_currencies = []
        for code in currencies:
            try:
                resp = await exchange.request("get_account_summary", "private", "GET", {"currency": code})
                result = resp.get("result") or {}
                balance = float(result.get("balance") or 0)
                equity = float(result.get("equity") or 0)
                if balance != 0 or equity != 0:
                    active_currencies.append(code)
                await asyncio.sleep(0.2)
            except Exception:
                continue
        if not active_currencies:
            active_currencies = currencies
        return active_currencies

    async def fetch_transaction_logs(
        self, exchange, currency: str, start_ms: int, end_ms: int
    ) -> List[Dict[str, Any]]:
        try:
            resp = await exchange.request(
                "get_transaction_log",
                "private",
                "GET",
                {"currency": currency, "start_timestamp": start_ms, "end_timestamp": end_ms},
            )
        except Exception as exc:
            if "too_many_requests" in str(exc):
                await asyncio.sleep(1)
                resp = await exchange.request(
                    "get_transaction_log",
                    "private",
                    "GET",
                    {"currency": currency, "start_timestamp": start_ms, "end_timestamp": end_ms},
                )
            else:
                return []
        result = resp.get("result") or {}
        logs = result.get("logs") if isinstance(result, dict) else result
        items = []
        for item in logs or []:
            instrument = item.get("instrument_name") or currency
            entry_type = item.get("type")
            currency_code = item.get("currency") or currency
            timestamp = item.get("timestamp")
            if entry_type == "settlement":
                funding = item.get("total_interest_pl")
                if funding is None:
                    funding = item.get("interest_pl")
                if funding is None:
                    continue
                items.append(
                    {
                        "instrument": instrument,
                        "entry_type": "funding",
                        "currency": currency_code,
                        "timestamp": timestamp,
                        "funding": float(funding),
                        "fee": None,
                    }
                )
            elif entry_type == "trade":
                fee = item.get("commission")
                if fee is None:
                    continue
                items.append(
                    {
                        "instrument": instrument,
                        "entry_type": "fee",
                        "currency": currency_code,
                        "timestamp": timestamp,
                        "funding": None,
                        "fee": float(fee),
                    }
                )
        return items

    async def fetch_strategy_deltas(
        self, exchange, strategy, start_ms: int, end_ms: int
    ) -> Tuple[float, float]:
        config = strategy.config or {}
        quote = config.get("quote") or "USDC"
        spot_asset = config.get("spot_asset") or ("STETH" if strategy.asset == "ETH" else strategy.asset)
        spot_id = config.get("spot_id") or f"{spot_asset}_{quote}"
        perp_id = config.get("perp_id") or f"{strategy.asset}_{quote}-PERPETUAL"

        logs = await self.fetch_transaction_logs(exchange, quote, start_ms, end_ms)
        funding_delta = 0.0
        fees_delta = 0.0
        for item in logs or []:
            instrument = item.get("instrument")
            entry_type = item.get("entry_type")
            currency_code = item.get("currency")
            if entry_type == "funding":
                if instrument != perp_id:
                    continue
                funding = item.get("funding")
                if funding is None:
                    continue
                funding_delta += float(funding)
            elif entry_type == "fee":
                if instrument not in (spot_id, perp_id):
                    continue
                fee = item.get("fee")
                if fee is None:
                    continue
                if instrument == spot_id and currency_code != quote:
                    continue
                fees_delta += float(fee)
        return funding_delta, fees_delta

    async def fetch_quote_balance(self, exchange, quote: str) -> float:
        try:
            resp = await exchange.request("get_account_summary", "private", "GET", {"currency": quote})
            result = resp.get("result") or {}
            equity = result.get("equity")
            if equity is not None:
                return float(equity or 0)
        except Exception:
            pass
        balance = await exchange.fetch_balance()
        free = balance.get("free", {})
        total = balance.get("total", {})
        value = free.get(quote)
        if value is None:
            value = total.get(quote)
        return float(value or 0)
