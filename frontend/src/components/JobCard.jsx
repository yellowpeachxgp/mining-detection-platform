import { Link } from 'react-router-dom'

export default function JobCard({ job, onDelete }) {
  const statusMap = {
    pending: { label: '等待中', class: 'status-pending' },
    running: { label: '运行中', class: 'status-running' },
    completed: { label: '已完成', class: 'status-completed' },
    failed: { label: '失败', class: 'status-failed' },
  }

  const status = statusMap[job.status] || { label: job.status, class: '' }

  const formatDate = (iso) => {
    if (!iso) return '-'
    const date = new Date(iso)
    return date.toLocaleString('zh-CN')
  }

  return (
    <div className="job-card">
      <div className="job-header">
        <span className={`job-status ${status.class}`}>{status.label}</span>
        <span className="job-id">#{job.job_id.slice(0, 8)}</span>
      </div>

      <div className="job-body">
        <div className="job-info">
          <div><strong>起始年份:</strong> {job.startyear || '-'}</div>
          <div><strong>引擎:</strong> {job.engine || '-'}</div>
          <div><strong>NDVI文件:</strong> {job.ndvi_filename || '-'}</div>
          <div><strong>创建时间:</strong> {formatDate(job.created_at)}</div>
          {job.completed_at && (
            <div><strong>完成时间:</strong> {formatDate(job.completed_at)}</div>
          )}
          {job.error_message && (
            <div className="job-error"><strong>错误:</strong> {job.error_message}</div>
          )}
        </div>
      </div>

      <div className="job-actions">
        {job.status === 'completed' && (
          <Link to={`/detect?job=${job.job_id}`} className="btn-small btn-primary">
            查看结果
          </Link>
        )}
        <button className="btn-small btn-danger" onClick={() => onDelete(job.job_id)}>
          删除
        </button>
      </div>
    </div>
  )
}
