import { useState, useRef } from 'react'

export default function FileUpload({ label, accept, onChange, file }) {
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef(null)

  const handleDragOver = (e) => {
    e.preventDefault()
    setDragOver(true)
  }

  const handleDragLeave = () => {
    setDragOver(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile && accept.split(',').some(ext => droppedFile.name.toLowerCase().endsWith(ext.trim()))) {
      onChange(droppedFile)
    }
  }

  const handleClick = () => {
    inputRef.current?.click()
  }

  const handleChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      onChange(selectedFile)
    }
  }

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1024 / 1024).toFixed(2)} MB`
  }

  return (
    <div className="file-upload">
      <label className="upload-label">{label}</label>
      <div
        className={`upload-zone ${dragOver ? 'drag-over' : ''} ${file ? 'has-file' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          onChange={handleChange}
          style={{ display: 'none' }}
        />
        {file ? (
          <div className="file-info">
            <span className="file-icon">📁</span>
            <span className="file-name">{file.name}</span>
            <span className="file-size">{formatSize(file.size)}</span>
          </div>
        ) : (
          <div className="upload-placeholder">
            <span className="upload-icon">📤</span>
            <span>点击或拖拽文件到此处</span>
          </div>
        )}
      </div>
    </div>
  )
}
