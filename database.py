from __future__ import annotations

from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from urllib.parse import quote


ROOT = Path(__file__).resolve().parent
DEFAULT_DB_PATH = ROOT / "data" / "maya_calendar.db"


PRODUCTS = [
    # symbol_index, product_no, key, zh, nahuatl, en, keywords, story, icon, accent
    (0, 5, "cipactli", "鳄", "Cipactli", "Caiman", "稳如泰山 / 镇守", "象征大地初生的力量、稳定与守护，适合作为踏实前行的随身纪念。", "鳄", "teal"),
    (1, 6, "ehecatl", "风", "Ehecatl", "Wind", "顺风顺水 / 自由", "象征流动、呼吸与改变，提醒人们保持自由，也保持前进的方向。", "风", "blue"),
    (2, 7, "calli", "房", "Calli", "House", "阖家团聚 / 安居", "象征居所、家人与内心的安定，是关于归属与团聚的一枚日符。", "房", "gold"),
    (3, 8, "cuetzpalin", "蜥", "Cuetzpalin", "Lizard", "破茧蜕变 / 逢凶化吉", "象征敏捷、更新与适应变化，在转折中找到新的生长方式。", "蜥", "green"),
    (4, 9, "coatl", "蛇", "Coatl", "Snake", "智慧生发 / 灵慧", "象征生命力、智慧与蜕变，适合送给正在开启新阶段的人。", "蛇", "red"),
    (5, 10, "miquiztli", "新生", "Miquiztli", "Rebirth", "涅槃重生 / 新生", "并非终结，而是旧事物的放下与新阶段的开始，象征更新和重生。", "新生", "sand"),
    (6, 11, "mazatl", "鹿", "Mazatl", "Deer", "福禄双全 / 指引", "象征温和、警觉与指引，以从容的脚步找到适合自己的道路。", "鹿", "gold"),
    (7, 12, "tochtli", "兔", "Tochtli", "Rabbit", "温和圆满 / 丰沛", "象征丰盛、敏锐与温柔，在轻盈中保有旺盛的生命力。", "兔", "green"),
    (8, 13, "atl", "水", "Atl", "Water", "海纳百川 / 聚财", "象征包容、流动与滋养，以柔软的方式抵达更远的地方。", "水", "blue"),
    (9, 14, "itzcuintli", "狗", "Itzcuintli", "Dog", "忠诚守护 / 挚友", "象征忠诚、陪伴与守护，是送给家人、朋友和伙伴的温暖日符。", "狗", "teal"),
    (10, 15, "ozomahtli", "猴", "Ozomahtli", "Monkey", "灵巧聪慧 / 欢愉", "象征创造、聪慧与快乐，在好奇和游戏中发现新的可能。", "猴", "red"),
    (11, 16, "malinalli", "草", "Malinalli", "Grass", "坚韧不拔 / 向阳", "象征韧性、修复与向阳生长，即使经历风雨，也能重新站起。", "草", "green"),
    (12, 17, "acatl", "苇", "Acatl", "Reed", "节节高升 / 柔韧", "象征方向、成长和柔韧，保持原则，也懂得顺势而行。", "苇", "gold"),
    (13, 18, "ocelotl", "美洲豹", "Ocelotl", "Jaguar", "勇者无畏 / 守护辟邪", "灵感来自美洲豹日符。象征勇气、敏锐与守护，适合作为随身纪念或送给重要的人。", "美洲豹", "red"),
    (14, 19, "cuauhtli", "鹰", "Cuauhtli", "Eagle", "大展宏图 / 远见", "象征高度、视野与行动力，从更高处看见方向，也勇于向前。", "鹰", "blue"),
    (15, 20, "cozcacuauhtli", "鹫", "Cozcacuauhtli", "Vulture", "健康长寿 / 豁达", "象征净化、长久与豁达，把经历转化为智慧与新的能量。", "鹫", "sand"),
    (16, 1, "ollin", "震", "Ollin", "Earthquake", "时来运转 / 生机", "象征运动、改变与生机，在变化中把握节奏，开启新的运转。", "震", "teal"),
    (17, 2, "tecpatl", "石", "Tecpatl", "Knife", "披荆斩棘 / 决断", "象征清晰、决断与突破，帮助人们切开犹疑，专注真正重要的方向。", "石", "blue"),
    (18, 3, "quiahuitl", "雨", "Quiahuitl", "Rain", "财源广进 / 甘霖", "象征滋养、丰收与及时的馈赠，让付出获得生长所需的力量。", "雨", "gold"),
    (19, 4, "xochitl", "花", "Xochitl", "Flower", "繁花似锦 / 结缘", "象征美、创造与人与人之间的连接，让日常开出属于自己的花。", "花", "red"),
]

DATE_GOD_TRANSLITERATIONS = {
    "cipactli": "西帕克特利",
    "ehecatl": "埃赫卡特尔",
    "calli": "卡利",
    "cuetzpalin": "库埃茨帕林",
    "coatl": "库瓦特尔",
    "miquiztli": "米基斯特里",
    "mazatl": "玛萨特尔",
    "tochtli": "托奇特利",
    "atl": "阿特",
    "itzcuintli": "伊茨奎恩特利",
    "ozomahtli": "奥索马特利",
    "malinalli": "马利纳利",
    "acatl": "阿卡特尔",
    "ocelotl": "奥塞洛特尔",
    "cuauhtli": "库阿特利",
    "cozcacuauhtli": "科斯卡夸乌特利",
    "ollin": "奥林",
    "tecpatl": "特克帕特尔",
    "quiahuitl": "基亚维特尔",
    "xochitl": "索奇特尔",
}

COS_DATE_GOD_BASE_URL = "https://maya-1408948459.cos.ap-guangzhou.myqcloud.com/20_Date_God/"
COS_DATE_GOD_FILENAMES = {
    sign_key: f"{transliteration}_{next(row[4] for row in PRODUCTS if row[2] == sign_key)}.png"
    for sign_key, transliteration in DATE_GOD_TRANSLITERATIONS.items()
}


SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol_index INTEGER NOT NULL UNIQUE,
    product_no INTEGER NOT NULL UNIQUE,
    sign_key TEXT NOT NULL UNIQUE,
    name_zh TEXT NOT NULL,
    name_nahuatl TEXT NOT NULL,
    name_en TEXT NOT NULL,
    keywords TEXT NOT NULL,
    story TEXT NOT NULL,
    icon_text TEXT NOT NULL,
    accent TEXT NOT NULL DEFAULT 'red',
    material TEXT NOT NULL DEFAULT '黄铜镀金 / 皮绳（Demo）',
    price_cents INTEGER,
    stock_status TEXT NOT NULL DEFAULT 'in_stock',
    hero_image TEXT,
    product_image TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS calculation_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(product_id) REFERENCES products(id)
);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(path: Path | str = DEFAULT_DB_PATH) -> None:
    now = utc_now()
    with closing(connect(path)) as conn:
        conn.executescript(SCHEMA)
        for row in PRODUCTS:
            conn.execute(
                """
                INSERT OR IGNORE INTO products (
                    symbol_index, product_no, sign_key, name_zh, name_nahuatl,
                    name_en, keywords, story, icon_text, accent, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (*row, now, now),
            )
        conn.execute(
            """
            UPDATE products
            SET
                name_zh = CASE WHEN name_zh = '死' THEN '新生' ELSE name_zh END,
                name_en = CASE WHEN name_en = 'Death' THEN 'Rebirth' ELSE name_en END,
                icon_text = CASE WHEN icon_text = '死' THEN '新生' ELSE icon_text END,
                updated_at = ?
            WHERE sign_key = 'miquiztli'
              AND (name_zh = '死' OR name_en = 'Death' OR icon_text = '死')
            """,
            (now,),
        )
        conn.execute(
            """
            UPDATE products
            SET
                name_zh = CASE WHEN name_zh = '豹' THEN '美洲豹' ELSE name_zh END,
                icon_text = CASE WHEN icon_text = '豹' THEN '美洲豹' ELSE icon_text END,
                updated_at = ?
            WHERE sign_key = 'ocelotl'
              AND (name_zh = '豹' OR icon_text = '豹')
            """,
            (now,),
        )
        conn.execute(
            "INSERT OR IGNORE INTO app_settings(key, value, updated_at) VALUES (?, ?, ?)",
            ("correlation", "GMT 584283", now),
        )
        conn.commit()


def row_to_product(row: sqlite3.Row) -> dict:
    data = dict(row)
    sign_key = data["sign_key"]
    filename = COS_DATE_GOD_FILENAMES[sign_key]
    data["name_transliteration"] = DATE_GOD_TRANSLITERATIONS[sign_key]
    data["date_god_image"] = COS_DATE_GOD_BASE_URL + quote(filename)
    data["price"] = None if data["price_cents"] is None else data["price_cents"] / 100
    data["in_stock"] = data["stock_status"] == "in_stock"
    return data
