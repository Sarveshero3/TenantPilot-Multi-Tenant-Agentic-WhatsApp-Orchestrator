# ── Stage 1: Build the React frontend ────────────────────────────────────────
FROM node:22-alpine AS frontend-build

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --silent
COPY frontend/ .
RUN npm run build

# ── Stage 2: Python backend + serve frontend static files ────────────────────
FROM python:3.11-slim AS production

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps (none needed for our pure-Python stack, but keeping
# the layer for future extension like Pillow/numpy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend source
COPY backend/ .

# Copy the built frontend into a static directory served by FastAPI
COPY --from=frontend-build /frontend/dist /app/static

# Expose the backend port
EXPOSE 8000

# Health check (reads PORT env var dynamically, defaulting to 8000)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request, os; port = os.getenv('PORT', '8000'); urllib.request.urlopen(f'http://localhost:{port}/health')" || exit 1

# Run the application (reads PORT env var dynamically, defaulting to 8000)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

