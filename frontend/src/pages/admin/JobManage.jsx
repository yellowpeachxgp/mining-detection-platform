import { useState, useEffect } from 'react'
import api from '../../api/client'

export default function JobManage() {
  const [jobs, setJobs] = useState([])
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filter, setFilter] = useState({ status: '', username: '' })
  const [actionLoading, setActionLoading] = useState(false)

  useEffect(() => {
    loadJobs()
  }, [page, filter.status])

  const loadJobs = async () => {
    setLoading(true)
    try {
      const params = { page, per_page: 20 }
      if (filter.status) params.status = filter.status
      if (filter.username) params.username = filter.username

      const res = await api.get('/api/admin/jobs', { params })
      setJobs(res.data.jobs || [])
      setTotalPages(res.data.pages || 1)
    } catch (err) {
      setError(err.response?.data?.error || '加载任务列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (job) => {
    if (!confirm(`确定要删除任务 "${job.job_id.slice(0, 8)}..." 吗？相关文件也会被删除。`)) {
      return
    }

    setActionLoading(true)
    try {
      await api.delete(`/api/admin/jobs/${job.job_id}`)
      loadJobs()
    } catch (err) {
      alert(err.response?.data?.error || '删除失败')
    } finally {
      setActionLoading(false)
    }
  }

  const handleSearch = (e) => {
    e.preventDefault()
    setPage(1)
    loadJobs()
  }

  return (
    <div className="admin-page">
      <div className="page-header">
        <h1>任务管理</h1>
        <p>管理所有检测任务</p>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="card">
        <div className="card-header">
          <h3>筛选条件</h3>
        </div>
        <form className="filter-form" onSubmit={handleSearch}>
          <div className="filter-row">
            <div className="form-group">
              <label>状态</label>
              <select
                value={filter.status}
                onChange={(e) => setFilter(f => ({ ...f, status: e.target.value }))}
              >
                <option value="">全部</option>
                <option value="pending">等待中</option>
                <option value="running">运行中</option>
                <option value="completed">已完成</option>
                <option value="failed">失败</option>
              </select>
            </div>
            <div className="form-group">
              <label>用户名</label>
              <input
                type="text"
                value={filter.username}
                onChange={(e) => setFilter(f => ({ ...f, username: e.target.value }))}
                placeholder="输入用户名搜索"
              />
            </div>
            <button type="submit" className="btn-primary">搜索</button>
          </div>
        </form>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>任务列表</h3>
          <span className="badge">{jobs.length} 条记录</span>
        </div>

        {loading ? (
          <div className="loading-container">
            <div className="spinner"></div>
          </div>
        ) : jobs.length === 0 ? (
          <div className="empty-state">
            <p>暂无任务记录</p>
          </div>
        ) : (
          <>
            <div className="table-container">
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>任务ID</th>
                    <th>用户</th>
                    <th>状态</th>
                    <th>引擎</th>
                    <th>起始年份</th>
                    <th>NDVI文件</th>
                    <th>创建时间</th>
                    <th>完成时间</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {jobs.map(job => (
                    <tr key={job.job_id}>
                      <td>
                        <code title={job.job_id}>{job.job_id.slice(0, 8)}...</code>
                      </td>
                      <td>{job.username || '-'}</td>
                      <td>
                        <span className={`status-badge status-${job.status}`}>
                          {getStatusText(job.status)}
                        </span>
                      </td>
                      <td>{job.engine || 'python'}</td>
                      <td>{job.startyear || '-'}</td>
                      <td title={job.ndvi_filename}>
                        {truncateFilename(job.ndvi_filename)}
                      </td>
                      <td>{formatDate(job.created_at)}</td>
                      <td>{formatDate(job.completed_at)}</td>
                      <td className="action-cell">
                        <button
                          className="btn-small btn-secondary"
                          onClick={() => window.open(`/detect?job=${job.job_id}`, '_blank')}
                          disabled={job.status !== 'completed'}
                          title={job.status !== 'completed' ? '任务未完成' : '查看结果'}
                        >
                          查看
                        </button>
                        <button
                          className="btn-small btn-danger"
                          onClick={() => handleDelete(job)}
                          disabled={actionLoading}
                        >
                          删除
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
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
    </div>
  )
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

function getStatusText(status) {
  const map = {
    pending: '等待中',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
  }
  return map[status] || status
}

function truncateFilename(filename) {
  if (!filename) return '-'
  if (filename.length <= 20) return filename
  return filename.slice(0, 17) + '...'
}
