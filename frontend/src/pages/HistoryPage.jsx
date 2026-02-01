import { useState, useEffect } from 'react'
import api from '../api/client'
import JobCard from '../components/JobCard'

export default function HistoryPage() {
  const [jobs, setJobs] = useState([])
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadJobs()
  }, [page])

  const loadJobs = async () => {
    setLoading(true)
    try {
      const res = await api.get('/api/jobs', { params: { page, per_page: 10 } })
      setJobs(res.data.jobs || [])
      setTotalPages(res.data.pages || 1)
    } catch (err) {
      console.error('加载历史记录失败:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (jobId) => {
    if (!confirm('确定要删除这个任务吗？相关文件也会被删除。')) return

    try {
      await api.delete(`/api/jobs/${jobId}`)
      loadJobs()
    } catch (err) {
      alert(`删除失败: ${err.response?.data?.error || err.message}`)
    }
  }

  return (
    <div className="history-page">
      <div className="page-header">
        <h1>📋 历史记录</h1>
        <p>查看您的检测任务历史</p>
      </div>

      {loading ? (
        <div className="loading-container">
          <div className="spinner"></div>
          <p>加载中...</p>
        </div>
      ) : jobs.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📭</div>
          <h3>暂无检测记录</h3>
          <p>去「检测分析」页面开始您的第一次检测吧</p>
        </div>
      ) : (
        <>
          <div className="job-list">
            {jobs.map(job => (
              <JobCard key={job.job_id} job={job} onDelete={handleDelete} />
            ))}
          </div>

          {totalPages > 1 && (
            <div className="pagination">
              <button
                className="btn-small"
                disabled={page <= 1}
                onClick={() => setPage(p => p - 1)}
              >
                上一页
              </button>
              <span className="page-info">{page} / {totalPages}</span>
              <button
                className="btn-small"
                disabled={page >= totalPages}
                onClick={() => setPage(p => p + 1)}
              >
                下一页
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
