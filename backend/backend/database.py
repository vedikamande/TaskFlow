"""
database.py - Database Setup & Connection Helper for TaskFlow
-------------------------------------------------------------
This module manages our embedded SQLite database (tasks.db).
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "tasks.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(seed_sample_data=True):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.commit()

        cursor.execute("SELECT COUNT(*) AS count FROM tasks;")
        row_count = cursor.fetchone()["count"]

        if row_count == 0 and seed_sample_data:
            initial_tasks = [
                ("Learn Python", "Practice functions", 0),
                ("Build React UI", "Create components", 1),
                ("Complete assignment", "Finish coursework", 0),
            ]
            cursor.executemany(
                """
                INSERT INTO tasks (title, description, completed)
                VALUES (?, ?, ?);
                """,
                initial_tasks
            )
            conn.commit()
            print(f"[Database] Table 'tasks' created and seeded with {len(initial_tasks)} conceptual tasks.")
        else:
            print(f"[Database] Table 'tasks' ready ({row_count} existing records).")

        print("[Database] Connected to SQLite database:", DB_PATH)
    finally:
        conn.close()


def task_to_dict(row):
    if row is None:
        return None
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"] or "",
        "completed": bool(row["completed"]),
        "created_at": row["created_at"],
    }


if __name__ == "__main__":
    init_db()
