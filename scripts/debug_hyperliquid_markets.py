import asyncio

import ccxt.async_support as ccxt


def _collect(markets, market_type: str, quote: str):
    rows = []
    for market in markets:
        if not isinstance(market, dict):
            continue
        if not market.get(market_type):
            continue
        if str(market.get("quote") or "").upper() != quote:
            continue
        rows.append((str(market.get("base") or ""), str(market.get("symbol") or "")))
    rows.sort(key=lambda item: item[0])
    return rows


async def main():
    exchange = ccxt.hyperliquid({"enableRateLimit": True})
    try:
        await exchange.load_markets()
        markets = list((exchange.markets or {}).values())
        spot = _collect(markets, "spot", "USDC")
        perp = _collect(markets, "swap", "USDC")
        spot_bases = {base for base, _ in spot if base}
        perp_bases = {base for base, _ in perp if base}
        common_bases = sorted(spot_bases.intersection(perp_bases))

        print("SPOT_USDC_SYMBOLS")
        for base, symbol in spot:
            print(f"{base}\t{symbol}")

        print("\nPERP_USDC_SYMBOLS")
        for base, symbol in perp:
            print(f"{base}\t{symbol}")

        print("\nCOMMON_BASES_SPOT_PERP_USDC")
        for base in common_bases:
            print(base)
    finally:
        await exchange.close()


if __name__ == "__main__":
    asyncio.run(main())
