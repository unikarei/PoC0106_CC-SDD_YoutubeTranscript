# Batch/Library UI 実装サマリー

実装完了日: 2025-12-28

## 実装内容

### 1. バックエンド（Backend API）

#### データベース拡張
- ✅ `jobs.user_title` カラム追加（Alembic migration: 20251225_001）
- ✅ `jobs.tags` カラム追加（セミコロン区切り）

#### API エンドポイント
- ✅ `POST /api/jobs/transcribe` - `user_title`, `tags` パラメータ対応
- ✅ `GET /api/jobs/` - ジョブ一覧・検索API
  - フィルタ: keyword, tag, 期間, 言語, モデル, QA有無
  - ページネーション: limit/offset
- ✅ `POST /api/jobs/expand` - プレイリスト/チャンネル展開API
  - yt-dlp による URL 展開
  - タイムアウト・エラーハンドリング
- ✅ `DELETE /api/jobs/{job_id}` - 単一ジョブ削除
  - 処理中ジョブは409エラーで拒否
  - audio_files 配下のファイルも削除（best-effort）
- ✅ `POST /api/jobs/bulk-delete` - 一括削除
  - 各ジョブの削除結果を返却
  - 処理中ジョブはスキップ

#### ファイル
- [backend/routers/jobs.py](../../../backend/routers/jobs.py)
- [backend/routers/schemas.py](../../../backend/routers/schemas.py)
- [backend/services/playlist_expander.py](../../../backend/services/playlist_expander.py)
- [alembic/versions/20251225_001_add_job_title_and_tags.py](../../../alembic/versions/20251225_001_add_job_title_and_tags.py)

### 2. フロントエンド（React/Next.js）

#### UI構造
- ✅ 4タブUI実装
  - **Batch**: 一括投入
  - **Results**: 詳細結果表示
  - **Library**: 過去結果検索
  - **Settings**: デフォルト設定

#### Batch タブ
- ✅ 入力モード3種類
  - モードA: URLリスト（複数行）
  - モードB: CSV形式（url,title,tags）
  - モードC: プレイリスト/チャンネル展開
- ✅ Queue管理
  - 状態・進捗・エラー表示
  - 行クリックでプレビュー表示
  - 自動ポーリング（3秒ごと）

#### Results タブ
- ✅ job_id 指定で結果取得
- ✅ サブタブ（Transcript / Proofread / QA）
- ✅ 右上アクション（Export, Re-run）
- ✅ QA入力欄のレイアウト調整
- ✅ Proofread/QA実行後の結果ポーリング

#### Library タブ
- ✅ フィルタUI
  - キーワード, タグ, 期間, 言語, モデル, QA有無
- ✅ 検索結果一覧
  - チェックボックスで複数選択
  - 行クリックでResultsへ遷移
- ✅ 削除機能
  - 単体削除（行ごと）
  - 一括削除（選択したN件）
  - confirm ダイアログで確認
  - 削除後はリスト即時更新

#### Settings タブ
- ✅ デフォルト値設定
  - 言語, モデル, 分割閾値
  - Proofread/QA 有効化
  - 自動保存ポリシー
- ✅ LocalStorage 保存/復元

#### ファイル
- [frontend/src/app/page.tsx](../../../frontend/src/app/page.tsx) - メインページ
- [frontend/src/components/tabs/BatchTab.tsx](../../../frontend/src/components/tabs/BatchTab.tsx)
- [frontend/src/components/tabs/ResultsTab.tsx](../../../frontend/src/components/tabs/ResultsTab.tsx)
- [frontend/src/components/tabs/LibraryTab.tsx](../../../frontend/src/components/tabs/LibraryTab.tsx)
- [frontend/src/components/tabs/SettingsTab.tsx](../../../frontend/src/components/tabs/SettingsTab.tsx)
- [frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts) - API Client
- [frontend/src/lib/settings.ts](../../../frontend/src/lib/settings.ts) - Settings管理

### 3. テスト

#### 既存テスト
- [tests/test_jobs_list_api.py](../../../tests/test_jobs_list_api.py) - ジョブ一覧API
- [tests/test_playlist_expander.py](../../../tests/test_playlist_expander.py) - プレイリスト展開

#### 注意
- Unit testの一部でSQLAlchemyのセットアップに関する調整が必要な状況
- 実機での動作確認を推奨

## 動作確認手順

### 1. バックエンド起動
```bash
docker compose up -d
# または
./start_app.sh
```

### 2. マイグレーション確認
```bash
docker compose exec api alembic current
```
`20251225_001_add_job_title_and_tags` が適用されていることを確認

### 3. フロントエンド起動
```bash
cd frontend
npm install
npm run dev
```

### 4. 動作確認
1. http://localhost:3000 にアクセス
2. Settings タブでデフォルト値を設定
3. Batch タブで複数URL投入
   - モードCでプレイリスト展開も試す
4. Library タブで検索・削除を確認
5. Results タブで詳細確認

## 既知の制限事項

- yt-dlpが必須（プレイリスト展開時）
- 処理中ジョブは削除不可（409エラー）
- CSVパース: quoted commaには未対応（簡易実装）
- テストの一部が要調整

## 今後の改善案

- CSVアップロード対応（ファイル選択UI）
- バッチ処理の優先度制御
- より詳細なフィルタ条件（duration範囲など）
- エクスポート形式の追加（JSON, MD）
- 削除時の詳細確認ダイアログ

## 関連ドキュメント

- [requirements.md](./requirements.md)
- [design.md](./design.md)
- [tasks.md](./tasks.md)
