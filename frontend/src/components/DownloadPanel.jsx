import { useState, useEffect } from 'react'
import api from '../api/client'

export default function DownloadPanel({ jobId }) {
  const [files, setFiles] = useState([])
  const [selected, setSelected] = useState(new Set())
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!jobId) return
    loadFiles()
  }, [jobId])

  const loadFiles = async () => {
    try {
      const res = await api.get(`/api/job-files/${jobId}`)
      setFiles(res.data.files || [])
    } catch (e) {
      console.error('加载文件列表失败:', e)
    }
  }

  const toggleSelect = (filename) => {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(filename)) {
        next.delete(filename)
      } else {
        next.add(filename)
      }
      return next
    })
  }

  const selectAll = () => {
    setSelected(new Set(files.map(f => f.filename)))
  }

  const deselectAll = () => {
    setSelected(new Set())
  }

  const downloadSelected = async () => {
    const filenames = Array.from(selected)
    if (filenames.length === 0) return

    if (filenames.length === 1) {
      // 单文件直接下载
      const file = files.find(f => f.filename === filenames[0])
      if (file) {
        const a = document.createElement('a')
        a.href = file.url
        a.download = file.filename
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
      }
    } else {
      // 多文件打包下载
      setLoading(true)
      try {
        const res = await api.post(`/api/download-zip/${jobId}`, { filenames }, {
          responseType: 'blob',
        })
        const url = URL.createObjectURL(res.data)
        const a = document.createElement('a')
        a.href = url
        a.download = `mining_results_${jobId.slice(0, 8)}.zip`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
      } catch (e) {
        console.error('下载失败:', e)
      } finally {
        setLoading(false)
      }
    }
  }

  const totalSize = files
    .filter(f => selected.has(f.filename))
    .reduce((sum, f) => sum + f.size, 0)

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1024 / 1024).toFixed(2)} MB`
  }

  if (!jobId || files.length === 0) return null

  return (
    <div className="download-panel card">
      <h3>📥 下载结果文件</h3>
      <div className="download-controls">
        <button className="btn-small" onClick={selectAll}>全选</button>
        <button className="btn-small" onClick={deselectAll}>取消全选</button>
      </div>
      <div className="file-list">
        {files.map(f => (
          <div key={f.filename} className="file-item" onClick={() => toggleSelect(f.filename)}>
            <input
              type="checkbox"
              checked={selected.has(f.filename)}
              onChange={() => {}}
            />
            <span className="file-name">{f.label}</span>
            <span className="file-size">{f.size_formatted}</span>
          </div>
        ))}
      </div>
      <div className="download-summary">
        <span>已选择 {selected.size} 个文件</span>
        <span>{selected.size > 0 ? formatSize(totalSize) : ''}</span>
      </div>
      <button
        className="btn-primary"
        disabled={selected.size === 0 || loading}
        onClick={downloadSelected}
      >
        {loading ? '打包中...' : '📦 下载选中文件'}
      </button>
    </div>
  )
}
