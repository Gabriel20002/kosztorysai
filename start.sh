#!/bin/bash
# KosztorysAI — buduje frontend i uruchamia serwer
# Użycie: ./start.sh [--port 8000] [--skip-build]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="/mnt/c/Users/Gabriel/Desktop/MVP kosztorysy/buildai-app"
PORT=8000
SKIP_BUILD=0

for arg in "$@"; do
  case $arg in
    --port=*) PORT="${arg#*=}" ;;
    --port)   shift; PORT="$1" ;;
    --skip-build) SKIP_BUILD=1 ;;
  esac
done

echo "================================================"
echo "  KosztorysAI"
echo "================================================"

# Build frontendu
if [ "$SKIP_BUILD" -eq 0 ]; then
  echo ""
  echo "[1/2] Budowanie frontendu React..."
  if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo "  → Instalowanie zależności npm..."
    npm --prefix "$FRONTEND_DIR" install
  fi
  npm --prefix "$FRONTEND_DIR" run build
  echo "  ✓ Frontend zbudowany → $SCRIPT_DIR/dist/"
else
  echo "[1/2] Pomijam build (--skip-build)"
fi

# Start serwera
echo ""
echo "[2/2] Uruchamiam serwer na porcie $PORT..."
echo ""
cd "$SCRIPT_DIR"
python3 server.py --port "$PORT"
