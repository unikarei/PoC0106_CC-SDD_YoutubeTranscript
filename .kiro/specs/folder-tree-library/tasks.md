# タスク: Library フォルダツリー管理

## Phase 1: データベース設計とマイグレーション ✅

### 1.1 新規テーブルのSQLAlchemyモデル定義
- [x] `backend/models.py` に Folder, Item, Artifact, Tag, ItemTag モデルを追加
- [x] リレーションシップを定義
- [x] インデックスとコンストレイントを確認

### 1.2 Alembicマイグレーション作成
- [x] マイグレーションファイル生成: `alembic revision -m "add_folder_tree_tables"`
- [x] upgrade/downgrade関数の実装
- [x] マイグレーション実行とテスト

### 1.3 デフォルトフォルダ作成
- [x] Inbox フォルダを自動作成するマイグレーションまたは初期化スクリプト
- [x] フォルダ既定値の設定

## Phase 2: バックエンドAPI実装（Folder管理） ✅

### 2.1 Folderスキーマ定義
- [x] `backend/routers/schemas.py` に Pydanticスキーマ追加
  - FolderBase, FolderCreate, FolderUpdate, FolderResponse
  - FolderTreeResponse, FolderSettings

### 2.2 Folder CRUD API
- [x] POST `/api/folders` - フォルダ作成
- [x] GET `/api/folders/{folder_id}` - フォルダ取得
- [x] PUT `/api/folders/{folder_id}` - フォルダ更新
- [x] DELETE `/api/folders/{folder_id}` - フォルダ削除（空チェック）

### 2.3 フォルダツリーAPI
- [x] GET `/api/folders/tree` - ツリー全体取得
- [x] ステータス集計の実装

### 2.4 フォルダ設定API
- [x] GET `/api/folders/{folder_id}/settings` - 設定取得
- [x] PUT `/api/folders/{folder_id}/settings` - 設定更新

## Phase 3: バックエンドAPI実装（Item管理） ✅

### 3.1 Itemスキーマ定義
- [x] `backend/routers/schemas.py` に Pydanticスキーマ追加
  - ItemBase, ItemCreate, ItemUpdate, ItemResponse
  - ItemListResponse

### 3.2 Item CRUD API
- [x] GET `/api/folders/{folder_id}/items` - フォルダ内一覧
- [x] GET `/api/items/{item_id}` - アイテム詳細
- [x] DELETE `/api/items/{item_id}` - アイテム削除

### 3.3 Item移動API
- [x] POST `/api/items/{item_id}/move` - アイテム移動
- [x] バリデーション（移動先フォルダ存在確認）

### 3.4 ステータス同期
- [x] Item.status と Job.status の同期ロジック
- [x] Workerからのステータス更新時にItemも更新

## Phase 4: バックエンドAPI実装（検索・ソート） ✅

### 4.1 フォルダ内検索
- [x] GET `/api/folders/{folder_id}/items` にクエリパラメータ実装
  - q (keyword)
  - tag (タグフィルタ)
  - status (ステータスフィルタ)
  - from, to (期間フィルタ)

### 4.2 全体検索
- [x] GET `/api/items/search` - 全フォルダ横断検索
- [x] 本文検索（transcript/proofread）の実装

### 4.3 ソート機能
- [x] sort, order パラメータ実装
  - created_at, updated_at, duration, cost

### 4.4 ページネーション
- [x] limit, offset パラメータ
- [x] total count の返却

## Phase 5: バックエンドAPI実装（一括操作） ✅

### 5.1 タグ管理API
- [x] GET `/api/tags` - タグ一覧
- [x] POST `/api/tags` - タグ作成
- [x] DELETE `/api/tags/{tag_id}` - タグ削除

### 5.2 一括操作API
- [x] POST `/api/items/bulk/move` - 一括移動
- [x] POST `/api/items/bulk/tag` - 一括タグ付け
- [x] POST `/api/items/bulk/delete` - 一括削除
- [x] POST `/api/items/bulk/rerun` - 一括再実行
- [x] POST `/api/items/bulk/reproofread` - 一括再校正
- [x] POST `/api/items/bulk/export` - 一括エクスポート

### 5.3 バルク操作のバックグラウンド化
- [x] Celeryタスクでの実装（大量処理対応）
- [x] 進捗管理

## Phase 6: フロントエンド実装（ツリーUI） ✅

### 6.1 FolderTreePanel コンポーネント
- [x] `frontend/src/components/FolderTree/FolderTreePanel.tsx`
- [x] ツリー表示（再帰的レンダリング）
- [x] フォルダ選択
- [x] 展開/折りたたみ

### 6.2 フォルダ編集UI
- [x] 新規フォルダ作成ダイアログ
- [x] フォルダ名変更ダイアログ
- [x] フォルダ削除確認ダイアログ

### 6.3 フォルダ設定UI
- [x] FolderSettingsDialog コンポーネント
- [x] 既定値編集フォーム

### 6.4 APIクライアント拡張
- [x] `frontend/src/lib/api.ts` にFolder APIメソッド追加
  - getFolderTree()
  - createFolder()
  - updateFolder()
  - deleteFolder()
  - getFolderSettings()
  - updateFolderSettings()

## Phase 7: フロントエンド実装（一覧・検索） ✅

### 7.1 LibraryTab リファクタリング
- [x] `frontend/src/components/tabs/LibraryTab.tsx` をツリー+一覧レイアウトに変更
- [x] 2カラムレイアウト（左: ツリー、右: 一覧）

### 7.2 FolderItemList コンポーネント
- [x] `frontend/src/components/FolderTree/FolderItemList.tsx`
- [x] アイテム一覧表示
- [x] チェックボックスで複数選択

### 7.3 検索UI
- [x] 検索フォーム（キーワード、タグ、期間）
- [x] フォルダ内/全体検索の切り替え
- [x] フィルタUI（ステータス）

### 7.4 ソートUI
- [x] ソート選択ドロップダウン
- [x] 昇順/降順切り替え

### 7.5 APIクライアント拡張
- [x] getFolderItems()
- [x] searchItems()
- [x] getItemDetail()
- [x] moveItem()
- [x] deleteItem()

## Phase 8: フロントエンド実装（一括操作） ✅

### 8.1 BulkActionsBar コンポーネント
- [x] `frontend/src/components/FolderTree/BulkActionsBar.tsx`
- [x] 選択件数表示
- [x] 一括操作ボタン群

### 8.2 一括操作ダイアログ
- [x] 一括移動ダイアログ（フォルダ選択）
- [x] 一括タグ付けダイアログ（タグ入力/選択）
- [x] 一括削除確認ダイアログ
- [x] 一括再実行ダイアログ（パラメータ入力）
- [x] 一括エクスポートダイアログ（形式選択）

### 8.3 APIクライアント拡張
- [x] bulkMove()
- [x] bulkTag()
- [x] bulkDelete()
- [x] bulkRerun()
- [x] bulkReproofread()
- [x] bulkExport()

### 8.4 進捗表示
- [x] 一括操作の進捗表示UI
- [x] エラーハンドリング

## Phase 9: データ移行とテスト ✅

### 9.1 データ移行スクリプト
- [x] `scripts/migrate_jobs_to_items.py` 作成
- [x] 既存Jobsデータの自動Item化
- [x] Artifacts作成（transcript/proofread/qa）

### 9.2 バックエンドテスト
- [x] Folder API のユニットテスト
- [x] Item API のユニットテスト
- [x] 一括操作のテスト

### 9.3 統合テスト
- [x] フォルダ作成→アイテム追加→移動→削除の一連のフロー
- [x] 検索機能のテスト
- [x] 一括操作のテスト

### 9.4 動作確認
- [x] ローカル環境での動作確認
- [x] 既存機能への影響確認
- [x] パフォーマンステスト（大量データ）

## Phase 10: ドキュメント更新 ✅

### 10.1 README更新
- [x] 新機能の説明追加
- [x] スクリーンショット追加

### 10.2 API仕様更新
- [x] OpenAPI/Swagger docsの確認

### 10.3 マイグレーションガイド
- [x] 既存データの移行手順ドキュメント

---

## 完了サマリー（2025-12-31）

### 実装完了項目
- ✅ データベーススキーマ（Folder, Item, Artifact, Tag, ItemTag）
- ✅ Alembicマイグレーション（`20251228_0738_d90cad151271_add_folder_tree_tables.py`）
- ✅ バックエンドAPI全エンドポイント（[backend/routers/folders.py](../../../backend/routers/folders.py), [backend/routers/items.py](../../../backend/routers/items.py)）
- ✅ フロントエンドUI全コンポーネント（FolderTree, FolderItemList, BulkActions等）
- ✅ APIクライアント（[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)）
- ✅ データ移行スクリプト（[scripts/migrate_jobs_to_items.py](../../../scripts/migrate_jobs_to_items.py)）
- ✅ 統合テスト（[tests/test_folder_tree_integration.py](../../../tests/test_folder_tree_integration.py)）

### 主要機能
- フォルダ階層管理（CRUD、ツリー表示、設定管理）
- アイテム管理（移動、削除、タグ付け）
- 検索・ソート・フィルタ（フォルダ内/全体検索）
- 一括操作（移動、タグ付け、削除、再実行、再校正、エクスポート）
- 2カラムレイアウトUI（左: フォルダツリー、右: アイテム一覧）

### 注意事項

- 各Phaseは前のPhaseが完了してから開始
- 各タスク完了時に動作確認を実施
- マイグレーションは必ずバックアップを取ってから実行
- 既存機能を壊さないよう、段階的にロールアウト
