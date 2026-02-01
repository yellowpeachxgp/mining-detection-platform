import { useState, useCallback, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import api from '../api/client'
import MapView, { openMapPopup } from '../components/MapView'
import NdviChart from '../components/NdviChart'
import FileUpload from '../components/FileUpload'
import DownloadPanel from '../components/DownloadPanel'

export default function DetectionPage() {
  const [searchParams] = useSearchParams()
  const existingJobId = searchParams.get('job')

  const [ndviFile, setNdviFile] = useState(null)
  const [coalFile, setCoalFile] = useState(null)
  const [startyear, setStartyear] = useState(2010)
  const [status, setStatus] = useState({ text: '等待上传文件...', type: 'info' })
  const [processing, setProcessing] = useState(false)
  const [jobId, setJobId] = useState(existingJobId)
  const [bounds, setBounds] = useState(null)
  const [crsInfo, setCrsInfo] = useState(null)
  const [ndviData, setNdviData] = useState(null)
  const [displayMode, setDisplayMode] = useState('vector')
  const [layersLoaded, setLayersLoaded] = useState(false)

  // 加载历史任务详情
  useEffect(() => {
    if (existingJobId) {
      loadExistingJob(existingJobId)
    }
  }, [existingJobId])

  const loadExistingJob = async (id) => {
    setStatus({ text: '加载历史任务...', type: 'loading' })
    try {
      const res = await api.get(`/api/jobs/${id}`)
      const job = res.data
      if (job.bounds) setBounds(job.bounds)
      if (job.crs_info) setCrsInfo(job.crs_info)
      if (job.startyear) setStartyear(job.startyear)
      setStatus({ text: '历史任务加载完成，点击地图查看 NDVI 曲线', type: 'success' })
    } catch (err) {
      setStatus({ text: `加载失败: ${err.response?.data?.error || err.message}`, type: 'error' })
    }
  }

  // 图层加载完成回调
  const handleLayersLoaded = useCallback(() => {
    setLayersLoaded(true)
    // 应用当前的显示模式
    updateDisplayMode(displayMode)
  }, [displayMode])

  // 切换显示模式
  useEffect(() => {
    if (layersLoaded) {
      updateDisplayMode(displayMode)
    }
  }, [displayMode, layersLoaded])

  const updateDisplayMode = (mode) => {
    const vectorLayers = window.vectorLayers || []
    const rasterLayers = window.rasterLayers || []

    if (mode === 'vector') {
      vectorLayers.forEach(l => { if (l) l.visible = l._savedVisible !== false })
      rasterLayers.forEach(l => { if (l) { l._savedVisible = l.visible; l.visible = false } })
    } else {
      rasterLayers.forEach((l, i) => { if (l) l.visible = i === 0 })
      vectorLayers.forEach(l => { if (l) { l._savedVisible = l.visible; l.visible = false } })
    }
  }

  const handleRunDetection = async () => {
    if (!ndviFile || !coalFile) {
      setStatus({ text: '请先选择 NDVI 和裸煤概率文件', type: 'error' })
      return
    }

    setProcessing(true)
    setLayersLoaded(false)
    setStatus({ text: '上传 NDVI 文件 (1/4)...', type: 'loading' })

    try {
      // 上传 NDVI
      const fd1 = new FormData()
      fd1.append('file', ndviFile)
      fd1.append('kind', 'ndvi')
      const up1 = await api.post('/api/upload', fd1)
      const newJobId = up1.data.job_id

      setStatus({ text: '上传裸煤文件 (2/4)...', type: 'loading' })

      // 上传 Coal
      const fd2 = new FormData()
      fd2.append('file', coalFile)
      fd2.append('kind', 'coal')
      fd2.append('job_id', newJobId)
      await api.post('/api/upload', fd2)

      setStatus({ text: '运行检测算法 (3/4)...', type: 'loading' })

      // 运行检测
      const runRes = await api.post('/api/run', { job_id: newJobId, startyear })

      setStatus({ text: '加载结果图层 (4/4)...', type: 'loading' })

      setJobId(newJobId)
      setBounds(runRes.data.bounds)
      setCrsInfo(runRes.data.crs_info)

      setStatus({ text: '检测完成！点击地图查看 NDVI 曲线', type: 'success' })
    } catch (err) {
      console.error('检测失败:', err)
      setStatus({
        text: `错误: ${err.response?.data?.error || err.message}`,
        type: 'error',
      })
    } finally {
      setProcessing(false)
    }
  }

  const handleMapClick = useCallback(async ({ lon, lat, mapPoint }) => {
    if (!jobId) {
      setStatus({ text: '请先运行检测', type: 'warning' })
      return
    }

    // 检查是否在数据范围内
    if (bounds) {
      if (lon < bounds.west || lon > bounds.east || lat < bounds.south || lat > bounds.north) {
        setStatus({ text: '点击位置超出数据范围', type: 'warning' })
        return
      }
    }

    setStatus({ text: '查询像元信息...', type: 'loading' })

    try {
      const res = await api.get('/api/ndvi-timeseries', {
        params: { job_id: jobId, lon, lat, startyear },
      })
      const data = res.data
      setNdviData(data)
      setStatus({ text: '查询成功', type: 'success' })

      // 打开地图弹窗
      openMapPopup(mapPoint, data)
    } catch (err) {
      setStatus({
        text: `查询失败: ${err.response?.data?.error || err.message}`,
        type: 'error',
      })
    }
  }, [jobId, bounds, startyear])

  return (
    <div className="detection-page">
      <div className="detection-sidebar">
        <div className="card">
          <h3>📤 上传数据</h3>
          <FileUpload
            label="NDVI 时序 GeoTIFF (多波段)"
            accept=".tif,.tiff"
            file={ndviFile}
            onChange={setNdviFile}
          />
          <FileUpload
            label="裸煤概率 GeoTIFF"
            accept=".tif,.tiff"
            file={coalFile}
            onChange={setCoalFile}
          />
          <div className="form-group">
            <label>起始年份</label>
            <input
              type="number"
              value={startyear}
              onChange={(e) => setStartyear(Number(e.target.value))}
              min={1990}
              max={2030}
            />
          </div>
          <button
            className="btn-primary btn-full"
            onClick={handleRunDetection}
            disabled={processing || !ndviFile || !coalFile}
          >
            {processing ? '处理中...' : '▶️ 上传并运行检测'}
          </button>
          <div className={`status status-${status.type}`}>{status.text}</div>
        </div>

        {crsInfo && (
          <div className="card">
            <h3>🌐 坐标系统信息</h3>
            <div className="crs-info">
              <div className="crs-row">
                <span className="crs-label">源数据坐标系:</span>
                <span className="crs-value">
                  {crsInfo.epsg ? `EPSG:${crsInfo.epsg}` : crsInfo.crs_string}
                </span>
              </div>
              <div className="crs-row">
                <span className="crs-label">显示坐标系:</span>
                <span className="crs-value">EPSG:3857</span>
              </div>
              {crsInfo.warning && (
                <div className="crs-warning">{crsInfo.warning}</div>
              )}
            </div>
          </div>
        )}

        <div className="card">
          <h3>🗂️ 图层管理</h3>
          {jobId ? (
            <>
              <div className="display-mode-toggle">
                <button
                  className={`mode-btn ${displayMode === 'vector' ? 'active' : ''}`}
                  onClick={() => setDisplayMode('vector')}
                >
                  矢量显示
                </button>
                <button
                  className={`mode-btn ${displayMode === 'raster' ? 'active' : ''}`}
                  onClick={() => setDisplayMode('raster')}
                >
                  栅格显示
                </button>
              </div>
              <div id="layerListDiv" className="layer-list-container"></div>
            </>
          ) : (
            <p className="empty-hint">运行检测后显示图层列表</p>
          )}
        </div>

        <div className="card">
          <h3>📊 NDVI 时间序列</h3>
          <NdviChart data={ndviData} />
        </div>

        <DownloadPanel jobId={jobId} />
      </div>

      <div className="detection-map">
        <MapView
          bounds={bounds}
          jobId={jobId}
          onMapClick={handleMapClick}
          onLayersLoaded={handleLayersLoaded}
        />
      </div>
    </div>
  )
}
