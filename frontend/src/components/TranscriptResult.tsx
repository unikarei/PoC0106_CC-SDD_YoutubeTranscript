'use client'

import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api'

interface TranscriptResultProps {
  jobId: string
}

interface JobResult {
  job_id: string
  status: string
  audio_file?: {
    title: string
    duration_seconds: number
    format: string
    file_size_bytes: number
  }
  transcript?: {
    text: string
    language_detected: string
    transcription_model: string
    created_at: string
  }
  corrected_transcript?: {
    corrected_text: string
    original_text: string
    correction_model: string
    changes_summary: string
    created_at: string
  }
  error_message?: string
}

export default function TranscriptResult({ jobId }: TranscriptResultProps) {
  const [result, setResult] = useState<JobResult | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [exportFormat, setExportFormat] = useState<'txt' | 'srt' | 'vtt'>('txt')
  const [isExporting, setIsExporting] = useState(false)
  const [isCorrecting, setIsCorrecting] = useState(false)
  const [viewMode, setViewMode] = useState<'original' | 'corrected' | 'comparison'>('original')

  useEffect(() => {
    fetchResult()
  }, [jobId])

  const fetchResult = async () => {
    try {
      const data = await apiClient.getJobResult(jobId)
      setResult(data)
    } catch (err: any) {
      console.error('Failed to fetch result:', err)
      setError('結果の取得に失敗しました')
    } finally {
      setIsLoading(false)
    }
  }

  const handleCopy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const handleExport = async () => {
    setIsExporting(true)
    try {
      const blob = await apiClient.exportTranscript(jobId, exportFormat)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `transcript_${jobId.slice(0, 8)}.${exportFormat}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err: any) {
      console.error('Failed to export:', err)
      alert('エクスポートに失敗しました')
    } finally {
      setIsExporting(false)
    }
  }

  const handleCorrection = async () => {
    setIsCorrecting(true)
    try {
      await apiClient.requestCorrection(jobId)
      // Wait a bit then refresh result
      setTimeout(async () => {
        await fetchResult()
        setIsCorrecting(false)
      }, 2000)
    } catch (err: any) {
      console.error('Failed to request correction:', err)
      alert('校正のリクエストに失敗しました')
      setIsCorrecting(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        {error}
      </div>
    )
  }

  if (!result || !result.transcript) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded">
        文字起こし結果がまだありません
      </div>
    )
  }

  const { transcript, corrected_transcript, audio_file } = result
  const displayText = viewMode === 'corrected' && corrected_transcript 
    ? corrected_transcript.corrected_text 
    : transcript.text

  return (
    <div className="space-y-6">
      {/* 音声ファイル情報 */}
      {audio_file && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h3 className="font-medium text-gray-900 mb-2">動画情報</h3>
          <div className="text-sm text-gray-600 space-y-1">
            <p>タイトル: {audio_file.title}</p>
            <p>長さ: {Math.floor(audio_file.duration_seconds / 60)}分{audio_file.duration_seconds % 60}秒</p>
            <p>形式: {audio_file.format?.toUpperCase()}</p>
          </div>
        </div>
      )}

      {/* 校正ボタン */}
      {!corrected_transcript && (
        <div>
          <button
            onClick={handleCorrection}
            disabled={isCorrecting}
            className="btn-primary"
          >
            {isCorrecting ? 'LLM校正中...' : 'LLMで校正する'}
          </button>
          <p className="text-sm text-gray-500 mt-2">
            GPT-4oで誤変換を修正し、読みやすいテキストに校正します
          </p>
        </div>
      )}

      {/* 表示モード切り替え */}
      {corrected_transcript && (
        <div className="flex space-x-2">
          <button
            onClick={() => setViewMode('original')}
            className={`px-4 py-2 rounded ${viewMode === 'original' ? 'bg-primary-600 text-white' : 'bg-gray-200 text-gray-700'}`}
          >
            元のテキスト
          </button>
          <button
            onClick={() => setViewMode('corrected')}
            className={`px-4 py-2 rounded ${viewMode === 'corrected' ? 'bg-primary-600 text-white' : 'bg-gray-200 text-gray-700'}`}
          >
            校正後
          </button>
          <button
            onClick={() => setViewMode('comparison')}
            className={`px-4 py-2 rounded ${viewMode === 'comparison' ? 'bg-primary-600 text-white' : 'bg-gray-200 text-gray-700'}`}
          >
            並列表示
          </button>
        </div>
      )}

      {/* 文字起こし結果 */}
      {viewMode === 'comparison' && corrected_transcript ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h3 className="font-medium text-gray-900 mb-2">元のテキスト</h3>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 h-96 overflow-y-auto">
              <p className="whitespace-pre-wrap text-sm">{transcript.text}</p>
            </div>
          </div>
          <div>
            <h3 className="font-medium text-gray-900 mb-2">校正後</h3>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 h-96 overflow-y-auto">
              <p className="whitespace-pre-wrap text-sm">{corrected_transcript.corrected_text}</p>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <div className="flex justify-between items-center mb-2">
            <h3 className="font-medium text-gray-900">
              {viewMode === 'corrected' ? '校正後テキスト' : '文字起こしテキスト'}
            </h3>
            <button
              onClick={() => handleCopy(displayText)}
              className="text-sm text-primary-600 hover:text-primary-700"
            >
              {copied ? '✓ コピーしました' : 'コピー'}
            </button>
          </div>
          <div className="max-h-96 overflow-y-auto">
            <p className="whitespace-pre-wrap text-sm">{displayText}</p>
          </div>
        </div>
      )}

      {/* 変更サマリー */}
      {corrected_transcript?.changes_summary && viewMode !== 'original' && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-medium text-blue-900 mb-2">校正内容</h3>
          <p className="text-sm text-blue-800">{corrected_transcript.changes_summary}</p>
        </div>
      )}

      {/* エクスポート */}
      <div className="border-t pt-6">
        <h3 className="font-medium text-gray-900 mb-4">エクスポート</h3>
        <div className="flex items-center space-x-4">
          <select
            value={exportFormat}
            onChange={(e) => setExportFormat(e.target.value as any)}
            className="input-field max-w-xs"
          >
            <option value="txt">TXT (テキストファイル)</option>
            <option value="srt">SRT (字幕ファイル)</option>
            <option value="vtt">VTT (WebVTT字幕)</option>
          </select>
          <button
            onClick={handleExport}
            disabled={isExporting}
            className="btn-secondary"
          >
            {isExporting ? 'エクスポート中...' : 'ダウンロード'}
          </button>
        </div>
      </div>
    </div>
  )
}
