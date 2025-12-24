# リポジトリ構造（Steering）
## 構成思想

- Layered（層構造）

  - ルーティング層（API）
  - サービス層（ビジネスロジック）
  - 永続化層（DBモデル/DBセッション）
  - 非同期処理層（Celeryタスク）
- Job（ジョブ）中心

  - 全ての処理は job_id をキーに状態/結果を蓄積し、APIはそれを参照・操作する

## ディレクトリ/ファイルの役割

### backend/

- backend/main.py

  - FastAPIアプリのエントリーポイント
  - 例外ハンドリング、CORS、router登録
- backend/routers/

  - HTTP API のコントラクト（入出力・ステータスコード）
  - jobs.py: ジョブ作成/状態/結果/校正/Proofread/QA
  - export.py: ダウンロード（TXT/SRT/VTT）
  - health.py: ヘルスチェック
  - schemas.py: Pydantic スキーマ（API契約）
- backend/services/

  - 外部連携と処理ロジックの中心
  - audio_extractor.py, transcription_service.py, correction_service.py, qa_service.py, export_service.py
  - job_manager.py: DB更新・永続化の集約
- backend/worker.py

  - Celeryタスク定義（非同期処理の実行）
- backend/celery_config.py

  - Celery設定（task_routes など運用上重要な設定）
- backend/database.py

  - SQLAlchemy Engine/Session と FastAPI依存注入（get_db）
- backend/models.py

  - SQLAlchemyモデル（DBスキーマのアプリ側表現）

### alembic/ と alembic.ini

- DBマイグレーション
- 方針として Alembic がスキーマの唯一の正

### audio_files/

- 音声抽出の生成物を置くランタイム領域
- Dockerではホストへマウントして永続化

### frontend/

- Next.js（App Router）プロジェクト
- frontend/src/app/: ページ/レイアウト
- frontend/src/components/: UIコンポーネント
- frontend/src/lib/api.ts: Backend API 呼び出し

### tests/

- pytest によるユニットテスト
- サービス層のテストが中心

### docker-compose.yml / Dockerfile.*

- ローカル開発・検証の標準実行環境
- migrate サービスで起動時にマイグレーションを適用

### start_app.sh / start_worker.sh

- `start_app.sh`: 開発時の標準起動スクリプト（compose 起動、Windows/WSL の Docker Desktop 未起動対策、`--with-frontend` 対応）
- `start_worker.sh`: ローカルで Celery worker を起動する補助スクリプト（通常は compose の worker を使う）

### ドキュメント（プロジェクト直下）

- README.md: セットアップ/使い方/環境変数の概要
- 起動手順.md: 起動確認・トラブルシュートの実務手順
- 開発メモ.md: 調査観点や既知問題（例: 長時間音声の末尾欠落、エクスポート仕様）

### .kiro/

- steering/: プロジェクト全体の方針
- specs/: 機能ごとの要件・設計・タスク

## 命名規約

- Python

  - モジュール/関数: snake_case
  - クラス: PascalCase
- TypeScript/React

  - コンポーネント: PascalCase
  - ファイル名: 既存に合わせる（componentsは PascalCase.tsx）

## 依存関係ルール（守る）

- routers は services を呼ぶが、services は routers に依存しない
- services は DB（models/job_manager）に依存してよいが、HTTP（FastAPI）には依存しない
- worker は services と DB に依存してよいが、routers（HTTP）には依存しない
- スキーマ変更は Alembic を必須とし、models の変更だけで済ませない
