from typing import List, Dict, Any, Tuple
import asyncio
import ccxt.async_support as ccxt
from app.services.exchanges.base import ExchangeAdapter


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
