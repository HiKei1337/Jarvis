import sqlite3
import threading
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Database:
    def __init__(self):
        self.lock = threading.Lock()
        self.conn = sqlite3.connect(
            str(BASE_DIR / "jarvis.db"),
            check_same_thread=False,
        )
        self.create()

    def create(self):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory(
            id INTEGER PRIMARY KEY,
            user TEXT,
            jarvis TEXT
            )
            """)
            self.conn.commit()

    def save(self, user, jarvis):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO memory(user, jarvis) VALUES (?, ?)",
                (user, jarvis),
            )
            self.conn.commit()
