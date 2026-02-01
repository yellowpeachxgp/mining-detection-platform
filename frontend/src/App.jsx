import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DetectionPage from './pages/DetectionPage'
import HistoryPage from './pages/HistoryPage'
import ProfilePage from './pages/ProfilePage'
import AdminDashboard from './pages/admin/Dashboard'
import AdminUserManage from './pages/admin/UserManage'
import AdminJobManage from './pages/admin/JobManage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* 公开路由 */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* 需要登录的路由 */}
        <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
          <Route path="/detect" element={<DetectionPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/profile" element={<ProfilePage />} />
        </Route>

        {/* 管理员路由 */}
        <Route element={<ProtectedRoute adminOnly><Layout /></ProtectedRoute>}>
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/users" element={<AdminUserManage />} />
          <Route path="/admin/jobs" element={<AdminJobManage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
