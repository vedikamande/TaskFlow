"""
app.py - Main Flask REST API for TaskFlow
-----------------------------------------
This application handles all HTTP API endpoints for TaskFlow:
- GET    /api/health            -> Server health check
- GET    /api/tasks             -> Fetch all tasks & stats
- POST   /api/tasks             -> Create a new task
- PUT    /api/tasks/<id>        -> Update an existing task
- PATCH  /api/tasks/<id>/complete -> Mark task completed (or toggle)
- DELETE /api/tasks/<id>        -> Delete a task

Architecture Highlights:
1. RESTful design: Uses standard HTTP methods (GET, POST, PUT, PATCH, DELETE).
2. JSON communication: Uses request.get_json() and jsonify().
3. Parameterized SQL: Prevents SQL injection vulnerabilities with '?' placeholders.
4. Clean resource management: Connections are always closed in 'finally' blocks.
5. CORS enabled: Allows seamless interaction with React (Vite dev server).
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from database import get_db_connection, init_db, task_to_dict

# 1. Initialize Flask application
app = Flask(__name__)

# 2. Enable CORS (Cross-Origin Resource Sharing)
# Allows the React frontend running on localhost:5173 to call these APIs
CORS(app, resources={r"/*": {"origins": "*"}})

# 3. Automatically initialize database and tables on backend startup
with app.app_context():
    init_db()



# --------------------------------------------------------------------------
# Route 0: Root API Directory Endpoint
# --------------------------------------------------------------------------
@app.route("/", methods=["GET"])
@app.route("/api", methods=["GET"])
def api_index():
    """
    GET / and GET /api
    Root API directory endpoint providing an overview of all available TaskFlow endpoints,
    service health status, and quick usage guidance.
    """
    return jsonify({
        "name": "TaskFlow REST API",
        "status": "online",
        "version": "1.0.0",
        "message": "TaskFlow Backend API is running successfully!",
        "endpoints": {
            "root": "GET /",
            "health": "GET /api/health",
            "get_tasks": "GET /api/tasks",
            "create_task": "POST /api/tasks",
            "update_task": "PUT /api/tasks/<id>",
            "mark_complete": "PATCH /api/tasks/<id>/complete",
            "delete_task": "DELETE /api/tasks/<id>"
        },
        "docs": "Make requests to /api/health or /api/tasks for application operations."
    }), 200


# --------------------------------------------------------------------------
# Route 1: Health Check Endpoint
# --------------------------------------------------------------------------
@app.route("/api/health", methods=["GET"])
@app.route("/health", methods=["GET"])
def health_check():
    """
    GET /api/health (or GET /health)
    Used by the frontend or testing tools to check if the server is active.
    Returns: JSON with status 'ok' and HTTP 200.
    """
    return jsonify({
        "status": "ok",
        "message": "TaskFlow Backend API is running successfully!"
    }), 200


# --------------------------------------------------------------------------
# Route 2: Get All Tasks & Summary Statistics
# --------------------------------------------------------------------------
@app.route("/api/tasks", methods=["GET"])
@app.route("/tasks", methods=["GET"])
def get_tasks():
    """
    GET /api/tasks (or GET /tasks)
    Retrieves all tasks ordered by creation date (newest first).
    Also computes and returns total, pending, and completed task counts.
    Returns: JSON object with tasks array and summary stats.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Parameterized query to select all tasks ordered from newest to oldest
        cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC;")
        rows = cursor.fetchall()

        # Convert database rows to Python dictionaries
        task_list = [task_to_dict(row) for row in rows]

        # Calculate statistics
        total = len(task_list)
        completed = sum(1 for task in task_list if task["completed"])
        pending = total - completed

        return jsonify({
            "tasks": task_list,
            "stats": {
                "total": total,
                "pending": pending,
                "completed": completed
            }
        }), 200
    finally:
        conn.close()


# --------------------------------------------------------------------------
# Route 3: Create a New Task
# --------------------------------------------------------------------------
@app.route("/api/tasks", methods=["POST"])
@app.route("/tasks", methods=["POST"])
def create_task():
    """
    POST /api/tasks
    Accepts JSON body: { "title": "...", "description": "..." }
    Validates required fields, inserts task into SQLite, and returns the created task.
    Status Codes:
    - 201 Created on success
    - 400 Bad Request if title is missing
    """
    # 1. Parse incoming JSON body
    data = request.get_json(silent=True)

    if not data or not isinstance(data, dict):
        return jsonify({"error": "Invalid request. JSON body is required."}), 400

    title = data.get("title", "").strip()
    description = data.get("description", "").strip()

    # 2. Field validation: title is strictly required
    if not title:
        return jsonify({"error": "Task title is required."}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # 3. Secure parameterized INSERT query using '?' placeholders
        cursor.execute(
            """
            INSERT INTO tasks (title, description, completed)
            VALUES (?, ?, 0);
            """,
            (title, description)
        )
        conn.commit()

        # 4. Fetch the newly inserted task using cursor.lastrowid
        new_task_id = cursor.lastrowid
        cursor.execute("SELECT * FROM tasks WHERE id = ?;", (new_task_id,))
        new_task_row = cursor.fetchone()

        return jsonify({
            "message": "Task created successfully.",
            "task": task_to_dict(new_task_row)
        }), 201
    finally:
        conn.close()


# --------------------------------------------------------------------------
# Route 4: Update an Existing Task
# --------------------------------------------------------------------------
@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    """
    PUT /api/tasks/<id> (or PUT /tasks/<id>)
    Accepts JSON body: { "title": "...", "description": "...", "completed": true/false }
    Updates an existing task's title, description, and completion status.
    Status Codes:
    - 200 OK on success
    - 400 Bad Request if title is empty
    - 404 Not Found if task_id does not exist
    """
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"error": "Invalid request. JSON body is required."}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # 1. Check if the task exists in the database
        cursor.execute("SELECT * FROM tasks WHERE id = ?;", (task_id,))
        existing_row = cursor.fetchone()

        if existing_row is None:
            return jsonify({"error": f"Task with ID {task_id} not found."}), 404

        existing_task = task_to_dict(existing_row)

        # 2. Extract and validate fields
        new_title = data.get("title", existing_task["title"]).strip()
        if not new_title:
            return jsonify({"error": "Task title cannot be empty."}), 400

        new_description = data.get("description", existing_task["description"]).strip()

        # Determine completion flag (convert boolean or integer to 0 or 1)
        if "completed" in data:
            new_completed = 1 if data["completed"] else 0
        else:
            new_completed = 1 if existing_task["completed"] else 0

        # 3. Parameterized UPDATE query
        cursor.execute(
            """
            UPDATE tasks
            SET title = ?, description = ?, completed = ?
            WHERE id = ?;
            """,
            (new_title, new_description, new_completed, task_id)
        )
        conn.commit()

        # 4. Return the updated task
        cursor.execute("SELECT * FROM tasks WHERE id = ?;", (task_id,))
        updated_row = cursor.fetchone()

        return jsonify({
            "message": "Task updated successfully.",
            "task": task_to_dict(updated_row)
        }), 200
    finally:
        conn.close()


# --------------------------------------------------------------------------
# Route 5: Mark Task as Completed (or Toggle)
# --------------------------------------------------------------------------
@app.route("/api/tasks/<int:task_id>/complete", methods=["PATCH"])
@app.route("/tasks/<int:task_id>/complete", methods=["PATCH"])
def mark_task_completed(task_id):
    """
    PATCH /api/tasks/<id>/complete (or PATCH /tasks/<id>/complete)
    Marks a task as completed.
    Optionally accepts a JSON body: { "completed": true/false } to toggle.
    If no body is provided, it defaults to marking the task completed (1).
    Status Codes:
    - 200 OK on success
    - 404 Not Found if task_id does not exist
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Check if task exists
        cursor.execute("SELECT * FROM tasks WHERE id = ?;", (task_id,))
        existing_row = cursor.fetchone()

        if existing_row is None:
            return jsonify({"error": f"Task with ID {task_id} not found."}), 404

        # Read optional body or default to 1 (Completed)
        data = request.get_json(silent=True) or {}
        if "completed" in data:
            new_completed = 1 if data["completed"] else 0
        else:
            new_completed = 1

        # Parameterized update
        cursor.execute(
            "UPDATE tasks SET completed = ? WHERE id = ?;",
            (new_completed, task_id)
        )
        conn.commit()

        # Fetch and return updated task
        cursor.execute("SELECT * FROM tasks WHERE id = ?;", (task_id,))
        updated_row = cursor.fetchone()

        status_text = "completed" if new_completed == 1 else "pending"
        return jsonify({
            "message": f"Task marked as {status_text}.",
            "task": task_to_dict(updated_row)
        }), 200
    finally:
        conn.close()


# --------------------------------------------------------------------------
# Route 6: Delete a Task
# --------------------------------------------------------------------------
@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    """
    DELETE /api/tasks/<id> (or DELETE /tasks/<id>)
    Deletes the task with the given ID from SQLite.
    Status Codes:
    - 200 OK on success
    - 404 Not Found if task_id does not exist
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Check if task exists first
        cursor.execute("SELECT * FROM tasks WHERE id = ?;", (task_id,))
        existing_row = cursor.fetchone()

        if existing_row is None:
            return jsonify({"error": f"Task with ID {task_id} not found."}), 404

        # Parameterized DELETE query
        cursor.execute("DELETE FROM tasks WHERE id = ?;", (task_id,))
        conn.commit()

        return jsonify({
            "message": f"Task with ID {task_id} deleted successfully."
        }), 200
    finally:
        conn.close()


# --------------------------------------------------------------------------
# 404 Error Handler for Unknown Endpoints
# --------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found. Please verify the URL and HTTP method.",
        "requested_url": request.path,
        "requested_method": request.method,
        "available_endpoints": [
            {"method": "GET", "path": "/", "description": "API Root & Index"},
            {"method": "GET", "path": "/api/health", "description": "Server Health Check"},
            {"method": "GET", "path": "/api/tasks", "description": "Fetch All Tasks & Statistics"},
            {"method": "POST", "path": "/api/tasks", "description": "Create a New Task"},
            {"method": "PUT", "path": "/api/tasks/<id>", "description": "Update Task Details"},
            {"method": "PATCH", "path": "/api/tasks/<id>/complete", "description": "Mark Task Completed or Toggle"},
            {"method": "DELETE", "path": "/api/tasks/<id>", "description": "Delete Task"}
        ]
    }), 404


# --------------------------------------------------------------------------
# Main Server Entry Point
# --------------------------------------------------------------------------
if __name__ == "__main__":
    # Ensure SQLite tables exist before serving traffic
    init_db()

    print("==================================================")
    print(" TaskFlow Flask REST API Running")
    print(" Local Address: http://127.0.0.1:5000")
    print(" Database: backend/tasks.db")
    print("==================================================")

    # Start Flask server
    app.run(host="127.0.0.1", port=5000, debug=True)
