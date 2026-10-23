"""
app.py - Main Flask REST API for TaskFlow (in backend/backend)
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from database import get_db_connection, init_db, task_to_dict

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

with app.app_context():
    init_db()

@app.route("/", methods=["GET"])
@app.route("/api", methods=["GET"])
def api_index():
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

@app.route("/api/health", methods=["GET"])
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "ok",
        "message": "TaskFlow Backend API is running successfully!"
    }), 200

@app.route("/api/tasks", methods=["GET"])
@app.route("/tasks", methods=["GET"])
def get_tasks():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC;")
        rows = cursor.fetchall()
        task_list = [task_to_dict(row) for row in rows]
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

@app.route("/api/tasks", methods=["POST"])
@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"error": "Invalid request. JSON body is required."}), 400
    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    if not title:
        return jsonify({"error": "Task title is required."}), 400
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (title, description, completed) VALUES (?, ?, 0);",
            (title, description)
        )
        conn.commit()
        new_task_id = cursor.lastrowid
        cursor.execute("SELECT * FROM tasks WHERE id = ?;", (new_task_id,))
        new_task_row = cursor.fetchone()
        return jsonify({
            "message": "Task created successfully.",
            "task": task_to_dict(new_task_row)
        }), 201
    finally:
        conn.close()

@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"error": "Invalid request. JSON body is required."}), 400
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?;", (task_id,))
        existing_row = cursor.fetchone()
        if existing_row is None:
            return jsonify({"error": f"Task with ID {task_id} not found."}), 404
        existing_task = task_to_dict(existing_row)
        new_title = data.get("title", existing_task["title"]).strip()
        if not new_title:
            return jsonify({"error": "Task title cannot be empty."}), 400
        new_description = data.get("description", existing_task["description"]).strip()
        if "completed" in data:
            new_completed = 1 if data["completed"] else 0
        else:
            new_completed = 1 if existing_task["completed"] else 0
        cursor.execute(
            "UPDATE tasks SET title = ?, description = ?, completed = ? WHERE id = ?;",
            (new_title, new_description, new_completed, task_id)
        )
        conn.commit()
        cursor.execute("SELECT * FROM tasks WHERE id = ?;", (task_id,))
        updated_row = cursor.fetchone()
        return jsonify({
            "message": "Task updated successfully.",
            "task": task_to_dict(updated_row)
        }), 200
    finally:
        conn.close()

@app.route("/api/tasks/<int:task_id>/complete", methods=["PATCH"])
@app.route("/tasks/<int:task_id>/complete", methods=["PATCH"])
def mark_task_completed(task_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?;", (task_id,))
        existing_row = cursor.fetchone()
        if existing_row is None:
            return jsonify({"error": f"Task with ID {task_id} not found."}), 404
        data = request.get_json(silent=True) or {}
        if "completed" in data:
            new_completed = 1 if data["completed"] else 0
        else:
            new_completed = 1
        cursor.execute(
            "UPDATE tasks SET completed = ? WHERE id = ?;",
            (new_completed, task_id)
        )
        conn.commit()
        cursor.execute("SELECT * FROM tasks WHERE id = ?;", (task_id,))
        updated_row = cursor.fetchone()
        status_text = "completed" if new_completed == 1 else "pending"
        return jsonify({
            "message": f"Task marked as {status_text}.",
            "task": task_to_dict(updated_row)
        }), 200
    finally:
        conn.close()

@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?;", (task_id,))
        existing_row = cursor.fetchone()
        if existing_row is None:
            return jsonify({"error": f"Task with ID {task_id} not found."}), 404
        cursor.execute("DELETE FROM tasks WHERE id = ?;", (task_id,))
        conn.commit()
        return jsonify({
            "message": f"Task with ID {task_id} deleted successfully."
        }), 200
    finally:
        conn.close()

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

if __name__ == "__main__":
    init_db()
    print("TaskFlow Flask REST API Running on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
