from pathlib import Path
from tempfile import TemporaryDirectory
from contextlib import closing
import unittest

from app import create_app
from database import connect, init_db


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.db_path = Path(self.temp.name) / "test.db"
        self.app = create_app({"TESTING": True, "DATABASE": str(self.db_path), "ADMIN_TOKEN": "secret"})
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def test_health_and_twenty_products(self):
        self.assertEqual(self.client.get("/api/health").status_code, 200)
        data = self.client.get("/api/products").get_json()
        self.assertEqual(len(data["items"]), 20)
        self.assertEqual(len({item["date_god_image"] for item in data["items"]}), 20)
        for item in data["items"]:
            self.assertTrue(item["name_transliteration"])
            self.assertTrue(item["date_god_image"].startswith("https://maya-1408948459.cos.ap-guangzhou.myqcloud.com/20_Date_God/"))
            self.assertTrue(item["date_god_image"].endswith(f"_{item['name_nahuatl']}.png"))

    def test_pages_and_frontend_assets_are_served(self):
        self.assertIn("生日图腾", self.client.get("/").get_data(as_text=True))
        self.assertIn("20款产品管理", self.client.get("/admin").get_data(as_text=True))
        css_response = self.client.get("/static/css/app.css")
        js_response = self.client.get("/static/js/app.js")
        self.assertEqual(css_response.status_code, 200)
        self.assertEqual(js_response.status_code, 200)
        css_response.close()
        js_response.close()

    def test_all_date_god_assets_are_served(self):
        sign_keys = [
            "ollin", "tecpatl", "quiahuitl", "xochitl", "cipactli",
            "ehecatl", "calli", "cuetzpalin", "coatl", "miquiztli",
            "mazatl", "tochtli", "atl", "itzcuintli", "ozomahtli",
            "malinalli", "acatl", "ocelotl", "cuauhtli", "cozcacuauhtli",
        ]
        for size in ("full", "icon"):
            for sign_key in sign_keys:
                response = self.client.get(f"/static/img/date-gods/{size}/{sign_key}.png")
                self.assertEqual(response.status_code, 200, f"{size}/{sign_key}.png")
                response.close()

    def test_calculate_returns_unique_product(self):
        response = self.client.post("/api/calculate", json={"birthDate": "2026-07-15", "name": "  小玛  "})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["product_no"], 18)
        self.assertEqual(data["product"]["name_nahuatl"], "Ocelotl")
        self.assertEqual(data["display_name"], "小玛")

    def test_result_page_has_optional_personal_title_without_glyph_english_label(self):
        page = self.client.get("/").get_data(as_text=True)
        self.assertIn('id="result-display-name"', page)
        self.assertIn('id="result-personal-copy"', page)
        self.assertIn("用于结果页和分享卡署名", page)
        self.assertNotIn('id="result-nahuatl-small"', page)

    def test_rebirth_product_and_share_calendar(self):
        products = self.client.get("/api/products").get_json()["items"]
        rebirth = next(item for item in products if item["product_no"] == 10)
        self.assertEqual(rebirth["name_zh"], "新生")
        self.assertEqual(rebirth["name_en"], "Rebirth")
        self.assertEqual(rebirth["name_nahuatl"], "Miquiztli")
        page = self.client.get("/").get_data(as_text=True)
        self.assertNotIn('id="share-nahuatl-small"', page)
        self.assertIn('id="share-long-count-glyphs"', page)
        self.assertIn('id="share-tzolkin-text"', page)
        self.assertIn('id="share-haab-text"', page)
        self.assertIn('id="share-night-lord-text"', page)
        self.assertIn("GMT 584283", page)

    def test_american_jaguar_name_and_chinese_transliteration(self):
        jaguar = self.client.get("/api/products/18").get_json()
        eagle = self.client.get("/api/products/19").get_json()
        self.assertEqual(jaguar["name_zh"], "美洲豹")
        self.assertEqual(jaguar["name_transliteration"], "奥塞洛特尔")
        self.assertEqual(eagle["name_transliteration"], "库阿特利")
        page = self.client.get("/").get_data(as_text=True)
        self.assertIn('id="result-name-transliteration"', page)
        self.assertIn('id="product-name-transliteration"', page)
        self.assertIn('id="share-name-transliteration"', page)
        self.assertIn('id="calendar-name-transliteration"', page)

    def test_legacy_rebirth_name_migrates_without_overwriting_custom_name(self):
        with closing(connect(self.db_path)) as conn:
            conn.execute(
                "UPDATE products SET name_zh = '死', name_en = 'Death', icon_text = '死' WHERE sign_key = 'miquiztli'"
            )
            conn.commit()
        init_db(self.db_path)
        migrated = self.client.get("/api/products/10").get_json()
        self.assertEqual((migrated["name_zh"], migrated["name_en"], migrated["icon_text"]), ("新生", "Rebirth", "新生"))

        with closing(connect(self.db_path)) as conn:
            conn.execute(
                "UPDATE products SET name_zh = '焕新', name_en = 'Renewal', icon_text = '焕新' WHERE sign_key = 'miquiztli'"
            )
            conn.commit()
        init_db(self.db_path)
        customized = self.client.get("/api/products/10").get_json()
        self.assertEqual((customized["name_zh"], customized["name_en"], customized["icon_text"]), ("焕新", "Renewal", "焕新"))

    def test_rejects_future_and_old_dates(self):
        self.assertEqual(self.client.post("/api/calculate", json={"birthDate": "2099-01-01"}).status_code, 400)
        self.assertEqual(self.client.post("/api/calculate", json={"birthDate": "1899-12-31"}).status_code, 400)

    def test_admin_requires_token_and_persists_update(self):
        denied = self.client.put("/api/admin/products/18", json={"keywords": "测试"})
        self.assertEqual(denied.status_code, 401)
        saved = self.client.put("/api/admin/products/18", headers={"X-Admin-Token": "secret"}, json={"keywords": "勇气 / 守护", "price_cents": 29900})
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(saved.get_json()["price"], 299)
        create_app({"TESTING": True, "DATABASE": str(self.db_path), "ADMIN_TOKEN": "secret"})
        reloaded = self.client.get("/api/products/18").get_json()
        self.assertEqual(reloaded["keywords"], "勇气 / 守护")


if __name__ == "__main__":
    unittest.main()
