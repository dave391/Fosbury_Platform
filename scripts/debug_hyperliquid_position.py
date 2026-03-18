import asyncio
import json
import os

import ccxt.async_support as ccxt


async def main():
    wallet = str(os.getenv("HYPERLIQUID_WALLET_ADDRESS") or "").strip()
    private_key = str(os.getenv("HYPERLIQUID_PRIVATE_KEY") or "").strip()
    if not wallet or not private_key:
        raise RuntimeError("Missing HYPERLIQUID_WALLET_ADDRESS or HYPERLIQUID_PRIVATE_KEY")

    exchange = ccxt.hyperliquid(
        {
            "walletAddress": wallet,
            "privateKey": private_key,
            "enableRateLimit": True,
        }
    )
    try:
        await exchange.load_markets()
        positions = await exchange.fetch_positions(["HYPE/USDC:USDC"])
        print(json.dumps(positions, indent=2, default=str))
    finally:
        await exchange.close()


if __name__ == "__main__":
    asyncio.run(main())
