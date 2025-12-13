'use client'

import { useState } from 'react'
import UrlInputForm from '@/components/UrlInputForm'
import JobStatus from '@/components/JobStatus'
import TranscriptResult from '@/components/TranscriptResult'

export default function HomePage() {
  const [jobId, setJobId] = useState<string | null>(null)
  const [jobStatus, setJobStatus] = useState<string>('idle')

  const handleJobCreated = (id: string) => {
    setJobId(id)
    setJobStatus('pending')
  }

  const handleStatusChange = (status: string) => {
    setJobStatus(status)
  }

  return (
    <div className="space-y-8">
      {/* URL入力フォーム */}
      <section className="card">
        <h2 className="text-xl font-semibold mb-4">1. YouTube動画URL入力</h2>
        <UrlInputForm 
          onJobCreated={handleJobCreated}
          disabled={jobStatus !== 'idle' && jobStatus !== 'completed' && jobStatus !== 'failed'}
        />
      </section>

      {/* ジョブステータス */}
      {jobId && (
        <section className="card">
          <h2 className="text-xl font-semibold mb-4">2. 処理状況</h2>
          <JobStatus 
            jobId={jobId}
            onStatusChange={handleStatusChange}
          />
        </section>
      )}

      {/* 文字起こし結果 */}
      {jobId && jobStatus === 'completed' && (
        <section className="card">
          <h2 className="text-xl font-semibold mb-4">3. 文字起こし結果</h2>
          <TranscriptResult jobId={jobId} />
        </section>
      )}
    </div>
  )
}
