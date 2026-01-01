# 設計書: Library フォルダツリー管理（階層 + タグ併用）

## 1. アーキテクチャ概要

### 1.1 設計方針
- 既存のJob/Transcript等のテーブルは維持（後方互換性）
- 新規にFolder/Item/Artifactテーブルを追加し、既存データへの参照として利用
- タグは中間テーブル（tags/item_tags）で管理
- 段階的な移行を可能にする

### 1.2 システム構成図
```
[Frontend (React/Next.js)]
    ↓ API calls
[Backend (FastAPI)]
    ↓ ORM
[Database (PostgreSQL)]
    - folders (新規)
    - items (新規)
    - artifacts (新規) 
    - tags (新規)
    - item_tags (新規)
    - jobs (既存)
    - transcripts (既存)
    - corrected_transcripts (既存)
    - qa_results (既存)
```

## 2. データモデル設計

### 2.1 新規テーブル

#### folders
フォルダを管理する階層構造テーブル

```sql
CREATE TABLE folders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    parent_id UUID REFERENCES folders(id) ON DELETE CASCADE,
    path TEXT NOT NULL,  -- materialized path (例: "/root/subfolder")
    
    -- フォルダ既定値
    default_language VARCHAR(10),
    default_model VARCHAR(50),
    default_prompt TEXT,
    default_qa_enabled BOOLEAN DEFAULT false,
    default_output_format VARCHAR(10) DEFAULT 'txt',
    naming_template VARCHAR(500),
    
    -- メタ情報
    description TEXT,
    color VARCHAR(20),
    icon VARCHAR(50),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT folders_name_parent_unique UNIQUE (name, parent_id)
);

CREATE INDEX idx_folders_parent_id ON folders(parent_id);
CREATE INDEX idx_folders_path ON folders(path);
```

#### items
動画（ジョブ）を管理するテーブル

```sql
CREATE TABLE items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    folder_id UUID NOT NULL REFERENCES folders(id) ON DELETE RESTRICT,
    job_id UUID UNIQUE REFERENCES jobs(id) ON DELETE CASCADE,
    
    -- 基本情報
    title VARCHAR(500),
    youtube_url TEXT NOT NULL,
    
    -- ステータス（jobsと同期）
    status VARCHAR(20) NOT NULL DEFAULT 'queued',
    progress INTEGER DEFAULT 0,
    error_message TEXT,
    
    -- メタ情報
    duration_seconds INTEGER,
    file_size_bytes BIGINT,
    cost_usd DECIMAL(10, 4),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT items_status_check CHECK (status IN ('queued', 'running', 'completed', 'failed'))
);

CREATE INDEX idx_items_folder_id ON items(folder_id);
CREATE INDEX idx_items_job_id ON items(job_id);
CREATE INDEX idx_items_status ON items(status);
CREATE INDEX idx_items_created_at ON items(created_at DESC);
CREATE INDEX idx_items_updated_at ON items(updated_at DESC);
```

#### artifacts
生成物を管理するテーブル

```sql
CREATE TABLE artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    
    -- 種別
    artifact_type VARCHAR(50) NOT NULL,  -- 'transcript', 'proofread', 'qa', 'export', 'summary'
    
    -- 既存テーブルへの参照
    transcript_id UUID REFERENCES transcripts(id) ON DELETE CASCADE,
    corrected_transcript_id UUID REFERENCES corrected_transcripts(id) ON DELETE CASCADE,
    qa_result_id UUID REFERENCES qa_results(id) ON DELETE CASCADE,
    
    -- 汎用データ
    content TEXT,
    metadata JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT artifacts_type_check CHECK (artifact_type IN ('transcript', 'proofread', 'qa', 'export', 'summary'))
);

CREATE INDEX idx_artifacts_item_id ON artifacts(item_id);
CREATE INDEX idx_artifacts_type ON artifacts(artifact_type);
```

#### tags
タグマスタテーブル

```sql
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    color VARCHAR(20),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_tags_name ON tags(name);
```

#### item_tags
アイテムとタグの中間テーブル

```sql
CREATE TABLE item_tags (
    item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    PRIMARY KEY (item_id, tag_id)
);

CREATE INDEX idx_item_tags_item_id ON item_tags(item_id);
CREATE INDEX idx_item_tags_tag_id ON item_tags(tag_id);
```

### 2.2 既存テーブルとの関係

- `items.job_id` → `jobs.id` （1:1関係、NULLABLEで段階移行可能）
- `artifacts.transcript_id` → `transcripts.id`
- `artifacts.corrected_transcript_id` → `corrected_transcripts.id`
- `artifacts.qa_result_id` → `qa_results.id`

## 3. API設計

### 3.1 Folder API

#### GET /api/folders/tree
フォルダツリー全体を取得

**Response:**
```json
{
  "folders": [
    {
      "id": "uuid",
      "name": "Inbox",
      "parent_id": null,
      "path": "/Inbox",
      "children": [...],
      "item_count": {
        "queued": 5,
        "running": 2,
        "completed": 100,
        "failed": 3
      }
    }
  ]
}
```

#### POST /api/folders
フォルダ作成

**Request:**
```json
{
  "name": "New Folder",
  "parent_id": "uuid",
  "description": "...",
  "default_language": "ja",
  "default_model": "gpt-4o-mini-transcribe"
}
```

#### PUT /api/folders/{folder_id}
フォルダ更新

#### DELETE /api/folders/{folder_id}
フォルダ削除（中身が空の場合のみ）

#### GET /api/folders/{folder_id}/settings
フォルダ設定取得

#### PUT /api/folders/{folder_id}/settings
フォルダ設定更新

### 3.2 Item API

#### GET /api/folders/{folder_id}/items
フォルダ内アイテム一覧

**Query Parameters:**
- `q`: keyword search
- `tag`: tag filter
- `status`: status filter
- `from`: date from
- `to`: date to
- `sort`: sort by (created_at, updated_at, duration, cost)
- `order`: asc/desc
- `limit`, `offset`: pagination

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "...",
      "youtube_url": "...",
      "status": "completed",
      "progress": 100,
      "duration_seconds": 600,
      "cost_usd": 0.05,
      "tags": ["tag1", "tag2"],
      "created_at": "...",
      "updated_at": "..."
    }
  ],
  "total": 100
}
```

#### GET /api/items/search
全体検索

#### POST /api/items/{item_id}/move
アイテム移動

**Request:**
```json
{
  "target_folder_id": "uuid"
}
```

#### GET /api/items/{item_id}
アイテム詳細取得

#### DELETE /api/items/{item_id}
アイテム削除

### 3.3 Bulk Operations API

#### POST /api/items/bulk/move
一括移動

**Request:**
```json
{
  "item_ids": ["uuid1", "uuid2"],
  "target_folder_id": "uuid"
}
```

#### POST /api/items/bulk/tag
一括タグ付け

**Request:**
```json
{
  "item_ids": ["uuid1", "uuid2"],
  "tag_names": ["tag1", "tag2"],
  "action": "add" | "remove" | "replace"
}
```

#### POST /api/items/bulk/delete
一括削除

#### POST /api/items/bulk/rerun
一括再実行

**Request:**
```json
{
  "item_ids": ["uuid1", "uuid2"],
  "language": "ja",
  "model": "gpt-4o-mini-transcribe"
}
```

#### POST /api/items/bulk/reproofread
一括再校正

#### POST /api/items/bulk/export
一括エクスポート

**Request:**
```json
{
  "item_ids": ["uuid1", "uuid2"],
  "format": "txt" | "md" | "json"
}
```

**Response:**
```json
{
  "export_id": "uuid",
  "download_url": "/api/exports/{export_id}"
}
```

### 3.4 Tag API

#### GET /api/tags
タグ一覧

#### POST /api/tags
タグ作成

#### DELETE /api/tags/{tag_id}
タグ削除

## 4. UI設計

### 4.1 画面構成

```
┌─────────────────────────────────────────────────────┐
│ Batch | Results | Library | Settings                │
├──────────┬──────────────────────────────────────────┤
│          │ Search: [_______] [Folder/All] [Filters] │
│ Folder   ├──────────────────────────────────────────┤
│ Tree     │ ┌────────────────────────────────────┐   │
│          │ │ ☐ Item 1   [completed] [tags...]   │   │
│ ⊞ Inbox  │ │ ☐ Item 2   [running 45%]           │   │
│   (110)  │ │ ☐ Item 3   [failed] Error...       │   │
│ ⊞ Work   │ └────────────────────────────────────┘   │
│   (45)   │                                           │
│ + New    │ [Actions: Move | Tag | Delete | ...]     │
└──────────┴──────────────────────────────────────────┘
```

### 4.2 コンポーネント構成

#### FolderTreePanel
- フォルダツリー表示
- フォルダ選択
- フォルダ編集（新規/名称変更/削除）
- ドラッグ&ドロップ（オプション）

#### FolderItemList
- フォルダ内アイテム一覧
- チェックボックスで複数選択
- ソート/フィルタUI
- ステータスバッジ表示

#### BulkActionsBar
- 一括操作ボタン
- 選択件数表示
- 確認ダイアログ

#### FolderSettingsDialog
- フォルダ既定値編集
- モーダルまたはサイドパネル

## 5. 実装計画

### 5.1 マイグレーション戦略

1. **Phase 1**: 新規テーブル作成
2. **Phase 2**: デフォルトフォルダ（Inbox）作成
3. **Phase 3**: 既存Jobsデータの自動Item化（バッチスクリプト）
4. **Phase 4**: UI実装と段階的ロールアウト

### 5.2 データ移行スクリプト

```python
# migrate_jobs_to_items.py
# 既存jobsをitemsに変換
def migrate_existing_jobs():
    # 1. デフォルトフォルダ（Inbox）を作成または取得
    inbox = get_or_create_inbox()
    
    # 2. job_idを持たないjobsを順次変換
    for job in get_unmigrated_jobs():
        item = create_item_from_job(job, inbox.id)
        create_artifacts_from_job_results(item.id, job.id)
```

## 6. セキュリティと制約

- フォルダ削除は中身が空の場合のみ許可
- 処理中（running）のアイテムは移動・削除を制限
- 一括操作は最大100件まで
- 長時間実行する一括操作はバックグラウンドジョブ化

## 7. パフォーマンス考慮

- フォルダツリーはmaterialized pathで高速検索
- item_countはキャッシュまたは集計テーブルで管理
- 検索はインデックスを活用
- ページネーションで大量データに対応

## 8. 将来拡張

- フォルダ共有機能
- 高度な全文検索（Elasticsearch等）
- 自動フォルダ振り分けルール
- カスタムビュー/フィルタ保存
