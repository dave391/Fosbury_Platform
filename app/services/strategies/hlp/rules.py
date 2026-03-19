STRATEGY_KEY = "hlp"
STRATEGY_NAME = "HLP Vault"
MIN_CAPITAL_USD = 5.0
MIN_ADD_CAPITAL_USDC = 5.0
MIN_REMAINING_CAPITAL_USDC = 1.0

EXCHANGE_RULES = {
    "hyperliquid": {
        "enabled": True,
        "assets": ["USDC"],
        "quote": "USDC",
    },
}


def get_exchange_rules(exchange_id: str) -> dict:
    rules = EXCHANGE_RULES.get(exchange_id or "")
    if not rules or not rules.get("enabled"):
        raise ValueError("Exchange non disponibile per questa strategia.")
    return rules
