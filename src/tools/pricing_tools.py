from typing import Any, Dict


def get_discount(coupon_code: str, repo: Any) -> Dict[str, Any]:
    coupons = repo.get_coupons()
    for c in coupons:
        if c.get("code", "").lower() == coupon_code.lower():
            return {"coupon": c.get("code"), "discount_pct": c.get("discount_pct", 0)}
    return {"coupon": coupon_code, "discount_pct": 0, "note": "coupon_not_found"}
