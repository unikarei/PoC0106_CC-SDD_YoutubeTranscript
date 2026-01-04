# 設計書: Library タイトルリネーム機能

## 概要

本設計書は、Library タブおよび Results タブから文字起こし結果のタイトルをリネームする機能の技術設計を定義する。

## アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Frontend                                   │
├─────────────────────────────────────────────────────────────────────┤
│  LibraryTab.tsx                  ResultsTab.tsx                      │
│       │                               │                              │
│       ▼                               ▼                              │
│  FolderItemList.tsx           (メタ情報エリア)                        │
│  - インライン編集UI             - インライン編集UI                     │
│       │                               │                              │
│       └──────────────┬───────────────┘                              │
│                      ▼                                               │
│               api.ts (updateJobTitle)                                │
└──────────────────────────────────────────────────────────────────────┘
                       │
                       ▼ PATCH /api/jobs/{job_id}/title
┌─────────────────────────────────────────────────────────────────────┐
│                           Backend                                    │
├─────────────────────────────────────────────────────────────────────┤
│  routers/jobs.py                                                     │
│  - update_job_title() エンドポイント                                  │
│       │                                                              │
│       ▼                                                              │
│  services/job_manager.py                                             │
│  - update_job_title(job_id, title) メソッド                          │
│       │                                                              │
│       ▼                                                              │
│  models.py (Job.user_title カラム更新)                               │
└──────────────────────────────────────────────────────────────────────┘
```

## コンポーネント設計

### 1. バックエンド API

#### 1.1 エンドポイント定義

**ファイル**: `backend/routers/jobs.py`

```python
@router.patch("/{job_id}/title", response_model=UpdateTitleResponse)
async def update_job_title(
    job_id: str,
    request: UpdateTitleRequest,
    db: Annotated[Session, Depends(get_db)]
):
    """ジョブのタイトルを更新する"""
```

#### 1.2 リクエスト/レスポンススキーマ

**ファイル**: `backend/routers/schemas.py`

```python
class UpdateTitleRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500, description="New title")

class UpdateTitleResponse(BaseModel):
    job_id: str
    title: str
    message: str
```

#### 1.3 JobManager メソッド

**ファイル**: `backend/services/job_manager.py`

```python
def update_job_title(self, job_id: str, title: str) -> bool:
    """
    ジョブのタイトル (user_title) を更新する
    
    Args:
        job_id: ジョブID
        title: 新しいタイトル
        
    Returns:
        True if successful, False otherwise
    """
```

### 2. フロントエンド

#### 2.1 API クライアント

**ファイル**: `frontend/src/lib/api.ts`

```typescript
// Update job title
async updateJobTitle(jobId: string, title: string) {
  const response = await this.client.patch(`/api/jobs/${jobId}/title`, {
    title,
  })
  return response.data
}
```

#### 2.2 インライン編集コンポーネント

**新規ファイル**: `frontend/src/components/common/InlineEditTitle.tsx`

```typescript
type Props = {
  value: string
  onSave: (newValue: string) => Promise<void>
  placeholder?: string
  className?: string
}

export default function InlineEditTitle({ value, onSave, placeholder, className }: Props) {
  // 状態: 編集中かどうか
  // 状態: 編集中のテキスト
  // 状態: 保存中かどうか
  // 状態: エラーメッセージ
}
```

**機能**:
- 通常時: タイトルテキスト + 編集アイコンを表示
- 編集時: テキスト入力欄 + 保存/キャンセルボタン
- Enter で保存、Escape でキャンセル
- 保存中はローディング表示
- エラー時はエラーメッセージ表示

#### 2.3 FolderItemList への統合

**ファイル**: `frontend/src/components/FolderTree/FolderItemList.tsx`

変更点:
1. Props に `onRenameItem: (itemId: string, newTitle: string) => Promise<void>` を追加
2. タイトル表示部分を `InlineEditTitle` コンポーネントに置き換え
3. `onRenameItem` を呼び出してタイトルを更新

#### 2.4 LibraryTab への統合

**ファイル**: `frontend/src/components/tabs/LibraryTab.tsx`

変更点:
1. `handleRenameItem` ハンドラを追加
2. API 呼び出し後、items 配列を更新
3. FolderItemList に `onRenameItem` を渡す

#### 2.5 ResultsTab への統合

**ファイル**: `frontend/src/components/tabs/ResultsTab.tsx`

変更点:
1. メタ情報エリアのタイトル部分に `InlineEditTitle` を使用
2. タイトル更新後、result を再取得

## データフロー

### タイトルリネームのシーケンス

```
User                   UI Component          API Client           Backend
 │                         │                     │                   │
 │  タイトルをクリック      │                     │                   │
 │ ─────────────────────>  │                     │                   │
 │                         │                     │                   │
 │                   [編集モード開始]             │                   │
 │  <──────────────────── │                     │                   │
 │                         │                     │                   │
 │  新タイトルを入力       │                     │                   │
 │  + Enterを押下          │                     │                   │
 │ ─────────────────────>  │                     │                   │
 │                         │                     │                   │
 │                         │  updateJobTitle()   │                   │
 │                         │ ─────────────────>  │                   │
 │                         │                     │  PATCH /api/jobs  │
 │                         │                     │ ─────────────────>│
 │                         │                     │                   │
 │                         │                     │   update DB       │
 │                         │                     │ <─────────────────│
 │                         │                     │                   │
 │                         │  {job_id, title}    │                   │
 │                         │ <─────────────────  │                   │
 │                         │                     │                   │
 │                   [UI更新]                    │                   │
 │  <──────────────────── │                     │                   │
```

## エラーハンドリング

### バックエンド

| ケース | HTTP Status | エラーメッセージ |
|--------|-------------|-----------------|
| ジョブが存在しない | 404 | Job {job_id} not found |
| タイトルが空 | 422 | Title is required |
| タイトルが長すぎる (>500) | 422 | Title too long |
| DB 更新失敗 | 500 | Failed to update title |

### フロントエンド

- API エラー時: 入力欄の下にエラーメッセージを表示
- ネットワークエラー時: トースト通知でエラーを表示
- 編集キャンセル時: 元のタイトルに戻す

## セキュリティ考慮事項

- タイトルはサニタイズして XSS を防止（フロントエンドで escape）
- バックエンドでも文字数制限を強制
- 現状は認証なしのため、将来的には認可チェックを追加

## テスト計画

### ユニットテスト

1. **JobManager.update_job_title**
   - 正常ケース: タイトル更新成功
   - 異常ケース: 存在しない job_id

2. **API エンドポイント**
   - 200: 正常更新
   - 404: ジョブ不在
   - 422: バリデーションエラー

### E2E テスト

1. Library からタイトルをリネーム
2. Results からタイトルをリネーム
3. リロード後もタイトルが保持されている

## 影響範囲

### 変更が必要なファイル

**バックエンド**:
- `backend/routers/jobs.py` - エンドポイント追加
- `backend/routers/schemas.py` - スキーマ追加
- `backend/services/job_manager.py` - メソッド追加

**フロントエンド**:
- `frontend/src/lib/api.ts` - API クライアントメソッド追加
- `frontend/src/components/common/InlineEditTitle.tsx` - 新規作成
- `frontend/src/components/FolderTree/FolderItemList.tsx` - インライン編集統合
- `frontend/src/components/tabs/LibraryTab.tsx` - ハンドラ追加
- `frontend/src/components/tabs/ResultsTab.tsx` - タイトル編集統合

### 既存機能への影響

- `user_title` カラムのみを更新するため、他機能への影響は最小限
- Library/Results の表示ロジックは既存の優先順位（user_title > audio_file.title）を維持
