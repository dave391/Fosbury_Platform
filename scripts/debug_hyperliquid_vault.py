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


async def _print_usdc_balance(exchange, label: str):
    balance = await exchange.fetch_balance({"type": "spot"})
    print(f"{label}:", balance.get("USDC"))


async def _vault_transfer(exchange, is_deposit: bool, usd: float):
    nonce = exchange.milliseconds()
    usd_units = int(round(float(usd) * 1_000_000))
    action = {
        "type": "vaultTransfer",
        "vaultAddress": HLP_VAULT_ADDRESS,
        "isDeposit": is_deposit,
        "usd": usd_units,
    }
    signature = exchange.sign_l1_action(action, nonce)
    request = {
        "action": action,
        "nonce": nonce,
        "signature": signature,
    }
    return await exchange.privatePostExchange(request)


async def main():
    wallet = str(os.getenv("HYPERLIQUID_WALLET_ADDRESS") or "").strip()
    private_key = str(os.getenv("HYPERLIQUID_PRIVATE_KEY") or "").strip()
    if not wallet or not private_key:
        raise RuntimeError("Missing HYPERLIQUID_WALLET_ADDRESS or HYPERLIQUID_PRIVATE_KEY")

    exchange = _create_client(wallet, private_key)
    try:
        print("STEP A")
        await _print_usdc_balance(exchange, "USDC before")

        print("STEP B")
        try:
            deposit_response = await _vault_transfer(exchange, is_deposit=True, usd=1.0)
            print("STEP B - deposit response:", json.dumps(deposit_response, indent=2, default=str))
        except Exception as exc:
            print("STEP B - deposit failed:", str(exc))

        print("STEP C")
        await _print_usdc_balance(exchange, "USDC after deposit")

        print("STEP D")
        try:
            withdraw_response = await _vault_transfer(exchange, is_deposit=False, usd=1.0)
            print("STEP D - withdraw response:", json.dumps(withdraw_response, indent=2, default=str))
        except Exception as exc:
            print("STEP D - withdraw failed:", str(exc))
    finally:
        await exchange.close()


if __name__ == "__main__":
    asyncio.run(main())
