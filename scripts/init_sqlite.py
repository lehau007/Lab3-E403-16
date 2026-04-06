import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "shop.db"
SCHEMA_PATH = ROOT / "db" / "schema.sql"
PRODUCTS_PATH = ROOT / "data" / "products.sample.json"
COUPONS_PATH = ROOT / "data" / "coupons.sample.json"


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        with SCHEMA_PATH.open("r", encoding="utf-8") as f:
            conn.executescript(f.read())

        products = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))
        coupons = json.loads(COUPONS_PATH.read_text(encoding="utf-8"))

        conn.execute("DELETE FROM products")
        conn.execute("DELETE FROM coupons")

        conn.executemany(
            "INSERT INTO products(id, name, price, stock, weight) VALUES(?, ?, ?, ?, ?)",
            [(p["id"], p["name"], p["price"], p["stock"], p["weight"]) for p in products],
        )
        conn.executemany(
            "INSERT INTO coupons(code, discount_pct) VALUES(?, ?)",
            [(c["code"], c["discount_pct"]) for c in coupons],
        )

        conn.commit()


if __name__ == "__main__":
    main()
