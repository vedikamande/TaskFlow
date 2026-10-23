"""
database.py - Database Setup & Connection Helper for TaskFlow
-------------------------------------------------------------
This module manages our embedded SQLite database (tasks.db).

Key concepts for beginners:
1. SQLite: A lightweight database stored inside a single file (tasks.db).
   No separate database server like MySQL or PostgreSQL is required!
2. Parameterized queries (?): Always pass user input as tuple arguments
   to cursor.execute() instead of string concatenation. This prevents
   SQL injection attacks.
3. Row factory: Setting row_factory = sqlite3.Row allows us to access
   columns by name (e.g. row['title']) instead of index numbers.
"""

import sqlite3
import os

# Define the absolute path to tasks.db in the same directory as this file
DB_PATH = os.path.join(os.path.dirname(__file__), "tasks.db")


def get_db_connection():
    """
    Opens and returns a connection to the SQLite database.
    
    Setting row_factory = sqlite3.Row lets us treat retrieved database
    rows like Python dictionaries.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(seed_sample_data=True):
    """
    Automatically creates the 'tasks.db' SQLite file and the 'tasks' table
    if they do not already exist when the backend starts.

    Table Schema:
    - id: INTEGER PRIMARY KEY AUTOINCREMENT (Uniquely identifies each task)
    - title: TEXT NOT NULL (Stores the task name)
    - description: TEXT DEFAULT '' (Stores additional details)
    - completed: INTEGER NOT NULL DEFAULT 0 (0 = Pending, 1 = Completed)
    - created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP (Auto creation timestamp)

    Automatic Seeding:
    If the table is newly created or empty, seeds initial demonstration tasks:
    1. Learn Python         | Practice functions | 0 (pending)
    2. Build React UI       | Create components  | 1 (completed)
    3. Complete assignment  | Finish coursework  | 0 (pending)
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # 1. Automatically create the table if it doesn't exist
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

        # 2. Check if the table is currently empty and seed if requested
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
        # Always close connection to free system resources
        conn.close()


def task_to_dict(row):
    """
    Helper function to convert an SQLite Row object into a JSON-friendly Python dict.
    Converts SQLite's integer 0/1 completed flag into a true boolean (False/True).
    """
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
    # Allows running `python database.py` to initialize or inspect the database
    init_db()
