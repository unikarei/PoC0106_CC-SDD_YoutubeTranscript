#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

usage() {
  cat <<'EOF'
Usage:
  ./start_app.sh [--foreground] [--no-build] [--logs] [--with-frontend]

Starts the backend stack via Docker Compose (postgres, redis, migrate, api, worker).

Options:
  --foreground     Run docker compose in the foreground (no -d)
  --no-build       Do not rebuild images
  --logs           After starting (detached), follow api/worker logs
  --with-frontend  Also start Next.js dev server (requires Node.js)
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

# Load environment variables (especially OPENAI_API_KEY) if .env exists.
# docker compose also reads .env automatically, but we validate here.
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "ERROR: OPENAI_API_KEY is not set." >&2
  echo "- Put it in .env (recommended), or" >&2
  echo "- export OPENAI_API_KEY=..." >&2
  exit 1
fi

if docker compose version >/dev/null 2>&1; then
  DC=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  DC=(docker-compose)
else
  echo "ERROR: docker compose (v2) or docker-compose is required." >&2
  exit 1
fi

DETACH=1
BUILD=1
FOLLOW_LOGS=0
WITH_FRONTEND=0

for arg in "$@"; do
  case "$arg" in
    --foreground)
      DETACH=0
      ;;
    --no-build)
      BUILD=0
      ;;
    --logs)
      FOLLOW_LOGS=1
      ;;
    --with-frontend)
      WITH_FRONTEND=1
      ;;
    *)
      echo "Unknown option: $arg" >&2
      usage
      exit 2
      ;;
  esac
done

UP_ARGS=(up)
if [[ $DETACH -eq 1 ]]; then
  UP_ARGS+=(-d)
fi
if [[ $BUILD -eq 1 ]]; then
  UP_ARGS+=(--build)
fi

"${DC[@]}" "${UP_ARGS[@]}"

"${DC[@]}" ps

echo
echo "Backend is starting." 
echo "- API:  http://localhost:8000"
echo "- Docs: http://localhost:8000/docs"
echo

if [[ $DETACH -eq 1 && $FOLLOW_LOGS -eq 1 ]]; then
  "${DC[@]}" logs -f api worker
fi

if [[ $WITH_FRONTEND -eq 1 ]]; then
  if ! command -v npm >/dev/null 2>&1; then
    echo "ERROR: npm is not installed. Install Node.js to run the frontend." >&2
    exit 1
  fi

  echo
  echo "Starting frontend (Next.js) on http://localhost:3000 ..."
  pushd frontend >/dev/null
  if [[ ! -d node_modules ]]; then
    npm install
  fi
  npm run dev
  popd >/dev/null
fi
