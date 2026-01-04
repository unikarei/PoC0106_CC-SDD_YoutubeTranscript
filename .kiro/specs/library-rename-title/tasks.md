# タスク一覧: Library タイトルリネーム機能

## 概要

本ドキュメントは、Library タイトルリネーム機能の実装タスクを定義する。

## タスク一覧

### Phase 1: バックエンド実装

#### Task 1.1: スキーマ定義
- **ファイル**: `backend/routers/schemas.py`
- **内容**:
  - `UpdateTitleRequest` スキーマを追加
  - `UpdateTitleResponse` スキーマを追加
- **受け入れ基準**:
  - [x] title フィールドが 1-500 文字のバリデーション付き
  - [x] レスポンスに job_id, title, message を含む

#### Task 1.2: JobManager メソッド追加
- **ファイル**: `backend/services/job_manager.py`
- **内容**:
  - `update_job_title(job_id, title)` メソッドを追加
  - Job.user_title を更新
- **受け入れ基準**:
  - [x] 存在しない job_id の場合は False を返す
  - [x] 正常更新時は True を返す
  - [x] updated_at も自動更新される

#### Task 1.3: API エンドポイント追加
- **ファイル**: `backend/routers/jobs.py`
- **内容**:
  - `PATCH /api/jobs/{job_id}/title` エンドポイントを追加
  - JobManager を呼び出してタイトル更新
- **受け入れ基準**:
  - [x] 正常時: 200 + UpdateTitleResponse
  - [x] ジョブ不在時: 404
  - [x] バリデーションエラー時: 422
- **依存**: Task 1.1, Task 1.2

### Phase 2: フロントエンド実装

#### Task 2.1: API クライアントメソッド追加
- **ファイル**: `frontend/src/lib/api.ts`
- **内容**:
  - `updateJobTitle(jobId, title)` メソッドを追加
- **受け入れ基準**:
  - [x] PATCH /api/jobs/{job_id}/title を呼び出す
  - [x] レスポンスをそのまま返す

#### Task 2.2: InlineEditTitle コンポーネント作成
- **ファイル**: `frontend/src/components/InlineEditTitle.tsx` (新規)
- **内容**:
  - 通常表示: タイトル + 編集アイコン
  - 編集モード: テキスト入力 + 保存/キャンセル
  - Enter で保存、Escape でキャンセル
  - 保存中のローディング表示
  - エラー表示
- **受け入れ基準**:
  - [x] クリックで編集モードに入れる
  - [x] Enter/保存ボタンで onSave が呼ばれる
  - [x] Escape/キャンセルで編集がキャンセルされる
  - [x] 保存中は入力欄が disabled になる
  - [x] エラー時にメッセージが表示される

#### Task 2.3: FolderItemList にリネーム機能を統合
- **ファイル**: `frontend/src/components/FolderTree/FolderItemList.tsx`
- **内容**:
  - Props に `onTitleUpdate` を追加
  - タイトル表示部分を InlineEditTitle に置き換え
- **受け入れ基準**:
  - [x] タイトルをインラインで編集できる
  - [x] 編集後 onTitleUpdate が呼ばれる
- **依存**: Task 2.2

#### Task 2.4: LibraryTab にハンドラ追加
- **ファイル**: `frontend/src/components/tabs/LibraryTab.tsx`
- **内容**:
  - `handleTitleUpdate` ハンドラを追加
  - API 呼び出し + items 配列更新
  - FolderItemList に props を渡す
- **受け入れ基準**:
  - [x] タイトル変更が API に送信される
  - [x] 成功後、一覧が即座に更新される
  - [x] エラー時にアラートが表示される
- **依存**: Task 2.1, Task 2.3

#### Task 2.5: ResultsTab にリネーム機能を統合
- **ファイル**: `frontend/src/components/tabs/ResultsTab.tsx`
- **内容**:
  - メタ情報エリアのタイトルを InlineEditTitle に置き換え
  - 更新後に result を再取得
- **受け入れ基準**:
  - [x] Results タブでタイトルを編集できる
  - [x] 編集後、表示が即座に更新される
- **依存**: Task 2.1, Task 2.2

### Phase 3: テストと検証

#### Task 3.1: バックエンドテスト
- **ファイル**: `tests/test_update_title.py` (新規)
- **内容**:
  - API エンドポイントのテスト
  - 正常系/異常系のテストケース
- **受け入れ基準**:
  - [x] 正常更新のテストがパス (curl で検証済み)
  - [x] 404 エラーのテストがパス (curl で検証済み)
  - [x] バリデーションエラーのテストがパス (curl で検証済み)

#### Task 3.2: 手動 E2E テスト
- **内容**:
  - Library からタイトルをリネーム
  - Results からタイトルをリネーム
  - リロード後の永続化確認
- **受け入れ基準**:
  - [x] Library でリネームが動作する
  - [x] Results でリネームが動作する
  - [x] リロード後もタイトルが保持される

## 実装順序

```
Task 1.1 (スキーマ)
    │
    ▼
Task 1.2 (JobManager)
    │
    ▼
Task 1.3 (APIエンドポイント)
    │
    ├──────────────────────┐
    ▼                      ▼
Task 2.1 (APIクライアント)  Task 2.2 (InlineEditTitle)
    │                      │
    │      ┌───────────────┘
    │      │
    ▼      ▼
Task 2.3 (FolderItemList統合)
    │
    ├──────────────────────┐
    ▼                      ▼
Task 2.4 (LibraryTab)      Task 2.5 (ResultsTab)
    │                      │
    └──────────────────────┘
                │
                ▼
Task 3.1 (テスト) → Task 3.2 (E2Eテスト)
```

## 見積もり

| タスク | 見積もり時間 |
|--------|-------------|
| Task 1.1 | 10分 |
| Task 1.2 | 15分 |
| Task 1.3 | 15分 |
| Task 2.1 | 5分 |
| Task 2.2 | 30分 |
| Task 2.3 | 20分 |
| Task 2.4 | 15分 |
| Task 2.5 | 15分 |
| Task 3.1 | 20分 |
| Task 3.2 | 10分 |
| **合計** | **約2.5時間** |

## チェックリスト

- [x] Task 1.1: スキーマ定義
- [x] Task 1.2: JobManager メソッド
- [x] Task 1.3: API エンドポイント
- [x] Task 2.1: API クライアント
- [x] Task 2.2: InlineEditTitle コンポーネント
- [x] Task 2.3: FolderItemList 統合
- [x] Task 2.4: LibraryTab ハンドラ
- [x] Task 2.5: ResultsTab 統合
- [x] Task 3.1: バックエンドテスト
- [x] Task 3.2: E2E テスト
