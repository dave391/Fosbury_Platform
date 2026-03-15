import logging
from typing import Any, Dict


logger = logging.getLogger(__name__)


def compute_metrics(position_info: Dict[str, Any], strategy_data: Dict[str, Any]) -> Dict[str, Any]:
    mark_price = position_info.get("mark_price")
    liquidation_price = position_info.get("liquidation_price")
    margin = position_info.get("margin")
    size = position_info.get("size")
    total_quantity = strategy_data.get("total_quantity")
    target_leverage = strategy_data.get("target_leverage")
    try:
        mark_price = float(mark_price)
    except (TypeError, ValueError):
        mark_price = None
    try:
        liquidation_price = float(liquidation_price)
    except (TypeError, ValueError):
        liquidation_price = None
    try:
        margin = float(margin)
    except (TypeError, ValueError):
        margin = None
    try:
        size = float(size)
    except (TypeError, ValueError):
        size = None
    try:
        total_quantity = float(total_quantity)
    except (TypeError, ValueError):
        total_quantity = None
    try:
        target_leverage = float(target_leverage)
    except (TypeError, ValueError):
        target_leverage = None

    liquidation_distance_pct = None
    if liquidation_price is None:
        logger.warning("Missing liquidation_price in position_info")
    elif not mark_price:
        logger.warning("Missing or zero mark_price in position_info")
    else:
        liquidation_distance_pct = abs(liquidation_price - mark_price) / mark_price * 100

    excess_margin = None
    if margin is None or size is None:
        logger.warning("Missing margin or size in position_info")
    elif not mark_price:
        logger.warning("Missing or zero mark_price in position_info")
    elif not target_leverage or target_leverage <= 0:
        logger.warning("Missing or invalid target_leverage in strategy_data")
    else:
        notional_value = abs(size) * mark_price
        required_margin = notional_value / target_leverage
        excess_margin = margin - required_margin

    delta_mismatch = None
    if total_quantity is None or size is None:
        logger.warning("Missing total_quantity in strategy_data or size in position_info")
    else:
        delta_mismatch = total_quantity - abs(size)

    position_health = None
    if liquidation_distance_pct is not None:
        if liquidation_distance_pct > 15:
            position_health = "HEALTHY"
        elif liquidation_distance_pct >= 5:
            position_health = "WARNING"
        else:
            position_health = "CRITICAL"

    return {
        "liquidation_distance_pct": (
            float(liquidation_distance_pct) if liquidation_distance_pct is not None else None
        ),
        "mark_price": mark_price,
        "liquidation_price": liquidation_price,
        "excess_margin": float(excess_margin) if excess_margin is not None else None,
        "delta_mismatch": float(delta_mismatch) if delta_mismatch is not None else None,
        "position_health": position_health,
    }
