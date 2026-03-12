# ============================================================
# Stage 1: Build React frontend
# ============================================================
FROM node:20-alpine AS frontend

WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build
# Wynik: /dist/ (outDir: '../dist' w vite.config.js)

# ============================================================
# Stage 2: Python backend + gotowy frontend
# ============================================================
FROM python:3.11-slim

WORKDIR /app

# Czcionki DejaVu dla PDF (polskie znaki)
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Zależności Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kod backendu
COPY . .

# Usunięcie zbędnych folderów z kontenera
RUN rm -rf frontend/ dist/ tests/ archive/ output/ knr_database/ \
    __pycache__ *.pyc .git

# Skopiowany build frontendu
COPY --from=frontend /dist ./dist

# Port (Railway ustawia $PORT automatycznie)
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "gunicorn server:app -k uvicorn.workers.UvicornWorker -w 2 --timeout 300 --keep-alive 5 --bind 0.0.0.0:${PORT:-8000}"]
