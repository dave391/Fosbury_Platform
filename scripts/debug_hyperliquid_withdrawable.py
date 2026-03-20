import argparse
import asyncio
import json
import os

import ccxt.async_support as ccxt


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("symbol", nargs="?", default="ETH/USDC:USDC")
    return parser.parse_args()


async def main():
    args = parse_args()
    symbol = str(args.symbol or "ETH/USDC:USDC").strip()
    wallet = str(os.getenv("HYPERLIQUID_WALLET_ADDRESS") or "").strip()
    private_key = str(os.getenv("HYPERLIQUID_PRIVATE_KEY") or "").strip()
    if not wallet or not private_key:
        raise RuntimeError("Missing HYPERLIQUID_WALLET_ADDRESS or HYPERLIQUID_PRIVATE_KEY")

    exchange = ccxt.hyperliquid(
        {
            "walletAddress": wallet,
            "privateKey": private_key,
            "enableRateLimit": True,
            "options": {"defaultSlippage": 0.05},
        }
    )

    try:
        await exchange.load_markets()
        positions = await exchange.fetch_positions([symbol])
        if not isinstance(positions, list) or not positions:
            print(json.dumps({"symbol": symbol, "error": "No position returned"}, indent=2, default=str))
            return

        position = positions[0]
        if not isinstance(position, dict):
            print(json.dumps({"symbol": symbol, "error": "Invalid position payload"}, indent=2, default=str))
            return

        contracts = to_float(position.get("contracts"))
        collateral = to_float(position.get("collateral"))
        initial_margin = to_float(position.get("initialMargin"))
        mark_price = to_float(position.get("markPrice"))
        unrealized_pnl = to_float(position.get("unrealizedPnl"))
        leverage = to_float(position.get("leverage"))
        liquidation_price = to_float(position.get("liquidationPrice"))

        if not mark_price or mark_price <= 0:
            ticker = await exchange.fetch_ticker(symbol)
            mark_price = to_float(
                ticker.get("last")
                or ticker.get("close")
                or ticker.get("mark")
                or ticker.get("bid")
                or ticker.get("ask")
            )

        size = abs(float(contracts or 0.0))
        notional = float(size * float(mark_price or 0.0))
        leverage_value = float(leverage or 0.0)
        required_by_leverage = float(notional / leverage_value) if leverage_value > 0 else 0.0
        required_by_10pct = float(0.1 * notional)
        transfer_margin_required = max(required_by_leverage, required_by_10pct)
        max_withdrawable = max(float(collateral or 0.0) - float(transfer_margin_required), 0.0)
        current_formula = float(
            (float(collateral or 0.0) - float(initial_margin or 0.0) - abs(float(unrealized_pnl or 0.0))) * 0.99
        )

        output = {
            "symbol": symbol,
            "raw_fields": {
                "contracts": contracts,
                "collateral": collateral,
                "initialMargin": initial_margin,
                "markPrice": mark_price,
                "unrealizedPnl": unrealized_pnl,
                "leverage": leverage,
                "liquidationPrice": liquidation_price,
            },
            "calculation": {
                "size_abs_contracts": size,
                "notional": notional,
                "required_by_leverage": required_by_leverage,
                "required_by_10pct": required_by_10pct,
                "transfer_margin_required": transfer_margin_required,
                "max_withdrawable": max_withdrawable,
                "current_formula_scale_up": current_formula,
            },
            "position_raw": position,
        }
        print(json.dumps(output, indent=2, default=str))

        if max_withdrawable > 1:
            test_amount = min(1.0, float(max_withdrawable))
            if test_amount > 0:
                try:
                    reduce_result = await exchange.reduce_margin(symbol, float(test_amount))
                    print(
                        json.dumps(
                            {
                                "reduce_margin_test": "ok",
                                "requested_amount": float(test_amount),
                                "result": reduce_result,
                            },
                            indent=2,
                            default=str,
                        )
                    )
                except Exception as exc:
                    print(
                        json.dumps(
                            {
                                "reduce_margin_test": "failed",
                                "requested_amount": float(test_amount),
                                "error": str(exc),
                            },
                            indent=2,
                            default=str,
                        )
                    )
    finally:
        await exchange.close()


if __name__ == "__main__":
    asyncio.run(main())
