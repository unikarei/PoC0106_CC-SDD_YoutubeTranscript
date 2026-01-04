# 設計: ResultsタブへのNote機能追加

## アーキテクチャ概要

```
Frontend (React/Next.js)
    |
    v
Backend API (FastAPI)
    |
    v
Database (SQLite/PostgreSQL)
```

## データベース設計

### 新規テーブル: job_notes

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | VARCHAR(36) | PK, NOT NULL | UUID |
| job_id | VARCHAR(36) | FK(jobs.id), UNIQUE, NOT NULL | ジョブID |
| content | TEXT | NOT NULL | メモ内容 |
| created_at | DATETIME | NOT NULL, DEFAULT NOW | 作成日時 |
| updated_at | DATETIME | NOT NULL, DEFAULT NOW | 更新日時 |

**リレーション:**
- `job_notes.job_id` → `jobs.id` (1:1)
- CASCADE DELETE

## API設計

### GET /api/v1/jobs/{job_id}/note

**説明:** ジョブのNoteを取得

**レスポンス:**
```json
{
  "job_id": "uuid",
  "content": "メモ内容",
  "created_at": "2026-01-04T10:00:00Z",
  "updated_at": "2026-01-04T10:00:00Z"
}
```

**Noteが存在しない場合:**
```json
{
  "job_id": "uuid",
  "content": null,
  "created_at": null,
  "updated_at": null
}
```

### PUT /api/v1/jobs/{job_id}/note

**説明:** ジョブのNoteを作成・更新（Upsert）

**リクエスト:**
```json
{
  "content": "メモ内容"
}
```

**レスポンス:**
```json
{
  "job_id": "uuid",
  "content": "メモ内容",
  "created_at": "2026-01-04T10:00:00Z",
  "updated_at": "2026-01-04T10:00:00Z"
}
```

## フロントエンド設計

### コンポーネント変更

#### ResultsTab.tsx

**変更点:**
1. `SubTab` 型に `'note'` を追加
2. Noteサブタブボタンを追加
3. Note表示・編集UIを追加
4. Note取得・保存ロジックを追加

**新規State:**
```typescript
const [noteContent, setNoteContent] = useState('')
const [originalNote, setOriginalNote] = useState('')
const [isNoteSaving, setIsNoteSaving] = useState(false)
const [noteLastSaved, setNoteLastSaved] = useState<string | null>(null)
```

**UIデザイン:**
- テキストエリア（複数行入力）
- 保存ボタン
- 保存状態の表示（最終保存時刻）

### APIクライアント変更

#### api.ts

**新規メソッド:**
```typescript
async getNote(jobId: string): Promise<NoteResponse>
async updateNote(jobId: string, content: string): Promise<NoteResponse>
```

## バックエンド設計

### モデル追加

#### models.py

```python
class JobNote(Base):
    __tablename__ = "job_notes"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), unique=True, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    job = relationship("Job", back_populates="note")
```

### ルーター追加

#### routers/notes.py（新規）

- `GET /api/v1/jobs/{job_id}/note`
- `PUT /api/v1/jobs/{job_id}/note`

### Jobモデルへのリレーション追加

```python
note = relationship("JobNote", back_populates="job", uselist=False, cascade="all, delete-orphan")
```

## マイグレーション

### Alembicマイグレーション

新規マイグレーションファイル: `20260104_001_add_job_notes.py`

## シーケンス図

### Note取得フロー

```
User -> ResultsTab: ジョブ選択
ResultsTab -> API Client: getNote(jobId)
API Client -> Backend: GET /api/v1/jobs/{jobId}/note
Backend -> Database: SELECT * FROM job_notes WHERE job_id = ?
Database -> Backend: Note or null
Backend -> API Client: NoteResponse
API Client -> ResultsTab: NoteResponse
ResultsTab -> User: Note表示
```

### Note保存フロー

```
User -> ResultsTab: 保存ボタンクリック
ResultsTab -> API Client: updateNote(jobId, content)
API Client -> Backend: PUT /api/v1/jobs/{jobId}/note
Backend -> Database: UPSERT job_notes
Database -> Backend: Updated Note
Backend -> API Client: NoteResponse
API Client -> ResultsTab: NoteResponse
ResultsTab -> User: 保存完了表示
```

## 影響範囲

### 変更ファイル
- `backend/models.py` - JobNoteモデル追加、Jobリレーション追加
- `backend/routers/` - notes.py新規作成
- `backend/main.py` - ルーター登録
- `frontend/src/lib/api.ts` - APIクライアントメソッド追加
- `frontend/src/components/tabs/ResultsTab.tsx` - Noteサブタブ追加

### 新規ファイル
- `backend/routers/notes.py`
- `alembic/versions/20260104_001_add_job_notes.py`

## 技術的考慮事項

1. **Upsert戦略:** SQLiteとPostgreSQLの両方で動作するUpsertロジックを実装
2. **空のNote:** 空文字列は許可し、NULLとは区別する
3. **既存APIへの影響:** getJobResult APIには含めず、独立したAPIとする
