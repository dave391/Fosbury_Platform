from enum import Enum

class StrategyStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"

class AssetType(str, Enum):
    BTC = "BTC"
    ETH = "ETH"
    PAXG = "PAXG"
    SOL = "SOL"

class ExchangeName(str, Enum):
    DERIBIT = "deribit"
    BITMEX = "bitmex"

class CookieName(str, Enum):
    SESSION = "session"
