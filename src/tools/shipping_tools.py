from typing import Any, Dict


def calc_shipping(weight: float, destination: str) -> Dict[str, Any]:
    base = 15000.0
    per_kg = 12000.0
    surcharge = 1.2 if destination.strip().lower() in {"hcm", "ho chi minh"} else 1.0
    shipping_fee = (base + per_kg * max(weight, 0.0)) * surcharge
    return {"destination": destination, "shipping_fee": round(shipping_fee, 2)}
