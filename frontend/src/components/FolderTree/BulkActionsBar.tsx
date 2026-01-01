'use client'

import { useState } from 'react'
import { Tag } from '@/types/folder'

type Props = {
  selectedCount: number
  availableTags: Tag[]
  onBulkMove: () => void
  onBulkTag: () => void
  onBulkDelete: () => void
  onCancel: () => void
}

export default function BulkActionsBar({
  selectedCount,
  availableTags,
  onBulkMove,
  onBulkTag,
  onBulkDelete,
  onCancel,
}: Props) {
  const [showMenu, setShowMenu] = useState(false)

  if (selectedCount === 0) {
    return null
  }

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-blue-600 text-white shadow-lg z-50">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="font-semibold">{selectedCount} 件選択中</span>
            <button
              onClick={onCancel}
              className="text-sm underline hover:no-underline"
            >
              選択解除
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onBulkMove}
              className="bg-white text-blue-600 px-4 py-2 rounded hover:bg-gray-100 font-medium"
            >
              📁 移動
            </button>
            <button
              onClick={onBulkTag}
              className="bg-white text-blue-600 px-4 py-2 rounded hover:bg-gray-100 font-medium"
            >
              🏷️ タグ付け
            </button>
            <button
              onClick={onBulkDelete}
              className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 font-medium"
            >
              🗑️ 削除
            </button>

            <div className="relative">
              <button
                onClick={() => setShowMenu(!showMenu)}
                className="bg-white text-blue-600 px-4 py-2 rounded hover:bg-gray-100 font-medium"
              >
                ⋮ その他
              </button>
              {showMenu && (
                <div className="absolute bottom-full right-0 mb-2 bg-white text-gray-800 shadow-lg rounded-lg w-48 py-2">
                  <button
                    className="w-full text-left px-4 py-2 hover:bg-gray-100"
                    onClick={() => {
                      setShowMenu(false)
                      alert('一括再実行機能は未実装です')
                    }}
                  >
                    🔄 再実行
                  </button>
                  <button
                    className="w-full text-left px-4 py-2 hover:bg-gray-100"
                    onClick={() => {
                      setShowMenu(false)
                      alert('一括再校正機能は未実装です')
                    }}
                  >
                    ✏️ 再校正
                  </button>
                  <button
                    className="w-full text-left px-4 py-2 hover:bg-gray-100"
                    onClick={() => {
                      setShowMenu(false)
                      alert('一括エクスポート機能は未実装です')
                    }}
                  >
                    💾 エクスポート
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
