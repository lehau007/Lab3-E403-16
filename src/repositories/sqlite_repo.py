import sqlite3
from typing import Any, Dict, List


class SqliteShopRepository:
    def __init__(self, db_path: str = "db/shop.db"):
        self.db_path = db_path

    def query(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]

    def get_products(self) -> List[Dict[str, Any]]:
        return self.query("SELECT id, name, price, stock, weight FROM products")

    def get_product_by_id(self, product_id: str) -> Dict[str, Any]:
        rows = self.query(
            "SELECT id, name, price, stock, weight FROM products WHERE lower(id) = lower(?)",
            (product_id,),
        )
        return rows[0] if rows else {}

    def get_coupons(self) -> List[Dict[str, Any]]:
        return self.query("SELECT code, discount_pct FROM coupons")
