import os
from typing import Any, Dict, List, Optional

from src.repositories.json_repo import JsonShopRepository
from src.repositories.sqlite_repo import SqliteShopRepository
from src.tools.catalog_tools import check_stock, check_stock_by_id, list_all_products
from src.tools.pricing_tools import get_discount
from src.tools.shipping_tools import calc_shipping


def build_repository(
    backend: Optional[str] = None,
    json_data_dir: Optional[str] = None,
    sqlite_path: Optional[str] = None,
):
    selected_backend = (backend or os.getenv("DATA_BACKEND", "json")).strip().lower()

    if selected_backend == "sqlite":
        db_path = sqlite_path or os.getenv("SQLITE_PATH", "./db/shop.db")
        return SqliteShopRepository(db_path=db_path)

    data_dir = json_data_dir or os.getenv("JSON_DATA_DIR", "data")
    return JsonShopRepository(data_dir=data_dir)


def create_tool_registry(repo: Any) -> List[Dict[str, Any]]:
    def get_product(product_id: str) -> Dict[str, Any]:
        product = repo.get_product_by_id(product_id)
        if not product:
            return {"error": "item_not_found", "product_id": product_id}
        return product

    def estimate_total(
        product_id: str,
        quantity: int,
        coupon_code: str = "",
        destination: str = "hanoi",
    ) -> Dict[str, Any]:
        product = repo.get_product_by_id(product_id)
        if not product:
            return {"error": "item_not_found", "product_id": product_id}

        qty = max(int(quantity), 1)
        unit_price = float(product.get("price", 0))
        subtotal = unit_price * qty

        discount_pct = 0.0
        if coupon_code:
            discount_result = get_discount(coupon_code=coupon_code, repo=repo)
            discount_pct = float(discount_result.get("discount_pct", 0))

        discount_amount = subtotal * (discount_pct / 100.0)

        weight = float(product.get("weight", 0.0)) * qty
        shipping_result = calc_shipping(weight=weight, destination=destination)
        shipping_fee = float(shipping_result.get("shipping_fee", 0.0))

        total = subtotal - discount_amount + shipping_fee
        return {
            "product_id": product_id,
            "product_name": product.get("name"),
            "quantity": qty,
            "unit_price": unit_price,
            "subtotal": round(subtotal, 2),
            "discount_pct": discount_pct,
            "discount_amount": round(discount_amount, 2),
            "shipping_fee": round(shipping_fee, 2),
            "total": round(total, 2),
        }

    return [
        {
            "name": "list_all_products",
            "description": (
                "Return only product id and name for discovery/search. "
                "Use this first to map user description to a product id. "
                "Do not use this tool for detailed product info."
            ),
            "fn": lambda: list_all_products(repo=repo),
        },
        {
            "name": "check_stock",
            "description": "Check stock by exact product name and return product id if found.",
            "fn": lambda item_name: check_stock(item_name=item_name, repo=repo),
        },
        {
            "name": "check_stock_by_id",
            "description": "Check stock by product id. Prefer this after selecting product from list_all_products.",
            "fn": lambda product_id: check_stock_by_id(product_id=product_id, repo=repo),
        },
        {
            "name": "get_product_by_id",
            "description": "Return full product details by product id after product selection.",
            "fn": get_product,
        },
        {
            "name": "get_discount",
            "description": "Return discount percent for coupon code.",
            "fn": lambda coupon_code: get_discount(coupon_code=coupon_code, repo=repo),
        },
        {
            "name": "calc_shipping",
            "description": "Calculate shipping fee from package weight and destination.",
            "fn": calc_shipping,
        },
        {
            "name": "estimate_total",
            "description": (
                "Estimate final order total by product id, quantity, optional coupon code, and destination. "
                "Includes subtotal, discount, shipping, and total."
            ),
            "fn": estimate_total,
        },
    ]
