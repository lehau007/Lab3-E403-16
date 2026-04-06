import json
from pathlib import Path
from typing import Any, Dict, List


class JsonShopRepository:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)

    def _load(self, file_name: str) -> List[Dict[str, Any]]:
        path = self.data_dir / file_name
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def get_products(self) -> List[Dict[str, Any]]:
        return self._load("products.sample.json")

    def get_product_by_id(self, product_id: str) -> Dict[str, Any]:
        for product in self.get_products():
            if str(product.get("id", "")).lower() == str(product_id).lower():
                return product
        return {}

    def get_coupons(self) -> List[Dict[str, Any]]:
        return self._load("coupons.sample.json")
