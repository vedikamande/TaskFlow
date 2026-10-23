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

import os
import sys
import subprocess
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from database import get_db_connection, init_db, task_to_dict

# Base directories
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, ".."))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
FRONTEND_DIST = os.path.join(FRONTEND_DIR, "dist")


def build_frontend():
    """
    Build the React frontend production bundle using Vite.
    Runs 'npm run build' inside the frontend directory so that
    the Flask backend serves the up-to-date application bundle.
    If npm is not installed (e.g. in lightweight production Docker image)
    and the compiled bundle already exists, serving proceeds seamlessly.
    """
    import shutil
    index_file = os.path.join(FRONTEND_DIST, "index.html")
    has_prebuilt_dist = os.path.exists(index_file)

    if not shutil.which("npm"):
        if has_prebuilt_dist:
            print(" [TaskFlow] Serving pre-compiled React frontend bundle from frontend/dist.", flush=True)
            return True
        print(f" [TaskFlow WARNING] 'npm' command not found and bundle missing at: {index_file}", flush=True)
        return False

    print("\n" + "=" * 60, flush=True)
    print(" [TaskFlow] Building React frontend via Vite...", flush=True)
    print(f" Working Directory: {FRONTEND_DIR}", flush=True)
    print("=" * 60, flush=True)
    if not os.path.exists(FRONTEND_DIR):
        print(f" [TaskFlow ERROR] Frontend directory not found at: {FRONTEND_DIR}", flush=True)
        print("=" * 60 + "\n", flush=True)
        return False

    try:
        # shell=True enables Windows to resolve npm.cmd correctly
        process = subprocess.run(
            "npm run build",
            cwd=FRONTEND_DIR,
            shell=True,
            capture_output=True,
            text=True,
            check=False
        )
        if process.returncode == 0:
            print(" [TaskFlow] Frontend build succeeded!", flush=True)
            print(f" Serving build assets from: {FRONTEND_DIST}", flush=True)
            print("=" * 60 + "\n", flush=True)
            return True
        else:
            print(f" [TaskFlow ERROR] Frontend build failed (exit code {process.returncode}):", flush=True)
            if process.stdout:
                print(process.stdout.strip(), flush=True)
            if process.stderr:
                print(process.stderr.strip(), flush=True)
            print("=" * 60 + "\n", flush=True)
            return False
    except Exception as exc:
        print(f" [TaskFlow EXCEPTION] Failed to execute build command: {exc}", flush=True)
        print("=" * 60 + "\n", flush=True)
        return False


# 1. Initialize Flask application
app = Flask(__name__, static_folder=None)

# 2. Enable CORS (Cross-Origin Resource Sharing)
# Allows the React frontend running on localhost:5173 to call these APIs
CORS(app, resources={r"/*": {"origins": "*"}})

# 3. Automatically initialize database and tables on backend startup
with app.app_context():
    init_db()


# --------------------------------------------------------------------------
# Route 0: Frontend Single-Page Application (SPA) Root
# --------------------------------------------------------------------------
@app.route("/", methods=["GET"])
def serve_frontend_root():
    """
    GET /
    Serves the production React frontend single-page application (index.html)
    from frontend/dist. If not yet built, attempts an automatic build.
    """
    index_path = os.path.join(FRONTEND_DIST, "index.html")
    if not os.path.exists(index_path):
        build_frontend()

    if os.path.exists(index_path):
        return send_from_directory(FRONTEND_DIST, "index.html")

    return jsonify({
        "error": "Frontend build not found.",
        "hint": "Please run 'npm run build' inside the frontend directory or restart the backend."
    }), 404


# --------------------------------------------------------------------------
# Route 0B: Root API Directory Endpoint
# --------------------------------------------------------------------------
@app.route("/api", methods=["GET"])
def api_index():
    """
    GET /api
    Root API directory endpoint providing an overview of all available TaskFlow endpoints,
    service health status, and quick usage guidance.
    """
    return jsonify({
        "name": "TaskFlow REST API",
        "status": "online",
        "version": "1.0.0",
        "message": "TaskFlow Backend API is running successfully!",
        "endpoints": {
            "frontend_ui": "GET / (React Frontend Application)",
            "api_index": "GET /api",
            "health": "GET /api/health",
            "get_tasks": "GET /api/tasks",
            "create_task": "POST /api/tasks",
            "update_task": "PUT /api/tasks/<id>",
            "mark_complete": "PATCH /api/tasks/<id>/complete",
            "delete_task": "DELETE /api/tasks/<id>",
            "trigger_build": "POST /api/build"
        },
        "docs": "Make requests to /api/health or /api/tasks for application operations."
    }), 200


# --------------------------------------------------------------------------
# Route 0C: On-Demand Frontend Build Endpoint
# --------------------------------------------------------------------------
@app.route("/api/build", methods=["POST"])
def trigger_build():
    """
    POST /api/build
    Allows triggering a frontend rebuild on-demand via an API request.
    """
    success = build_frontend()
    if success:
        return jsonify({
            "message": "Frontend built successfully.",
            "dist_path": FRONTEND_DIST
        }), 200
    return jsonify({
        "error": "Frontend build failed. Please check server console logs."
    }), 500


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
# Route 7: Frontend Static Assets & SPA Catch-All
# --------------------------------------------------------------------------
@app.route("/<path:path>", methods=["GET"])
def serve_frontend_assets(path):
    """
    Serve static assets (CSS, JS, SVG, images) from frontend/dist.
    If the requested path does not match a physical file, falls back to index.html
    to support client-side routing, while preserving 404 for missing /api routes.
    """
    # Guard the /api namespace from serving index.html
    if path.startswith("api/") or path == "api":
        return not_found(None)

    # Check if a physical static file exists in frontend/dist (e.g. assets/..., favicon.svg)
    file_path = os.path.join(FRONTEND_DIST, path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_from_directory(FRONTEND_DIST, path)

    # SPA client-side routing fallback: return index.html
    index_file = os.path.join(FRONTEND_DIST, "index.html")
    if os.path.exists(index_file):
        return send_from_directory(FRONTEND_DIST, "index.html")

    return not_found(None)


# --------------------------------------------------------------------------
# 404 Error Handler for Unknown Endpoints
# --------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(error):
    # If the user requested a non-api route and index.html exists, fallback to SPA
    if not request.path.startswith("/api"):
        index_file = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.exists(index_file):
            return send_from_directory(FRONTEND_DIST, "index.html")

    return jsonify({
        "error": "Endpoint not found. Please verify the URL and HTTP method.",
        "requested_url": request.path,
        "requested_method": request.method,
        "available_endpoints": [
            {"method": "GET", "path": "/", "description": "React Frontend Application UI"},
            {"method": "GET", "path": "/api", "description": "API Root & Index"},
            {"method": "GET", "path": "/api/health", "description": "Server Health Check"},
            {"method": "GET", "path": "/api/tasks", "description": "Fetch All Tasks & Statistics"},
            {"method": "POST", "path": "/api/tasks", "description": "Create a New Task"},
            {"method": "PUT", "path": "/api/tasks/<id>", "description": "Update Task Details"},
            {"method": "PATCH", "path": "/api/tasks/<id>/complete", "description": "Mark Task Completed or Toggle"},
            {"method": "DELETE", "path": "/api/tasks/<id>", "description": "Delete Task"},
            {"method": "POST", "path": "/api/build", "description": "Trigger Frontend Rebuild"}
        ]
    }), 404


# --------------------------------------------------------------------------
# Server Startup Function & Entry Point
# --------------------------------------------------------------------------
def start_server(host=None, port=None, debug=None):
    """
    Starts the full-stack TaskFlow server.
    Ensures the SQLite database is initialized and builds the React frontend
    before serving traffic. Also rebuilds whenever the server reloads.
    Supports environment variables: HOST, PORT, FLASK_DEBUG for containerized deployment.
    """
    # 1. Resolve host, port, and debug mode dynamically
    if host is None:
        host = os.environ.get("HOST", "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1")
    if port is None:
        port = int(os.environ.get("PORT", 5000))
    if debug is None:
        debug = os.environ.get("FLASK_DEBUG", "true").lower() in ("true", "1")

    # 2. Initialize SQLite schema
    init_db()

    # 3. Build frontend on server startup or reload
    is_worker = os.environ.get("WERKZEUG_RUN_MAIN") == "true"
    index_missing = not os.path.exists(os.path.join(FRONTEND_DIST, "index.html"))
    if is_worker or not debug or index_missing:
        build_frontend()

    print("==================================================", flush=True)
    print(" TaskFlow Full-Stack Server Running", flush=True)
    print(f" Application UI: http://{host}:{port}/", flush=True)
    print(f" REST API Base:  http://{host}:{port}/api", flush=True)
    print(f" Serving Bundle: {FRONTEND_DIST}", flush=True)
    print(" Database:       backend/tasks.db", flush=True)
    print("==================================================", flush=True)

    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    start_server()
