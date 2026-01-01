'use client'

import { useState } from 'react'
import { Folder, FolderItemCount } from '@/types/folder'

type Props = {
  folders: Folder[]
  selectedFolderId: string | null
  onSelectFolder: (folderId: string) => void
  onCreateFolder: (parentId: string | null) => void
  onEditFolder: (folderId: string) => void
  onDeleteFolder: (folderId: string) => void
}

export default function FolderTreePanel({
  folders,
  selectedFolderId,
  onSelectFolder,
  onCreateFolder,
  onEditFolder,
  onDeleteFolder,
}: Props) {
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set())

  const toggleExpanded = (folderId: string) => {
    setExpandedFolders((prev) => {
      const next = new Set(prev)
      if (next.has(folderId)) {
        next.delete(folderId)
      } else {
        next.add(folderId)
      }
      return next
    })
  }

  const renderItemCount = (count: FolderItemCount) => {
    const total = count.queued + count.running + count.completed + count.failed
    if (total === 0) return null
    
    return (
      <span className="text-xs text-gray-500 ml-2">
        ({total})
        {count.running > 0 && <span className="text-blue-600 ml-1">⏳{count.running}</span>}
        {count.failed > 0 && <span className="text-red-600 ml-1">❌{count.failed}</span>}
      </span>
    )
  }

  const renderFolder = (folder: Folder, depth: number = 0) => {
    const isExpanded = expandedFolders.has(folder.id)
    const isSelected = selectedFolderId === folder.id
    const hasChildren = folder.children && folder.children.length > 0

    return (
      <div key={folder.id}>
        <div
          className={`flex items-center gap-1 py-2 px-2 hover:bg-gray-100 cursor-pointer ${
            isSelected ? 'bg-blue-50 border-l-4 border-blue-500' : ''
          }`}
          style={{ paddingLeft: `${depth * 12 + 8}px` }}
        >
          {hasChildren && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                toggleExpanded(folder.id)
              }}
              className="w-4 h-4 flex items-center justify-center text-gray-500 hover:text-gray-700 flex-shrink-0"
            >
              {isExpanded ? '▼' : '▶'}
            </button>
          )}
          {!hasChildren && <span className="w-4 flex-shrink-0" />}
          
          <button
            onClick={() => onSelectFolder(folder.id)}
            className="flex-1 text-left flex items-center gap-1 min-w-0 overflow-hidden"
            title={folder.name}
          >
            <span className="text-base flex-shrink-0">{folder.icon || '📁'}</span>
            <span className="font-medium truncate text-sm">{folder.name}</span>
            {renderItemCount(folder.item_count)}
          </button>

          <div className="flex items-center gap-0.5 flex-shrink-0">
            <button
              onClick={(e) => {
                e.stopPropagation()
                onCreateFolder(folder.id)
              }}
              className="text-xs text-gray-500 hover:text-blue-600 px-1.5 py-0.5"
              title="サブフォルダを作成"
            >
              +
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation()
                onEditFolder(folder.id)
              }}
              className="text-xs text-gray-500 hover:text-blue-600 px-1.5 py-0.5"
              title="編集"
            >
              ✏️
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation()
                onDeleteFolder(folder.id)
              }}
              className="text-xs text-gray-500 hover:text-red-600 px-1.5 py-0.5"
              title="削除"
            >
              🗑️
            </button>
          </div>
        </div>

        {hasChildren && isExpanded && (
          <div>
            {folder.children.map((child) => renderFolder(child, depth + 1))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="card h-full overflow-y-auto">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">📂 フォルダ</h2>
        <button
          onClick={() => onCreateFolder(null)}
          className="btn-primary text-sm px-4 py-2"
        >
          + 新規フォルダ
        </button>
      </div>

      <div className="border-t border-gray-200">
        {folders.length === 0 ? (
          <div className="py-8 text-center text-gray-500">
            フォルダがありません
          </div>
        ) : (
          folders.map((folder) => renderFolder(folder, 0))
        )}
      </div>
    </div>
  )
}
