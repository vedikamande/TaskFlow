# ==============================================================================
# Stage 1: Build React Frontend Assets (Vite)
# ==============================================================================
FROM node:22-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend dependency manifests
COPY frontend/package.json ./

# Install npm dependencies
RUN npm install

# Copy frontend source code
COPY frontend/ ./

# Compile production single-page application into dist/
RUN npm run build

# ==============================================================================
# Stage 2: Final Production Runtime (Python Flask API & Static Server)
# ==============================================================================
FROM python:3.12-alpine

# Set production environment variables for performance and container routing
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000 \
    HOST=0.0.0.0 \
    PYTHONPATH=/app:/app/backend

WORKDIR /app

# Install lightweight dependencies & production WSGI server (Gunicorn)
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy backend application files and root launcher
COPY backend/ ./backend/
COPY app.py ./

# Copy compiled frontend assets from Stage 1 into frontend/dist
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose default container port
EXPOSE 5000

# Start production server using Gunicorn dynamically bound to $PORT (default 5000)
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 app:app"]
