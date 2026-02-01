import { Link } from 'react-router-dom'
import useAuthStore from '../store/authStore'

export default function LandingPage() {
  const { isAuthenticated } = useAuthStore()

  return (
    <div className="landing-page">
      <header className="landing-header">
        <div className="landing-logo">
          <span className="logo-icon">🌍</span>
          <span className="logo-text">矿区检测平台</span>
        </div>
        <nav className="landing-nav">
          {isAuthenticated ? (
            <Link to="/detect" className="btn-primary">进入系统</Link>
          ) : (
            <>
              <Link to="/login" className="btn-outline">登录</Link>
              <Link to="/register" className="btn-primary">注册</Link>
            </>
          )}
        </nav>
      </header>

      <main className="landing-main">
        <section className="hero">
          <h1>露天矿区损毁与复垦检测平台</h1>
          <p className="hero-subtitle">
            基于 NDVI 时间序列分析和 KNN-DTW 算法，自动识别矿区扰动与植被恢复
          </p>
          <div className="hero-actions">
            {isAuthenticated ? (
              <Link to="/detect" className="btn-large btn-primary">开始检测</Link>
            ) : (
              <>
                <Link to="/register" className="btn-large btn-primary">免费注册</Link>
                <Link to="/login" className="btn-large btn-outline">已有账号</Link>
              </>
            )}
          </div>
        </section>

        <section className="features">
          <div className="feature-card">
            <div className="feature-icon">📊</div>
            <h3>时间序列分析</h3>
            <p>支持多年 NDVI 数据，自动识别扰动和恢复年份</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🗺️</div>
            <h3>空间可视化</h3>
            <p>基于 ArcGIS 的交互式地图，支持矢量和栅格图层叠加</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🤖</div>
            <h3>智能检测</h3>
            <p>KNN-DTW 算法自动分类，配合煤矿分布数据精确定位</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">📥</div>
            <h3>结果导出</h3>
            <p>支持 GeoTIFF 格式下载，方便后续处理和归档</p>
          </div>
        </section>

        <section className="workflow">
          <h2>使用流程</h2>
          <div className="workflow-steps">
            <div className="step">
              <div className="step-number">1</div>
              <h4>上传数据</h4>
              <p>上传 NDVI 时序和裸煤概率 GeoTIFF</p>
            </div>
            <div className="step-arrow">→</div>
            <div className="step">
              <div className="step-number">2</div>
              <h4>运行检测</h4>
              <p>系统自动进行 KNN-DTW 分类</p>
            </div>
            <div className="step-arrow">→</div>
            <div className="step">
              <div className="step-number">3</div>
              <h4>查看结果</h4>
              <p>在地图上查看扰动和恢复区域</p>
            </div>
            <div className="step-arrow">→</div>
            <div className="step">
              <div className="step-number">4</div>
              <h4>下载导出</h4>
              <p>下载 GeoTIFF 结果文件</p>
            </div>
          </div>
        </section>
      </main>

      <footer className="landing-footer">
        <p>© 2026 矿区检测平台 | 技术支持: NDVI + KNN-DTW</p>
      </footer>
    </div>
  )
}
