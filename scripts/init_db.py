"""Initialize the demo SQLite system of record."""

import os
import sqlite3


def init_database(db_path: str = "data/veritas.db") -> None:
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        with open("data/schema.sql", encoding="utf-8") as schema_file:
            connection.executescript(schema_file.read())
    print(f"Database initialized at {db_path}")


if __name__ == "__main__":
    init_database()
