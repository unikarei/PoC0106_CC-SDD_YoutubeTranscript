# プロダクト概要（Steering）

本プロダクトは、YouTube動画のURLを入力すると、音声抽出→文字起こし→（任意で）LLM校正→（任意で）Q&A→エクスポート（TXT/SRT/VTT）までを一連のジョブとして非同期に実行できるWebアプリケーションである。

## 対象ユーザー

- 動画の内容をテキスト化して読解・検索・引用したい利用者（個人/チーム）
- 字幕（SRT/VTT）を必要とする利用者
- 文字起こし結果に対して追加質問（Q&A）を行いたい利用者

## プロダクトのゴール

- YouTube URL 1本を「ジョブ」として扱い、処理の進捗・状態・結果を追跡できる
- 文字起こし（OpenAI Whisper）を自動化し、結果をDBに永続化する
- 校正（LLM）を任意で実行し、結果をDBに永続化する
- 文字起こし/校正文を基にQ&Aを任意で実行し、履歴として蓄積できる
- エクスポート（TXT/SRT/VTT）をファイルとしてダウンロードできる

## 標準の起動体験（開発時の期待値）

- 起動は `./start_app.sh` を標準とする（docker compose 直叩きよりも環境差分に強い）
- GUI も含める場合は `./start_app.sh --with-frontend` を標準とする
  - UI: http://localhost:3000
  - API: http://localhost:8000
  - Docs: http://localhost:8000/docs

補足:
- Windows/WSL で Docker Desktop 未起動の場合、スクリプトは「起動を促す/可能なら自動起動して待機」する。

## 非ゴール（現時点で提供しない）

- ユーザー認証・権限管理（現状は単一環境・単一テナント想定）
- YouTubeアカウント連携、チャンネル管理、プレイリスト処理
- 長期の履歴検索/全文検索UI、分析ダッシュボード
- 多言語（日本語/英語以外）のUI対応（音声認識APIが対応しても、プロダクトとして保証しない）

## ドメインモデル（永続化対象）

本プロダクトは「ジョブ」中心の状態管理を行う。

- Job

  - 入力: `youtube_url`, `language`, `model`
  - 状態: `status`, `progress`, `error_message`
- AudioFile

  - 音声抽出の成果物とメタ情報（タイトル、長さ、形式、サイズ）
- Transcript

  - 文字起こし本文とメタ情報（検出言語、使用モデル）
- CorrectedTranscript

  - 校正文、元文、モデル、差分サマリ
- QaResult

  - 質問、回答、モデル、作成日時（同一ジョブに対して複数件が追記される）

## 状態モデル（Job Status）

Jobの状態はDB制約として以下のいずれかに限定する。

- `pending`: ジョブ作成直後
- `processing`: 音声抽出など前処理
- `transcribing`: 文字起こし中
- `correcting`: 校正中（/correct, /proofread を含む）
- `completed`: 完了（文字起こしが完了した状態、校正が走っても最終的にここへ戻る）
- `failed`: 失敗（`error_message` に理由）

補足:
- Q&A はジョブ状態を変更しない（結果が `qa_results` として追加される）。

## 機能一覧（現コードに基づく網羅）

### 1) YouTube URL から文字起こしジョブを作成

- API: `POST /api/jobs/transcribe`

  - 入力: `youtube_url`, `language`（`ja`/`en`）, `model`（`gpt-4o-mini-transcribe`/`gpt-4o-transcribe`）
  - 出力: `job_id`, `status`, `message`
- 非同期: キューへ `worker.transcription_task` を投入

### 2) ジョブの進捗/状態確認

- API: `GET /api/jobs/{job_id}/status`

  - 出力: `status`, `progress`, `error_message`, `youtube_url`, `language`, `model`, `created_at`, `updated_at`

### 3) ジョブ結果の取得（統合ビュー）

- API: `GET /api/jobs/{job_id}/result`

  - `audio_file`（存在すれば）
  - `transcript`（存在すれば）
  - `corrected_transcript`（存在すれば）
  - `qa_results`（存在すれば、配列で返却）

### 4) 文字起こしテキストのLLM校正（任意）

校正は「Correct」と「Proofread」の2つの入口を持つが、いずれも `CorrectedTranscript` を更新する。

- API: `POST /api/jobs/{job_id}/correct`

  - 入力: `correction_model`（`gpt-4o-mini`/`gpt-4o`）
  - 非同期: `worker.correction_task` を投入
- API: `POST /api/jobs/{job_id}/proofread`

  - 入力: `proofread_model`（`gpt-4o-mini`/`gpt-4o`）
  - 非同期: `worker.proofread_task` を投入

### 5) Q&A（任意）

- API: `POST /api/jobs/{job_id}/qa`

  - 入力: `question`（必須）, `qa_model`（`gpt-4o-mini`/`gpt-4o`）
  - 非同期: `worker.qa_task` を投入
- 結果: `GET /api/jobs/{job_id}/result` の `qa_results` に履歴が追加される
- 基本文書: `CorrectedTranscript` が存在すればその本文を優先し、なければ `Transcript` を使用する

### 6) エクスポート（TXT/SRT/VTT）

- API: `GET /api/jobs/{job_id}/export?format=txt|srt|vtt`

  - `format` が不正なら 400
  - `status != completed` なら 400
  - 校正文があれば校正文を、なければ元の文字起こしをエクスポートに使用
  - SRT/VTT 用の `segments` はオリジナル transcript 側（`transcripts.segments_json`）から読み込む
  - `Content-Disposition` でファイルダウンロードを返す（ASCII安全な `filename` とUTF-8の `filename*` を併用）

## 既知の重要な品質課題と方針

### 長時間音声で「末尾が欠落する」リスク

- サイズが 25MB 未満でも、長時間音声を1リクエストで文字起こしすると末尾が途中で切れるケースがある
- そのため、`MAX_SINGLE_CHUNK_SEC`（デフォルト 900 秒）を超える音声は分割して複数チャンクで処理する（安定性優先）

### 7) ヘルスチェック/メタ

- API: `GET /health`（DB/Redisの疎通を返す）
- API: `GET /`（サービス情報）
- FastAPIの `/docs`（自動生成）

### 8) Web UI（Next.js）

- URL入力→ジョブ作成→進捗表示→結果表示（Original/Proofread/QA タブ）→エクスポート
- Proofread は「手動実行」可能で、さらに「文字起こし完了かつ校正結果なし」の場合に自動実行（UI側）する
- QA は質問入力→送信→履歴表示（ジョブごとに複数件）

## 品質・運用上の重要事項

- 外部依存:

  - 音声抽出: yt-dlp
  - 文字起こし/校正/Q&A: OpenAI API（`OPENAI_API_KEY` が必須）
- 制限:

  - 動画時間制限: **制限なし**（デフォルト）
    - 環境変数 `MAX_VIDEO_DURATION_SECONDS` で制御可能（0=無制限、秒単位で指定）
  - 音声ファイルのサイズ上限: 25MB上限チェック（超過時は自動圧縮/分割）
- 可観測性:

  - API/Worker ともにログ出力を行う（APIはJSON形式のログ設定）

