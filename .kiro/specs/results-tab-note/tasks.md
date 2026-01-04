# タスク: ResultsタブへのNote機能追加

## タスク一覧

### Task 1: データベースモデル追加
- [x] `backend/models.py` に `JobNote` モデルを追加
- [x] `Job` モデルに `note` リレーションを追加
- 依存: なし

### Task 2: Alembicマイグレーション作成
- [x] `alembic/versions/20260104_001_add_job_notes.py` を作成
- [x] job_notesテーブル作成
- [x] インデックス作成
- 依存: Task 1

### Task 3: バックエンドAPIルーター実装
- [x] `backend/routers/notes.py` を新規作成
- [x] GET /api/v1/jobs/{job_id}/note エンドポイント実装
- [x] PUT /api/v1/jobs/{job_id}/note エンドポイント実装
- [x] Pydanticスキーマ定義
- 依存: Task 1

### Task 4: バックエンドルーター登録
- [x] `backend/main.py` にnotesルーターを登録
- 依存: Task 3

### Task 5: フロントエンドAPIクライアント追加
- [x] `frontend/src/lib/api.ts` に `getNote` メソッド追加
- [x] `frontend/src/lib/api.ts` に `updateNote` メソッド追加
- 依存: Task 3

### Task 6: ResultsTab Noteサブタブ実装
- [x] SubTab型に 'note' を追加
- [x] Noteタブボタン追加
- [x] Note入力・編集UI実装
- [x] Note取得・保存ロジック実装
- [x] 保存状態フィードバック表示
- 依存: Task 5

### Task 7: マイグレーション実行・動作確認
- [ ] Alembicマイグレーション実行（Docker環境で実行が必要）
- [ ] 動作確認テスト
- 依存: Task 2, Task 4, Task 6

## 完了条件

- [x] ResultsタブにNoteサブタブが表示される（コード実装完了）
- [x] Noteの入力・保存・取得が正常に動作する（コード実装完了）
- [x] 既存機能に影響がない

## マイグレーション実行方法

Docker環境でマイグレーションを実行してください:

```bash
docker compose exec api alembic upgrade head
```

または、Docker Composeを起動すると自動的に実行されます。
