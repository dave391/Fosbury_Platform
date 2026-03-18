import asyncio
import json
import os

import ccxt.async_support as ccxt


def _find_market(markets, *, base: str, quote: str, spot: bool = False, swap: bool = False):
    for market in markets.values():
        if not isinstance(market, dict):
            continue
        if str(market.get("base") or "").upper() != base.upper():
            continue
        if str(market.get("quote") or "").upper() != quote.upper():
            continue
        if spot and not bool(market.get("spot")):
            continue
        if swap and not bool(market.get("swap")):
            continue
        return market
    return None


def _ticker_last_price(ticker):
    if not isinstance(ticker, dict):
        return None
    for key in ("last", "close", "mark", "bid", "ask"):
        value = ticker.get(key)
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _create_client(wallet: str, private_key: str):
    client = ccxt.hyperliquid(
        {
            "walletAddress": wallet,
            "privateKey": private_key,
            "enableRateLimit": True,
            "options": {"defaultSlippage": 0.05},
        }
    )
    original_create_order = client.create_order

    async def patched_create_order(symbol, type, side, amount, price=None, params=None):
        normalized_type = str(type or "").lower()
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
        return await original_create_order(symbol, type, side, amount, price, params or {})

    client.create_order = patched_create_order
    return client


async def main():
    wallet = str(os.getenv("HYPERLIQUID_WALLET_ADDRESS") or "").strip()
    private_key = str(os.getenv("HYPERLIQUID_PRIVATE_KEY") or "").strip()
    if not wallet or not private_key:
        raise RuntimeError("Missing HYPERLIQUID_WALLET_ADDRESS or HYPERLIQUID_PRIVATE_KEY")

    exchange = _create_client(wallet, private_key)
    try:
        await exchange.load_markets()

        print("STEP A")
        btc_markets = [s for s in exchange.markets.keys() if "BTC" in s.upper()]
        print("BTC markets:", btc_markets)

        print("STEP B")
        spot_market = _find_market(exchange.markets, base="BTC", quote="USDC", spot=True)
        if spot_market:
            print(
                "Spot market:",
                {"symbol": spot_market.get("symbol"), "id": spot_market.get("id")},
            )
        else:
            print("Spot market: NOT FOUND")

        print("STEP C")
        perp_market = _find_market(exchange.markets, base="BTC", quote="USDC", swap=True)
        if perp_market:
            print(
                "Perp market:",
                {"symbol": perp_market.get("symbol"), "id": perp_market.get("id")},
            )
        else:
            print("Perp market: NOT FOUND")

        if not spot_market or not perp_market:
            print("STOP: missing spot or perp market")
            return

        spot_symbol = spot_market.get("symbol")
        perp_symbol = perp_market.get("symbol")

        print("STEP D")
        spot_ticker = await exchange.fetch_ticker(spot_symbol)
        perp_ticker = await exchange.fetch_ticker(perp_symbol)
        print("Spot ticker:", spot_ticker)
        print("Perp ticker:", perp_ticker)

        print("STEP E")
        capital = 25.0
        spot_price = _ticker_last_price(spot_ticker)
        if spot_price is None or spot_price <= 0:
            print("STOP: invalid spot price", spot_price)
            return
        base_amount = capital / (spot_price * (1 + 1.2 / 5.0))
        print("spot_price:", spot_price)
        print("base_amount:", base_amount)

        print("STEP F")
        spot_amount = exchange.amount_to_precision(spot_symbol, base_amount)
        perp_amount = exchange.amount_to_precision(perp_symbol, base_amount)
        print("spot amount_to_precision:", spot_amount)
        print("perp amount_to_precision:", perp_amount)

        print("STEP G")
        print(f"Would execute: exchange.create_market_buy_order({spot_symbol!r}, {spot_amount})")

        print("STEP H")
        try:
            order = await exchange.create_market_buy_order("BTC/USDC", 0.00028)
            print("STEP H - spot buy order:", json.dumps(order, indent=2, default=str))
        except Exception as e:
            print("STEP H - spot buy FAILED:", str(e))

        print("STEP I")
        try:
            order = await exchange.create_market_sell_order("BTC/USDC:USDC", 0.00028)
            print("STEP I - perp sell order:", json.dumps(order, indent=2, default=str))
        except Exception as e:
            print("STEP I - perp sell FAILED:", str(e))
    finally:
        await exchange.close()


if __name__ == "__main__":
    asyncio.run(main())
