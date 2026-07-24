from __future__ import annotations

from datetime import date
from contextlib import closing
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
VENDOR = ROOT / ".vendor"
if VENDOR.exists():
    sys.path.insert(0, str(VENDOR))

from flask import Flask, jsonify, render_template, request

from database import DEFAULT_DB_PATH, connect, init_db, row_to_product, utc_now
from maya_calendar import convert_birth_date


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=os.environ.get("MAYA_DB_PATH", str(DEFAULT_DB_PATH)),
        ADMIN_TOKEN=os.environ.get("MAYA_ADMIN_TOKEN", "demo-admin"),
        ENABLE_ANALYTICS=os.environ.get("MAYA_ENABLE_ANALYTICS", "0") == "1",
        JSON_AS_ASCII=False,
    )
    if test_config:
        app.config.update(test_config)

    init_db(app.config["DATABASE"])

    def db():
        return connect(app.config["DATABASE"])

    def require_admin():
        token = request.headers.get("X-Admin-Token", "")
        return token and token == app.config["ADMIN_TOKEN"]

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/admin")
    def admin():
        return render_template("admin.html")

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "birthday-totem-h5"})

    @app.get("/api/products")
    def products():
        with closing(db()) as conn:
            rows = conn.execute("SELECT * FROM products ORDER BY product_no").fetchall()
        return jsonify({"items": [row_to_product(row) for row in rows]})

    @app.get("/api/products/<int:product_no>")
    def product(product_no: int):
        with closing(db()) as conn:
            row = conn.execute("SELECT * FROM products WHERE product_no=?", (product_no,)).fetchone()
        if row is None:
            return jsonify({"error": "未找到该产品"}), 404
        return jsonify(row_to_product(row))

    @app.post("/api/calculate")
    def calculate():
        payload = request.get_json(silent=True) or {}
        raw_date = str(payload.get("birthDate", ""))
        try:
            birth_date = date.fromisoformat(raw_date)
        except ValueError:
            return jsonify({"error": "请输入有效的公历日期"}), 400

        if birth_date > date.today():
            return jsonify({"error": "出生日期不能晚于今天"}), 400
        if birth_date.year < 1900:
            return jsonify({"error": "Demo 当前支持1900年至今天"}), 400

        result = convert_birth_date(birth_date)
        with closing(db()) as conn:
            row = conn.execute(
                "SELECT * FROM products WHERE symbol_index=?", (result.symbol_index,)
            ).fetchone()
            if row is None:
                return jsonify({"error": "产品映射尚未配置"}), 500
            product_data = row_to_product(row)
            if app.config["ENABLE_ANALYTICS"]:
                conn.execute(
                    "INSERT INTO calculation_events(product_id, created_at) VALUES (?, ?)",
                    (row["id"], utc_now()),
                )
                conn.commit()

        response = result.to_dict()
        response["product"] = product_data
        response["display_name"] = str(payload.get("name", "")).strip()[:30]
        return jsonify(response)

    @app.put("/api/admin/products/<int:product_no>")
    def update_product(product_no: int):
        if not require_admin():
            return jsonify({"error": "管理令牌无效"}), 401
        payload = request.get_json(silent=True) or {}
        allowed = {
            "keywords", "story", "material", "price_cents", "stock_status",
            "hero_image", "product_image",
        }
        values = {key: payload[key] for key in allowed if key in payload}
        if not values:
            return jsonify({"error": "没有可更新的字段"}), 400
        if "stock_status" in values and values["stock_status"] not in {
            "in_stock", "low_stock", "sold_out"
        }:
            return jsonify({"error": "库存状态无效"}), 400

        setters = ", ".join(f"{key}=?" for key in values)
        params = list(values.values()) + [utc_now(), product_no]
        with closing(db()) as conn:
            cursor = conn.execute(
                f"UPDATE products SET {setters}, updated_at=? WHERE product_no=?",
                params,
            )
            if cursor.rowcount == 0:
                return jsonify({"error": "未找到该产品"}), 404
            row = conn.execute("SELECT * FROM products WHERE product_no=?", (product_no,)).fetchone()
            conn.commit()
        return jsonify(row_to_product(row))

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
