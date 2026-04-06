from typing import Any, Dict


def list_all_products(repo: Any) -> Dict[str, Any]:
    """Return the entire product catalog so the agent can ground on real IDs."""
    products = repo.get_products()
    normalized = []
    for p in products:
        normalized.append(
            {
                "id": p.get("id"),
                "name": p.get("name"),
                "price": p.get("price"),
                "stock": p.get("stock"),
                "weight": p.get("weight"),
            }
        )
    return {"count": len(normalized), "products": normalized}


def check_stock(item_name: str, repo: Any) -> Dict[str, Any]:
    products = repo.get_products()
    for p in products:
        if p.get("name", "").lower() == item_name.lower():
            return {"id": p.get("id"), "item": p.get("name"), "stock": p.get("stock", 0)}
    return {"error": "item_not_found", "item": item_name}


def check_stock_by_id(product_id: str, repo: Any) -> Dict[str, Any]:
    product = repo.get_product_by_id(product_id)
    if not product:
        return {"error": "item_not_found", "product_id": product_id}
    return {
        "id": product.get("id"),
        "item": product.get("name"),
        "stock": product.get("stock", 0),
    }
