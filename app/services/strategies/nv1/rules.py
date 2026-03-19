STRATEGY_KEY = "nv1"
STRATEGY_NAME = "Neutro V1"
FEE_BUFFER = 1.002
MIN_CAPITAL_USD = 20
DEFAULT_LEVERAGE = 5.0
MARGIN_SAFETY_BUFFER = 1.2
MIN_ALLOCATION_PCT = 0.95
SCALE_UP_REMOVABLE_FACTOR = 0.99
MIN_REMAINING_CAPITAL_USDC = 5.0

DEFAULT_SAFE_DISTANCE_PCT = 15.0
DEFAULT_WARNING_DISTANCE_PCT = 5.0
DEFAULT_CRITICAL_DISTANCE_PCT = 2.0
DEFAULT_MIN_EXCESS_MARGIN = 5.0
DEFAULT_MAX_DELTA_MISMATCH_PCT = 2.0
DEFAULT_COOLDOWN_SECONDS = 300

EXCHANGE_RULES = {
    "deribit": {
        "enabled": True,
        "assets": ["BTC", "ETH", "SOL", "XRP","BNB","PAXG"],
        "quote": "USDC",
        "spot_asset_aliases": {"ETH": "STETH"},
        "perp_size_mode": "base",
        "partial_allocation_allowed": False,
    },
    "bitmex": {
        "enabled": True,
        "assets": ["BTC", "ETH", "SOL", "XRP","HYPE","LINK","POL","UNI","BMEX"],
        "quote": "USDT",
        "spot_asset_aliases": {},
        "perp_size_mode": "auto",
        "partial_allocation_allowed": True,
    },
    "hyperliquid": {
        "enabled": True,
        "assets": ["BTC", "ETH", "SOL", "HYPE", "FARTCOIN", "PURR"],
        "quote": "USDC",
        "default_leverage": 5.0,
        "asset_leverage_overrides": {"PURR": 3.0},
        "spot_asset_aliases": {"FARTCOIN": "FART"},
        "spot_symbol_overrides": {
            "PUMP": "PUMP/USDC",
            "FARTCOIN": "FART/USDC",
            "PURR": "PURR/USDC",
        },
        "perp_symbol_overrides": {
            "PUMP": "PUMP/USDC:USDC",
            "FARTCOIN": "FARTCOIN/USDC:USDC",
            "PURR": "PURR/USDC:USDC",
        },
        "perp_size_mode": "base",
        "partial_allocation_allowed": True,
    },
}


def get_exchange_rules(exchange_id: str) -> dict:
    rules = EXCHANGE_RULES.get(exchange_id or "")
    if not rules or not rules.get("enabled"):
        raise ValueError("Exchange non disponibile per questa strategia.")
    return rules


def get_default_thresholds() -> dict:
    return {
        "safe_distance_pct": DEFAULT_SAFE_DISTANCE_PCT,
        "warning_distance_pct": DEFAULT_WARNING_DISTANCE_PCT,
        "critical_distance_pct": DEFAULT_CRITICAL_DISTANCE_PCT,
        "min_excess_margin": DEFAULT_MIN_EXCESS_MARGIN,
        "max_delta_mismatch_pct": DEFAULT_MAX_DELTA_MISMATCH_PCT,
        "cooldown_seconds": DEFAULT_COOLDOWN_SECONDS,
    }
