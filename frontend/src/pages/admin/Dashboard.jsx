import { useState, useEffect } from 'react'
import api from '../../api/client'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [users, setUsers] = useState([])
  const [recentJobs, setRecentJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [statsRes, usersRes, jobsRes] = await Promise.all([
        api.get('/api/admin/stats'),
        api.get('/api/admin/users?per_page=10'),
        api.get('/api/admin/jobs?per_page=5'),
      ])
      setStats(statsRes.data)
      setUsers(usersRes.data.users || [])
      setRecentJobs(jobsRes.data.jobs || [])
    } catch (err) {
      setError(err.response?.data?.error || '加载统计数据失败')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="admin-page">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>加载中...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="admin-page">
        <div className="error-state">
          <p>{error}</p>
          <button className="btn-primary" onClick={loadData}>重试</button>
        </div>
      </div>
    )
  }

  return (
    <div className="admin-page">
      <div className="page-header">
        <h1>管理控制台</h1>
        <p>系统概览与统计信息</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">👥</div>
          <div className="stat-content">
            <div className="stat-value">{stats?.users || 0}</div>
            <div className="stat-label">注册用户</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">📋</div>
          <div className="stat-content">
            <div className="stat-value">{stats?.jobs?.total || 0}</div>
            <div className="stat-label">检测任务</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">✅</div>
          <div className="stat-content">
            <div className="stat-value">{stats?.jobs?.completed || 0}</div>
            <div className="stat-label">已完成</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">❌</div>
          <div className="stat-content">
            <div className="stat-value">{stats?.jobs?.failed || 0}</div>
            <div className="stat-label">失败</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">💾</div>
          <div className="stat-content">
            <div className="stat-value">{stats?.disk?.total || '0 B'}</div>
            <div className="stat-label">磁盘占用</div>
          </div>
        </div>
      </div>

      <div className="admin-sections">
        <div className="card">
          <h3>最近任务</h3>
          {recentJobs.length > 0 ? (
            <table className="admin-table">
              <thead>
                <tr>
                  <th>任务ID</th>
                  <th>用户</th>
                  <th>状态</th>
                  <th>创建时间</th>
                </tr>
              </thead>
              <tbody>
                {recentJobs.map(job => (
                  <tr key={job.job_id}>
                    <td><code>{job.job_id.slice(0, 8)}...</code></td>
                    <td>{job.username || '未知'}</td>
                    <td>
                      <span className={`status-badge status-${job.status}`}>
                        {getStatusText(job.status)}
                      </span>
                    </td>
                    <td>{formatDate(job.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="empty-hint">暂无任务记录</p>
          )}
        </div>

        <div className="card">
          <h3>磁盘使用</h3>
          <div className="info-list">
            <div className="info-row">
              <span className="info-label">上传文件</span>
              <span className="info-value">{stats?.disk?.uploads || '0 B'}</span>
            </div>
            <div className="info-row">
              <span className="info-label">检测结果</span>
              <span className="info-value">{stats?.disk?.results || '0 B'}</span>
            </div>
            <div className="info-row">
              <span className="info-label">总计</span>
              <span className="info-value">{stats?.disk?.total || '0 B'}</span>
            </div>
          </div>
        </div>

        <div className="card">
          <h3>用户列表</h3>
          {users.length > 0 ? (
            <table className="admin-table">
              <thead>
                <tr>
                  <th>用户名</th>
                  <th>角色</th>
                  <th>任务数</th>
                  <th>注册时间</th>
                </tr>
              </thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.id} className={!u.is_active ? 'row-disabled' : ''}>
                    <td>{u.username}</td>
                    <td>
                      <span className={`role-badge role-${u.role}`}>
                        {u.role === 'admin' ? '管理员' : '用户'}
                      </span>
                    </td>
                    <td>{u.job_count || 0}</td>
                    <td>{formatDate(u.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="empty-hint">暂无用户</p>
          )}
        </div>

        <div className="card">
          <h3>系统信息</h3>
          <div className="info-list">
            <div className="info-row">
              <span className="info-label">数据库</span>
              <span className="info-value">SQLite</span>
            </div>
            <div className="info-row">
              <span className="info-label">检测引擎</span>
              <span className="info-value">Python (KNN-DTW)</span>
            </div>
          </div>
        </div>
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
