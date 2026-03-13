import pytest
import sqlite3
from database.connection import initialize_db


@pytest.fixture
def db_conn():
    """インメモリSQLiteコネクション（テスト毎に初期化）。"""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    initialize_db(conn)
    yield conn
    conn.close()
