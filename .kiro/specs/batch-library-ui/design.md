# 設計: Batch / Results / Library / Settings UI

## 方針
- UIは4タブで責務を分離する
  - Batch: 投入と進捗（詳細は見ない）
  - Results: 1件を深く見る
  - Library: 探す
  - Settings: 既定値
- 既存のバックエンド（FastAPI + Celery）とDBスキーマを最大限再利用し、必要な最小のAPI追加で成立させる


## 画面/コンポーネント設計（Next.js）

### グローバル構成
- 画面上部にTabs
- 各タブは同一ページ内の表示切替（最小）またはルーティング（`/batch`, `/results`, `/library`, `/settings`）のいずれか
  - 最小実装は「単一ページ + タブ切替」を採用
  - Resultsだけは `job_id` をURLに載せる（再読込で復元できる）

### 状態管理
- `Settings` はブラウザLocalStorageへ永続化し、各タブで参照
- `Batch Queue` はフロント側のキュー状態（投入対象と対応job_id）を保持し、一定間隔で status/result をポーリング
- `Library` はバックエンド検索APIの結果をそのまま表示


## バックエンドAPI設計

### 既存API（再利用）
- `POST /api/jobs/transcribe`
- `GET /api/jobs/{job_id}/status`
- `GET /api/jobs/{job_id}/result`
- `POST /api/jobs/{job_id}/proofread`
- `POST /api/jobs/{job_id}/qa`
- `GET /api/jobs/{job_id}/export`

### 追加API（最小）

#### 1) ジョブ一覧/検索（Library用）
- `GET /api/jobs`
  - query params（最小）:
    - `q`（キーワード）
    - `tag`（タグ）
    - `from` / `to`（期間）
    - `language`
    - `model`
    - `min_duration` / `max_duration`
    - `has_qa`（bool）
    - `limit` / `offset`
  - response:
    - `items: [...]`
    - `total`

検索対象（最小）:
- タイトル（AudioFile.title もしくはユーザー指定タイトル）
- URL（Job.youtube_url）
- Transcript.text（段階導入。初期実装は title/url のみに限定してよい）


#### 2) プレイリスト/チャンネル展開（Batch C用）
- `POST /api/jobs/expand`
  - request:
    - `url`（playlist または channel のURL）
  - response:
    - `items: [{ youtube_url, title? }]`

実装案:
- サーバ側で `yt-dlp` を `--flat-playlist` 相当で実行し、個別動画URLとtitleを抽出
- 失敗時は 400（不正URL）または 500（処理失敗）


#### 3) ジョブ削除（Library用）
- 単体削除: `DELETE /api/jobs/{job_id}`
  - DB上の Job と関連レコード（AudioFile/Transcript/CorrectedTranscript/QaResult）を削除
  - `audio_files/` 配下の成果物もベストエフォートで削除
  - 処理中ジョブの誤削除防止のため、in progress は 409 を返して拒否する
- 一括削除: `POST /api/jobs/bulk-delete`
  - request: `{ job_ids: string[] }`
  - response: per-job の削除成否（not_found / in_progress / db_error など）


## DB/モデル設計

### 現状の永続化
- Job / AudioFile / Transcript / CorrectedTranscript / QaResult は既にDBに保存される

### 追加が必要なフィールド（タグ/ユーザー指定タイトル）
要件の「CSV貼り付け（url,title,tag…）」「タグで検索」「Resultsにタグ表示」を満たすため、以下を追加する。
- `jobs.user_title`（任意、TEXT）
- `jobs.tags`（任意、TEXT もしくは JSON配列）

タグ入力/保存の方針（今回の合意）:
- UI入力は `;` 区切り
- DB保存は初期実装ではTEXTでよい（将来JSON化は検討）

検索/表示優先順位:
- title: `jobs.user_title` があれば優先し、なければ `audio_files.title`


## 主要フロー

### Batch A/B投入
1. 入力をパースしてURL配列へ
2. 共通設定を適用
3. 逐次 `POST /api/jobs/transcribe` を呼び出し job_id を得る
4. Queueに行を追加し、`GET /status` をポーリング
5. 行クリックで `GET /result` を取得してプレビュー表示

### Batch C（展開）
1. `POST /api/jobs/expand` で動画URL一覧を取得
2. 取得した一覧を投入対象として表示
3. RunでA/B同様に投入

### Library → Results
1. Libraryで `GET /api/jobs` を呼ぶ
2. 一覧からジョブを選ぶ
3. Resultsへ job_id を渡して表示


## エラーハンドリング/UX
- Batch投入中に個別URLが失敗しても全体は継続し、該当行にエラーを表示
- 進捗ポーリングは指数バックオフまたは最大頻度制限を入れる
- ResultsのRe-runは「新しいジョブ作成」扱い（履歴として残す）を基本とする

### Results（Proofread/QA）の非同期反映
- Proofread/QAはバックエンドで非同期にDBへ反映される
- UIは「ボタン押下→一定時間ポーリング→反映された瞬間に表示更新」を採用し、タブ切替なしで結果が見えるようにする
- QAは「直前の質問の回答が次回表示される」ズレを避けるため、送信したquestionが履歴に現れるまで待つ


## セキュリティ/運用
- Playlist/Channel展開はサーバ側で外部コマンド実行となるため、URLバリデーションとタイムアウトを必須
- APIは現状通り認証なし前提（非ゴール）
