from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from database import DEFAULT_DB_PATH, init_db

if __name__ == "__main__":
    init_db(DEFAULT_DB_PATH)
    print(f"Database ready: {DEFAULT_DB_PATH}")

