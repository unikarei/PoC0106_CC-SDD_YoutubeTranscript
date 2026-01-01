'use client'

import { useState } from 'react'
import { Item } from '@/types/folder'

type Props = {
  items: Item[]
  total: number
  isLoading: boolean
  selectedItemIds: Set<string>
  onToggleSelect: (itemId: string, checked: boolean) => void
  onSelectAll: (checked: boolean) => void
  onItemClick: (itemId: string) => void
  onDeleteItem: (itemId: string) => void
  onSearch?: (params: SearchParams) => void
}

export type SearchParams = {
  q?: string
  tag?: string
  status?: string
  sort?: string
  order?: 'asc' | 'desc'
  limit?: number
  offset?: number
}

export default function FolderItemList({
  items,
  total,
  isLoading,
  selectedItemIds,
  onToggleSelect,
  onSelectAll,
  onItemClick,
  onDeleteItem,
  onSearch,
}: Props) {
  const [searchKeyword, setSearchKeyword] = useState('')
  const [searchTag, setSearchTag] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [sortBy, setSortBy] = useState('created_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')

  const handleSearch = () => {
    if (onSearch) {
      onSearch({
        q: searchKeyword || undefined,
        tag: searchTag || undefined,
        status: statusFilter || undefined,
        sort: sortBy,
        order: sortOrder,
        limit: 50,
        offset: 0,
      })
    }
  }

  const allSelected = items.length > 0 && items.every((item) => selectedItemIds.has(item.id))

  const handleSelectAll = (checked: boolean) => {
    onSelectAll(checked)
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleString('ja-JP', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getStatusBadge = (status: string) => {
    const badges = {
      queued: { bg: 'bg-gray-100', text: 'text-gray-700', label: '待機中' },
      running: { bg: 'bg-blue-100', text: 'text-blue-700', label: '実行中' },
      completed: { bg: 'bg-green-100', text: 'text-green-700', label: '完了' },
      failed: { bg: 'bg-red-100', text: 'text-red-700', label: '失敗' },
    }
    const badge = badges[status as keyof typeof badges] || badges.queued
    return (
      <span className={`px-2 py-1 rounded text-xs ${badge.bg} ${badge.text}`}>
        {badge.label}
      </span>
    )
  }

  return (
    <div className="card h-full flex flex-col">
      {/* Search/Filter Bar */}
      <div className="mb-4 space-y-3">
        <div className="flex gap-2">
          <input
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            placeholder="キーワード検索..."
            className="input-field flex-1"
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
          <input
            value={searchTag}
            onChange={(e) => setSearchTag(e.target.value)}
            placeholder="タグ"
            className="input-field w-32"
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="input-field w-32"
          >
            <option value="">全ステータス</option>
            <option value="queued">待機中</option>
            <option value="running">実行中</option>
            <option value="completed">完了</option>
            <option value="failed">失敗</option>
          </select>
          <button onClick={handleSearch} className="btn-primary px-6" disabled={isLoading}>
            {isLoading ? '検索中...' : '検索'}
          </button>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="input-field w-40"
          >
            <option value="created_at">作成日時</option>
            <option value="updated_at">更新日時</option>
            <option value="duration_seconds">再生時間</option>
            <option value="cost_usd">コスト</option>
          </select>
          <button
            onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
            className="btn-secondary px-4"
          >
            {sortOrder === 'asc' ? '↑ 昇順' : '↓ 降順'}
          </button>
          <div className="text-sm text-gray-600 ml-auto">
            {total} 件
          </div>
        </div>
      </div>

      {/* Items List */}
      <div className="flex-1 overflow-y-auto">
        {items.length > 0 && (
          <div className="mb-2 flex items-center gap-2 py-2 px-3 border-b border-gray-200">
            <input
              type="checkbox"
              checked={allSelected}
              onChange={(e) => handleSelectAll(e.target.checked)}
              className="cursor-pointer"
            />
            <span className="text-sm text-gray-600">すべて選択</span>
          </div>
        )}

        <div className="space-y-2">
          {items.map((item) => {
            const isSelected = selectedItemIds.has(item.id)
            return (
              <div
                key={item.id}
                className={`border border-gray-200 rounded-lg p-3 hover:bg-gray-50 ${
                  isSelected ? 'bg-blue-50 border-blue-300' : ''
                }`}
              >
                <div className="flex items-start gap-3">
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={(e) => onToggleSelect(item.id, e.target.checked)}
                    className="mt-1 cursor-pointer"
                  />

                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-3 mb-1">
                      <button
                        onClick={() => onItemClick(item.id)}
                        className="font-medium text-gray-900 hover:text-blue-600 text-left truncate"
                        title={item.title || ''}
                      >
                        {item.title || '（タイトルなし）'}
                      </button>
                      {getStatusBadge(item.status)}
                    </div>

                    {item.youtube_url && (
                      <div className="text-sm text-gray-600 truncate mb-1">
                        {item.youtube_url}
                      </div>
                    )}

                    <div className="flex items-center gap-3 text-xs text-gray-500">
                      <span>{formatDate(item.created_at)}</span>
                      {item.duration_seconds && (
                        <span>{Math.floor(item.duration_seconds / 60)}分</span>
                      )}
                      {item.cost_usd && <span>${item.cost_usd.toFixed(4)}</span>}
                    </div>

                    {item.tags && item.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {item.tags.map((tag) => (
                          <span
                            key={tag.id}
                            className="px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-700"
                            style={tag.color ? { backgroundColor: tag.color } : undefined}
                          >
                            {tag.name}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  <button
                    onClick={() => onDeleteItem(item.id)}
                    className="btn-secondary px-4 py-2 text-sm whitespace-nowrap"
                  >
                    削除
                  </button>
                </div>
              </div>
            )
          })}

          {!isLoading && items.length === 0 && (
            <div className="py-12 text-center text-gray-500">
              アイテムがありません
            </div>
          )}

          {isLoading && (
            <div className="py-12 text-center text-gray-500">
              読み込み中...
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
