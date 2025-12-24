# YouTube Transcription Web App

YouTube動画の音声を抽出し、日本語・英語の文字起こしとLLM校正を提供するWebアプリケーション。

## Features

- YouTube動画URLからの音声抽出
- 日本語・英語の高精度文字起こし（OpenAI Whisper API）
- LLMによるテキスト校正（GPT-4o）
- 複数形式でのエクスポート（TXT、SRT、VTT）
- 非同期処理による高速な処理
- レスポンシブなWebUI

## Architecture

- **Frontend**: React + Next.js
- **Backend**: FastAPI (Python)
- **Task Queue**: Celery + Redis
- **Database**: PostgreSQL
- **Audio Extraction**: yt-dlp
- **Speech-to-Text**: OpenAI Whisper API
- **LLM Correction**: OpenAI GPT-4o

## Prerequisites

- Docker & Docker Compose
- OpenAI API Key
- ffmpeg（大容量音声の自動圧縮/分割に使用）

> NOTE (WSL2 + Docker Desktop): WSL ディストリビューション側で `docker` が見えない場合、Docker Desktop の
> Settings → Resources → WSL Integration で使用中のディストリを有効化してから再試行してください。

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd 0106_cc-sdd
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` and set your OpenAI API key:

```
OPENAI_API_KEY=your_actual_api_key_here
```

### 3. Start Services

```bash
docker compose up -d
```

If your environment still uses the legacy `docker-compose` command, you can run:

```bash
docker-compose up -d
```

Or use the helper script:

```bash
chmod +x start_app.sh
./start_app.sh
```

To start the UI as well:

```bash
./start_app.sh --with-frontend
```

### 4. Verify Services

```bash
docker compose ps
```

All services (postgres, redis, api, worker) should be running.

### 5. Setup Frontend (Optional)

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

### 6. Access Application

- Frontend: http://localhost:3000 (Next.js UI)
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Development

### Run Tests

```bash
# Create venv (PEP 668 environment requires venv)
python3 -m venv .venv
. .venv/bin/activate

# Install dependencies
python -m pip install -r requirements.txt

# Run tests
pytest tests/
```

## Large File Support (over 25MB)

OpenAI の音声アップロード制限（デフォルト 25MB）を超える場合、ワーカーが自動で以下を行います：

- まず音声を **音声認識向けに圧縮**（mono / 16kHz / mp3 / 低ビットレート）
- それでも大きい場合は **分割**（チャンク間に短いオーバーラップを付与）
- 各チャンクを個別に文字起こしし、**タイムスタンプ（segments）をオフセットで連結**

### Environment Variables

- `MAX_UPLOAD_MB`：入力ファイルの防御的な上限（デフォルト `25`）
- `TARGET_UPLOAD_MB`：圧縮/分割後に目指す上限（安全マージン、デフォルト `24`）
- `AUDIO_BITRATE_KBPS`：圧縮時のビットレート（デフォルト `48`）
- `CHUNK_OVERLAP_SEC`：分割チャンクのオーバーラップ秒（デフォルト `0.8`）
- `MAX_SINGLE_CHUNK_SEC`：サイズが小さくても長時間音声を分割する閾値（デフォルト `900`）。長い音声を1リクエストで投げると末尾が欠ける場合があるため、安定化のために分割します。`0` 以下で無効化。

### Notes

- `ffmpeg` が PATH に無い場合、大容量ファイルの処理は失敗します。
- タイムスタンプは可能な場合に `verbose_json` の `segments` を保存し、SRT/VTT 出力に利用します。モデルやAPI仕様により segments が得られない場合は従来方式（均等割り当て）にフォールバックします。

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### Start Celery Worker (Local Development)

**Windows:**
```bash
start_worker.bat
```

**Linux/Mac:**
```bash
chmod +x start_worker.sh
./start_worker.sh
```

**Or run directly:**
```bash
celery -A backend.worker worker --loglevel=info --concurrency=2
```

NOTE: Celery worker は自動リロードしません。バックエンドコードを変更した場合は worker を再起動してください。

### Stop Services

```bash
docker compose down
```

### Clean Up (including volumes)

```bash
docker compose down -v
```

## Project Structure

```
.
├── backend/              # Backend application code
│   ├── main.py          # FastAPI application entry point
│   ├── worker.py        # Celery worker tasks
│   ├── models.py        # SQLAlchemy database models
│   ├── database.py      # Database connection
│   ├── celery_config.py # Celery configuration
│   ├── routers/         # API route handlers
│   │   ├── jobs.py      # Job management endpoints
│   │   ├── export.py    # Export endpoints
│   │   ├── health.py    # Health check endpoint
│   │   └── schemas.py   # Pydantic request/response models
│   └── services/        # Business logic services
│       ├── audio_extractor.py          # YouTube audio extraction
│       ├── transcription_service.py    # Whisper API integration
│       ├── correction_service.py       # LLM correction
│       ├── export_service.py           # Export to TXT/SRT/VTT
│       └── job_manager.py              # Job lifecycle management
├── tests/               # Test suite
│   ├── test_audio_extractor.py
│   ├── test_transcription_service.py
│   ├── test_correction_service.py
│   ├── test_export_service.py
│   └── test_infrastructure.py
├── alembic/             # Database migrations
├── audio_files/         # Generated audio files (runtime)
├── .kiro/               # Spec-driven development files
│   └── specs/youtube-transcription/
│       ├── requirements.md   # Feature requirements
│       ├── design.md         # Technical design
│       └── tasks.md          # Implementation tasks
├── docker-compose.yml   # Docker orchestration
├── Dockerfile.api       # API container
├── Dockerfile.worker    # Worker container
├── requirements.txt     # Python dependencies
├── test_integration.py  # Integration test script
└── .env.example         # Environment template
```

## Implementation Status

### ✅ Phase 1: プロジェクト基盤構築 (Completed)
- Docker環境セットアップ
- データベーススキーマ設計
- タスクキューシステム構築

### ✅ Phase 2: コアサービス実装 (Completed)
- YouTube音声抽出サービス
- 文字起こしサービス
- LLM校正サービス
- エクスポートサービス

### ✅ Phase 3: バックエンドAPI構築 (Completed)
- FastAPIアプリケーションセットアップ
- ジョブ管理エンドポイント
- エクスポートエンドポイント
- ヘルスチェックエンドポイント

### ✅ Phase 5: 統合とテスト (Partially Completed)
- ワーカータスクの統合
- 統合テストスクリプト

### ✅ Phase 4: フロントエンド実装 (Completed)
- Next.js 14 + TypeScript + Tailwind CSS
- YouTube URL入力UI
- 進行状況表示UI
- 文字起こし結果表示UI
- LLM校正と前後比較UI
- エクスポート機能UI

## API Endpoints

### Job Management
- `POST /api/jobs/transcribe` - Create new transcription job
- `GET /api/jobs/{job_id}/status` - Get job status
- `GET /api/jobs/{job_id}/result` - Get transcription result
- `POST /api/jobs/{job_id}/correct` - Request LLM correction

### Export
- `GET /api/jobs/{job_id}/export?format=txt|srt|vtt` - Export transcript

Notes:
- 校正済み（`corrected_transcript` が存在）なら、エクスポートは校正後テキストが優先されます。
- SRT/VTT の `segments` はオリジナル transcript 側（`transcripts.segments_json`）から読み込みます。

### Monitoring
- `GET /health` - Health check
- `GET /` - Service info

## Testing

### Run Integration Tests

```bash
# Make sure API is running
python test_integration.py
```

### Run Unit Tests

```bash
pytest tests/ -v
```

## License

MIT
