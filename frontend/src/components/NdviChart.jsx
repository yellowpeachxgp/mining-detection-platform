import { useEffect, useRef } from 'react'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

export default function NdviChart({ data }) {
  const chartRef = useRef(null)
  const chartInstance = useRef(null)

  useEffect(() => {
    if (!chartRef.current || !data) return

    if (chartInstance.current) {
      chartInstance.current.destroy()
    }

    const ctx = chartRef.current.getContext('2d')

    const ndvi = data.ndvi.map(v => {
      if (v === null || Number.isNaN(v)) return null
      return Number(v).toFixed(3)
    })

    chartInstance.current = new Chart(ctx, {
      type: 'line',
      data: {
        labels: data.years.map(String),
        datasets: [{
          label: 'NDVI 时间序列',
          data: ndvi,
          spanGaps: true,
          borderColor: '#2563eb',
          backgroundColor: 'rgba(37, 99, 235, 0.1)',
          tension: 0.3,
          pointRadius: 4,
          pointBackgroundColor: '#2563eb',
          pointBorderColor: 'white',
          pointBorderWidth: 2,
          pointHoverRadius: 6,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            display: true,
            labels: { font: { size: 12 }, usePointStyle: true },
          },
          tooltip: {
            backgroundColor: 'rgba(0,0,0,0.8)',
            padding: 10,
          },
        },
        scales: {
          y: {
            min: -0.1,
            max: 1.1,
            title: { display: true, text: 'NDVI 值' },
            grid: { color: 'rgba(0,0,0,0.05)' },
          },
          x: {
            title: { display: true, text: '年份' },
            grid: { color: 'rgba(0,0,0,0.05)' },
          },
        },
      },
    })

    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy()
      }
    }
  }, [data])

  if (!data) {
    return (
      <div className="chart-placeholder">
        <p>点击地图上的任意位置查看该像元的NDVI时间序列曲线</p>
      </div>
    )
  }

  return (
    <div className="chart-container">
      <div className="pixel-info">
        <div><strong>坐标:</strong> {data.lon.toFixed(6)}, {data.lat.toFixed(6)}</div>
        <div>
          <strong>扰动年份:</strong>{' '}
          <span className={data.disturbance_year ? 'text-danger' : 'text-muted'}>
            {data.disturbance_year ?? '无'}
          </span>
        </div>
        <div>
          <strong>恢复年份:</strong>{' '}
          <span className={data.recovery_year ? 'text-success' : 'text-muted'}>
            {data.recovery_year ?? '无'}
          </span>
        </div>
      </div>
      <canvas ref={chartRef} />
    </div>
  )
}
