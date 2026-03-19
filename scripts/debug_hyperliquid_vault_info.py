import asyncio
import json
import os

import ccxt.async_support as ccxt


HLP_VAULT_ADDRESS = "0xdfc24b077bc1425ad1dea75bcb6f8158e10df303"


def _create_client(wallet: str, private_key: str):
    return ccxt.hyperliquid(
        {
            "walletAddress": wallet,
            "privateKey": private_key,
            "enableRateLimit": True,
            "options": {"defaultSlippage": 0.05},
        }
    )


def _print_json(label: str, response):
    try:
        payload = json.dumps(response, indent=2, default=str)
    except Exception:
        payload = str(response)
    if len(payload) <= 12000:
        print(f"{label}: {payload}")
        return
    if isinstance(response, dict):
        trimmed = {"keys": list(response.keys())}
        followers = response.get("followers")
        if isinstance(followers, list):
            trimmed["followers_preview"] = followers[:2]
            trimmed["followers_count"] = len(followers)
        print(f"{label} (trimmed): {json.dumps(trimmed, indent=2, default=str)}")
        return
    print(f"{label}: {payload[:12000]}")


async def main():
    wallet = str(os.getenv("HYPERLIQUID_WALLET_ADDRESS") or "").strip()
    private_key = str(os.getenv("HYPERLIQUID_PRIVATE_KEY") or "").strip()
    if not wallet or not private_key:
        raise RuntimeError("Missing HYPERLIQUID_WALLET_ADDRESS or HYPERLIQUID_PRIVATE_KEY")

    exchange = _create_client(wallet, private_key)
    try:
        response = await exchange.publicPostInfo(
            {
                "type": "vaultDetails",
                "vaultAddress": HLP_VAULT_ADDRESS,
                "user": wallet,
            }
        )
        _print_json("STEP A - vaultDetails", response)

        response = await exchange.publicPostInfo(
            {
                "type": "userVaultEquities",
                "user": wallet,
            }
        )
        _print_json("STEP B - userVaultEquities", response)
    finally:
        await exchange.close()


if __name__ == "__main__":
    asyncio.run(main())
