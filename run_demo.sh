#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

cleanup() {
  [[ -n "${API_PID:-}" ]] && kill "$API_PID" 2>/dev/null || true
  [[ -n "${FE_PID:-}" ]] && kill "$FE_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

if [[ ! -d venv ]]; then
  echo "Missing venv/. Create it and pip install -r requirements.txt first."
  exit 1
fi

echo "Starting API on http://127.0.0.1:8000 …"
./venv/bin/uvicorn src.api:app --host 127.0.0.1 --port 8000 &
API_PID=$!

# Wait for health
for i in {1..30}; do
  if curl -sf http://127.0.0.1:8000/health >/dev/null; then
    echo "API ready."
    break
  fi
  sleep 0.5
done

echo "Starting frontend on http://localhost:5173 …"
(
  cd frontend
  npm run dev -- --host 127.0.0.1 --port 5173
) &
FE_PID=$!

echo ""
echo "RxGuard India demo"
echo "  UI:  http://localhost:5173"
echo "  API: http://127.0.0.1:8000/docs"
echo "Press Ctrl+C to stop."
wait
