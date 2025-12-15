# 技術方針（Steering）

本ファイルは「現コードの前提となる技術選定・運用方針」を固定化し、仕様・実装・運用のズレを抑える。

## 全体アーキテクチャ

- Backend: FastAPI（HTTP API）
- Worker: Celery（非同期ジョブ）
- Broker/Result Backend: Redis
- DB: PostgreSQL（SQLAlchemy + Alembic）
- Frontend: Next.js（React/TypeScript/Tailwind）
- 外部依存:
	- yt-dlp（YouTube音声抽出）
	- OpenAI API（Whisper 文字起こし、GPT 校正、Q&A）

中心概念は Job（ジョブ）。APIはジョブの作成・状態確認・追加処理依頼を担い、実処理（抽出/文字起こし/校正/Q&A）はWorkerが実行する。

## Backend（FastAPI）

- 実装配置
	- ルーティング: backend/routers/
	- 起動・例外ハンドリング: backend/main.py
	- DB: backend/database.py, backend/models.py
- 入力バリデーション
	- 422（RequestValidationError）を捕捉し、errors() を JSON 直列化して返す
- CORS
	- 現状は allow_origins=["*"]（開発向け）。本番はオリジンを絞る。

## Worker（Celery）

- 実装配置: backend/worker.py
- タスク（現コード）
	- worker.transcription_task
		- AudioExtractor → TranscriptionService → JobManager（DB更新）
	- worker.correction_task
		- Transcript → CorrectionService → JobManager（CorrectedTranscript upsert）
	- worker.proofread_task
		- Transcript → CorrectionService → JobManager（CorrectedTranscript upsert）
	- worker.qa_task
		- CorrectedTranscript（あれば）/ Transcript → QaService → JobManager（QaResult 追加）
- リトライ
	- 各タスクは max_retries とバックオフ設定を持ち、例外時に自動リトライする

### キュー設計（重要）

- ルーティングの正は backend/celery_config.py の task_routes
- キュー
	- transcription: worker.transcription_task
	- correction: worker.correction_task / worker.proofread_task / worker.qa_task
- worker は transcription と correction を購読して起動する

## DB（SQLAlchemy + Alembic）

### 方針: Alembic をスキーマの唯一の正（Single Source of Truth）とする

- スキーマ変更は Alembic マイグレーションでのみ行う
- アプリ起動時に create_all は実行しない（スキーマは migrate で適用する）

### 起動時マイグレーション

- docker-compose.yml の migrate サービスで alembic upgrade head を実行し、完了後に API/Worker を起動する
- DB接続は DATABASE_URL を単一の契約として統一する

## 音声抽出（yt-dlp）

- 実装配置: backend/services/audio_extractor.py
- 生成物は audio_files/ に出力し、Dockerではホストへマウントして永続化する

## OpenAI API

- OPENAI_API_KEY は必須（未設定時は各サービスが失敗を返す）
- 文字起こし: backend/services/transcription_service.py
	- 音声ファイルの25MB上限チェックがある
- 校正: backend/services/correction_service.py
	- 言語別プロンプトを内包
	- 長文は分割して複数リクエストする設計
- Q&A: backend/services/qa_service.py
	- Transcriptに基づく回答を促す（含まれない情報は「見つからない」と答える）

## Frontend（Next.js）

- 実装配置: frontend/
- API クライアント: frontend/src/lib/api.ts
- UIコンポーネント
	- URL入力: frontend/src/components/UrlInputForm.tsx
	- 状態表示: frontend/src/components/JobStatus.tsx
	- 結果/Proofread/QA/Export: frontend/src/components/TranscriptResult.tsx

## 環境変数（運用上の契約）

- DATABASE_URL: PostgreSQL 接続文字列
- REDIS_URL: Redis 接続文字列
- OPENAI_API_KEY: OpenAI APIキー

## 重要な技術的意思決定（今後も守る）

- 起動時の Alembic 自動適用（migrate サービス）を維持し、スキーマ未適用で起動しない
- Celery のルーティングと worker 購読キューの整合を維持し、「投げたのに実行されない」を防ぐ
- エクスポートは校正文があれば優先する（表示とダウンロードの整合性）
