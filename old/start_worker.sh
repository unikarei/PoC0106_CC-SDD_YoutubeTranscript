#!/bin/bash
# Worker startup script for local development

set -euo pipefail

cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Load environment variables
if [ -f ".env" ]; then
    set -a
    # shellcheck disable=SC1090
    source <(sed 's/\r$//' .env)
    set +a
fi

# ------------------------------------------------------------
# Docker の起動確認（Windows/WSL: Docker Desktop を自動起動して待つ）
# - Worker自体はローカル起動だが、Redis/Postgres等をDockerで起動しているケースが多いため
# ------------------------------------------------------------
is_windows_like() {
    case "$(uname -s 2>/dev/null || true)" in
        MINGW*|MSYS*|CYGWIN*) return 0 ;;
    esac
    if [[ -r /proc/version ]] && grep -qi microsoft /proc/version 2>/dev/null; then
        return 0
    fi
    return 1
}

docker_daemon_ready() {
    docker info >/dev/null 2>&1
}

start_docker_desktop() {
    if command -v powershell.exe >/dev/null 2>&1; then
        powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command '
$p1Base = [System.Environment]::GetEnvironmentVariable("ProgramFiles")
$p2Base = [System.Environment]::GetEnvironmentVariable("ProgramFiles(x86)")
$p1 = Join-Path $p1Base "Docker\Docker\Docker Desktop.exe"
$p2 = if ($p2Base) { Join-Path $p2Base "Docker\Docker\Docker Desktop.exe" } else { $null }
if (Test-Path $p1) { Start-Process -FilePath $p1 | Out-Null; exit 0 }
elseif ($p2 -and (Test-Path $p2)) { Start-Process -FilePath $p2 | Out-Null; exit 0 }
else { exit 2 }
' >/dev/null 2>&1
        return $?
    fi

    if command -v cmd.exe >/dev/null 2>&1; then
        cmd.exe /c "start \"\" \"%ProgramFiles%\\Docker\\Docker\\Docker Desktop.exe\"" >/dev/null 2>&1 && return 0
        cmd.exe /c "start \"\" \"%ProgramFiles(x86)%\\Docker\\Docker\\Docker Desktop.exe\"" >/dev/null 2>&1 && return 0
        return 2
    fi

    return 127
}

if command -v docker >/dev/null 2>&1; then
    if ! docker_daemon_ready; then
        if is_windows_like; then
            echo "Docker daemon is not reachable. Trying to start Docker Desktop..." >&2
            if ! start_docker_desktop; then
                echo "ERROR: Failed to start Docker Desktop automatically." >&2
                echo "- Please start Docker Desktop manually and retry." >&2
                exit 1
            fi
            echo "Waiting for Docker to become ready..." >&2
            for _ in {1..60}; do
                if docker_daemon_ready; then
                    break
                fi
                sleep 2
            done
            if ! docker_daemon_ready; then
                echo "ERROR: Docker Desktop did not become ready in time." >&2
                echo "- Please check Docker Desktop status and retry." >&2
                exit 1
            fi
        else
            echo "ERROR: Docker is not running (docker daemon unreachable)." >&2
            echo "- Start Docker and retry." >&2
            exit 1
        fi
    fi
fi

# Start Celery worker
cd backend

celery -A worker worker \
    --loglevel=info \
    --concurrency=2 \
    --max-tasks-per-child=1000 \
    --queues=transcription,correction
