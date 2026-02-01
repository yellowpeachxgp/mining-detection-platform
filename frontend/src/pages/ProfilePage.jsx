import { useState } from 'react'
import api from '../api/client'
import useAuthStore from '../store/authStore'

export default function ProfilePage() {
  const { user, updateUser } = useAuthStore()
  const [email, setEmail] = useState(user?.email || '')
  const [oldPassword, setOldPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [profileMsg, setProfileMsg] = useState({ text: '', type: '' })
  const [passwordMsg, setPasswordMsg] = useState({ text: '', type: '' })
  const [loading, setLoading] = useState(false)

  const handleUpdateProfile = async (e) => {
    e.preventDefault()
    setLoading(true)
    setProfileMsg({ text: '', type: '' })

    try {
      const res = await api.put('/api/user/profile', { email })
      updateUser(res.data.user)
      setProfileMsg({ text: '更新成功', type: 'success' })
    } catch (err) {
      setProfileMsg({
        text: err.response?.data?.error || '更新失败',
        type: 'error',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleChangePassword = async (e) => {
    e.preventDefault()
    setPasswordMsg({ text: '', type: '' })

    if (newPassword !== confirmPassword) {
      setPasswordMsg({ text: '两次输入的密码不一致', type: 'error' })
      return
    }

    if (newPassword.length < 6) {
      setPasswordMsg({ text: '新密码至少需要6个字符', type: 'error' })
      return
    }

    setLoading(true)
    try {
      await api.put('/api/user/password', {
        old_password: oldPassword,
        new_password: newPassword,
      })
      setPasswordMsg({ text: '密码修改成功', type: 'success' })
      setOldPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (err) {
      setPasswordMsg({
        text: err.response?.data?.error || '修改失败',
        type: 'error',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="profile-page">
      <div className="page-header">
        <h1>👤 个人中心</h1>
        <p>管理您的账户信息</p>
      </div>

      <div className="profile-content">
        <div className="card">
          <h3>账户信息</h3>
          <form onSubmit={handleUpdateProfile}>
            <div className="form-group">
              <label>用户名</label>
              <input type="text" value={user?.username || ''} disabled />
              <small className="form-hint">用户名不可修改</small>
            </div>
            <div className="form-group">
              <label>邮箱</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>角色</label>
              <input
                type="text"
                value={user?.role === 'admin' ? '管理员' : '普通用户'}
                disabled
              />
            </div>
            <div className="form-group">
              <label>注册时间</label>
              <input
                type="text"
                value={user?.created_at ? new Date(user.created_at).toLocaleString('zh-CN') : '-'}
                disabled
              />
            </div>
            {profileMsg.text && (
              <div className={`form-message ${profileMsg.type}`}>{profileMsg.text}</div>
            )}
            <button type="submit" className="btn-primary" disabled={loading}>
              保存修改
            </button>
          </form>
        </div>

        <div className="card">
          <h3>修改密码</h3>
          <form onSubmit={handleChangePassword}>
            <div className="form-group">
              <label>当前密码</label>
              <input
                type="password"
                value={oldPassword}
                onChange={(e) => setOldPassword(e.target.value)}
                placeholder="输入当前密码"
              />
            </div>
            <div className="form-group">
              <label>新密码</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="至少6个字符"
              />
            </div>
            <div className="form-group">
              <label>确认新密码</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="再次输入新密码"
              />
            </div>
            {passwordMsg.text && (
              <div className={`form-message ${passwordMsg.type}`}>{passwordMsg.text}</div>
            )}
            <button type="submit" className="btn-primary" disabled={loading}>
              修改密码
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
