#!/bin/bash

set -euo pipefail

# run02_app.sh は start_app.sh の起動モードを呼び分ける薄いラッパー。
# デフォルトは「バックエンド + フロントエンド(Docker)」で起動する。

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'HELP'
使い方:
  ./run02_app.sh [mode]

mode:
  backend           バックエンドのみ起動
  docker-frontend   バックエンド + フロント(Docker)  ※デフォルト
  local-frontend    バックエンド + フロント(ローカルNode)

例:
  OPEN_API_KEY="sk-proj-..." ./run02_app.sh
  OPEN_API_KEY="sk-proj-..." ./run02_app.sh backend
  OPEN_API_KEY="sk-proj-..." ./run02_app.sh local-frontend
HELP
  exit 0
fi

MODE="${1:-docker-frontend}"

case "$MODE" in
  backend)
    exec ./start_app.sh --no-build
    ;;
  docker-frontend)
    exec ./start_app.sh --with-frontend --no-build
    ;;
  local-frontend)
    exec ./start_app.sh --frontend-local --no-build
    ;;
  *)
    echo "Unknown mode: $MODE" >&2
    echo "Try: ./run02_app.sh --help" >&2
    exit 1
    ;;
esac
