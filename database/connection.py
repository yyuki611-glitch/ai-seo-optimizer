import sqlite3
import os
from pathlib import Path
from typing import Optional


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """SQLite接続を返す。db_path未指定時は環境変数 DB_PATH を使用。"""
    path = db_path or os.getenv("DB_PATH", "data/articles.db")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def initialize_db(conn: sqlite3.Connection) -> None:
    """schema.sql を読み込みテーブルを作成する。"""
    schema_path = Path(__file__).parent / "schema.sql"
    conn.executescript(schema_path.read_text())
    conn.commit()
