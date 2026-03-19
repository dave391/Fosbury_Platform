STRATEGY_KEY = "cash_funding"
STRATEGY_NAME = "Cash & Funding"
FEE_BUFFER = 1.002
MIN_CAPITAL_USD = 25
MIN_ADD_CAPITAL_USDC = 10.0
MIN_REMAINING_CAPITAL_USDC = 1.0

EXCHANGE_RULES = {
    "deribit": {
        "enabled": True,
        "assets": ["BTC", "ETH", "PAXG", "SOL"],
        "quote": "USDC",
        "spot_asset_aliases": {"ETH": "STETH"},
        "perp_size_mode": "base",
    },
    "bitmex": {
        "enabled": True,
        "assets": ["BTC", "ETH", "SOL", "XRP"],
        "quote": "USDT",
        "spot_asset_aliases": {},
        "perp_size_mode": "auto",
    },
}


def get_exchange_rules(exchange_id: str) -> dict:
    rules = EXCHANGE_RULES.get(exchange_id or "")
    if not rules or not rules.get("enabled"):
        raise ValueError("Exchange non disponibile per questa strategia.")
    return rules
