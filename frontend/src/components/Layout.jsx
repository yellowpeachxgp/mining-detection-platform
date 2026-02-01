import { useEffect, useState, useRef } from 'react'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import useAuthStore from '../store/authStore'

export default function Layout() {
  const { user, isAuthenticated, isLoading, init, logout, isAdmin } = useAuthStore()
  const location = useLocation()
  const navigate = useNavigate()
  const [showDropdown, setShowDropdown] = useState(false)
  const menuRef = useRef(null)

  useEffect(() => {
    init()
  }, [])

  // 点击外部关闭下拉菜单
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>加载中...</p>
      </div>
    )
  }

  const isActive = (path) => location.pathname === path || location.pathname.startsWith(path + '/')

  return (
    <div className="layout">
      <header className="layout-header">
        <Link to="/" className="logo">
          <span className="logo-icon">🌍</span>
          矿区检测平台
        </Link>

        <nav className="nav-menu">
          <Link to="/detect" className={`nav-link ${isActive('/detect') ? 'active' : ''}`}>
            检测分析
          </Link>
          <Link to="/history" className={`nav-link ${isActive('/history') ? 'active' : ''}`}>
            历史记录
          </Link>
          {isAdmin() && (
            <Link to="/admin" className={`nav-link ${isActive('/admin') ? 'active' : ''}`}>
              管理后台
            </Link>
          )}
        </nav>

        <div className="user-menu" ref={menuRef}>
          <button className="user-trigger" onClick={() => setShowDropdown(!showDropdown)}>
            <span className="user-avatar">{user?.username?.[0]?.toUpperCase() || 'U'}</span>
            <div className="user-info">
              <div className="user-name">{user?.username || '用户'}</div>
              <div className="user-role">{user?.role === 'admin' ? '管理员' : '用户'}</div>
            </div>
          </button>
          {showDropdown && (
            <div className="user-dropdown">
              <Link to="/profile" className="dropdown-item" onClick={() => setShowDropdown(false)}>
                个人中心
              </Link>
              <div className="dropdown-divider"></div>
              <button onClick={handleLogout} className="dropdown-item danger">
                退出登录
              </button>
            </div>
          )}
        </div>
      </header>

      <main className="layout-content">
        <Outlet />
      </main>
    </div>
  )
}
