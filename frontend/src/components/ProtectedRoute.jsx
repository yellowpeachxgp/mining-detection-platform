import { useEffect } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import useAuthStore from '../store/authStore'

export default function ProtectedRoute({ children, adminOnly = false }) {
  const { isAuthenticated, isLoading, init, isAdmin } = useAuthStore()
  const location = useLocation()

  useEffect(() => {
    init()
  }, [])

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>验证身份中...</p>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (adminOnly && !isAdmin()) {
    return <Navigate to="/detect" replace />
  }

  return children
}
