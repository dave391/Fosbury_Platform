import time
from typing import Any, Dict, Optional

from app.services.strategies.nv1.rules import get_default_thresholds

DEFAULT_THRESHOLDS = get_default_thresholds()


def decide(metrics: Dict[str, Any], thresholds: Dict[str, Any], last_action_timestamp: Optional[float] = None) -> Dict[str, Any]:
    t = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    distance = metrics.get("liquidation_distance_pct")
    excess_margin = float(metrics.get("excess_margin") or 0.0)
    delta_mismatch = metrics.get("delta_mismatch")
    size = metrics.get("size")
    has_delta_mismatch = False
    if size not in (None, 0) and delta_mismatch is not None:
        has_delta_mismatch = abs(float(delta_mismatch)) / abs(float(size)) > (float(t["max_delta_mismatch_pct"]) / 100.0)
    if distance is None:
        return {"action": "HOLD", "reason": "liquidation price not available", "params": None, "has_delta_mismatch": has_delta_mismatch}
    distance = float(distance)
    if distance < float(t["critical_distance_pct"]):
        return {"action": "EMERGENCY_CLOSE", "reason": f"liquidation distance {distance}% below critical threshold {t['critical_distance_pct']}%", "params": {}, "has_delta_mismatch": has_delta_mismatch}
    now = time.time()
    if last_action_timestamp is not None and now - float(last_action_timestamp) < float(t["cooldown_seconds"]):
        return {"action": "HOLD", "reason": "cooldown active", "params": None, "has_delta_mismatch": has_delta_mismatch}
    if distance < float(t["warning_distance_pct"]):
        return {"action": "SCALE_DOWN", "reason": f"liquidation distance {distance}% below warning threshold {t['warning_distance_pct']}%", "params": {"target_distance_pct": float(t["safe_distance_pct"])}, "has_delta_mismatch": has_delta_mismatch}
    if distance > float(t["safe_distance_pct"]) and excess_margin > float(t["min_excess_margin"]):
        return {"action": "SCALE_UP", "reason": f"liquidation distance {distance}% above safe threshold {t['safe_distance_pct']}% with excess margin {excess_margin}", "params": {"excess_margin": float(excess_margin)}, "has_delta_mismatch": has_delta_mismatch}
    return {"action": "HOLD", "reason": "no rebalance condition met", "params": None, "has_delta_mismatch": has_delta_mismatch}
