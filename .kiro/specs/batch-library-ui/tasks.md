# タスク: Batch / Results / Library / Settings UI

## 0. 事前確認
- 既存のUIコンポーネント（Tab相当）とスタイル規約を確認し、追加が最小になる構成を選ぶ
- 既存APIのレスポンス構造（job result/status）を前提に画面設計を確定

## 1. バックエンド（API/DB）
1. `jobs.user_title` と `jobs.tags` を追加するAlembicマイグレーションを作成
2. `POST /api/jobs/transcribe` がユーザー指定title/tagsを受け取れるように拡張（後方互換）
3. `GET /api/jobs`（一覧/検索）を追加
   - 最小: title/url/期間/言語/モデル/QAあり + limit/offset
   - 可能なら: duration条件
4. `POST /api/jobs/expand`（playlist/channel展開）を追加
   - yt-dlp 実行
   - URLバリデーション/タイムアウト
5. 追加APIのスキーマ（Pydantic）を定義し、OpenAPI docsで確認

## 2. フロントエンド（4タブUI）
1. Tabsの骨格（Batch/Results/Library/Settings）を実装
2. Settings
   - デフォルト値の入力UI
   - LocalStorage保存/復元
3. Batch
   - 入力モードA/B/Cのトグル
   - A: 複数行URLパース
   - B: CSVパース（url,title,tag…）
   - C: expand API呼び出し→投入対象生成
   - Run: URLごとに createJob を呼んでQueueへ追加
   - Queueテーブル表示（status/progress/error/retry）
   - 行クリックでプレビュー表示（resultのサマリ）
4. Results
   - job_id を指定して result を取得
   - サブタブ（Transcript/Proofread/QA）
   - 右上アクション（Export, Re-run）
   - Save to DB: 自動保存ONのときは Saved 表示のみ
5. Library
   - フィルタUI
   - 検索API呼び出し
   - 結果リスト表示→クリックでResultsに遷移

## 2.5 追加（削除機能: Library）
1. バックエンド
   - `DELETE /api/jobs/{job_id}` を追加（処理中は409で拒否）
   - `POST /api/jobs/bulk-delete` を追加（per-job結果を返す）
   - `audio_files/` 配下の成果物削除もベストエフォートで実施
2. フロントエンド
   - Libraryの検索結果にチェックボックスを追加し複数選択可能にする
   - 行ごとに「削除」ボタン（単体削除）
   - 「選択を削除 (N)」ボタン（一括削除）
   - confirmで最小限の確認を入れる
   - 削除成功時は、リスト/選択状態を即時に更新してGUIから消す（必要ならbest-effortで再検索）

## 2.6 追加（UX修正: Results）
- QA入力欄が狭くならないようにレイアウト調整（モデルselectの幅制御）
- Proofread/QA実行後、結果がDBに反映されるまでポーリングし、タブ切替なしで結果を表示

## 3. テスト/検証
1. バックエンド
   - `GET /api/jobs` のフィルタが動くこと
   - `POST /api/jobs/expand` の正常系/異常系
2. フロントエンド
   - Batch A/Bパース（単体テスト or 最小の関数テスト）
   - Tabs遷移とResults表示

## 4. ドキュメント
- README または `.kiro/steering` に「過去結果の参照がLibraryで可能」な前提を追記

