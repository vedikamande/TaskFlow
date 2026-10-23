"""
TaskFlow - Root Application Runner
----------------------------------
Convenience launcher to run the TaskFlow Flask REST API from the project root.
When running 'python app.py' in the root TaskFlow directory, this launcher loads
the backend application from backend/app.py and starts the server.
"""

import os
import sys
import importlib.util

# Set backend directory path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")

# Ensure sys.argv[0] is absolute so Werkzeug reloader preserves the runner path on restart
sys.argv[0] = os.path.abspath(sys.argv[0])

# Ensure backend directory is in sys.path so its internal imports (e.g. database) resolve
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Change current working directory to backend so sqlite and relative paths resolve accurately
os.chdir(BACKEND_DIR)

# Dynamically load the backend app module to avoid circular name collision with root app.py
backend_app_path = os.path.join(BACKEND_DIR, "app.py")
spec = importlib.util.spec_from_file_location("taskflow_backend", backend_app_path)
taskflow_backend = importlib.util.module_from_spec(spec)
sys.modules["taskflow_backend"] = taskflow_backend

try:
    spec.loader.exec_module(taskflow_backend)
except ModuleNotFoundError as err:
    print("\n" + "=" * 60)
    print(" [TaskFlow Dependency Notice]")
    print(f" Missing dependency: '{err.name}'")
    print(" Please start the server using the backend virtual environment:")
    print(r"   .\backend\venv\Scripts\python.exe app.py")
    print(" Or activate it first:")
    print(r"   cd backend; .\venv\Scripts\Activate.ps1; python app.py")
    print("=" * 60 + "\n")
    sys.exit(1)

app = taskflow_backend.app
init_db = taskflow_backend.init_db
build_frontend = taskflow_backend.build_frontend
start_server = taskflow_backend.start_server

if __name__ == "__main__":
    start_server(host="127.0.0.1", port=5000, debug=True)

