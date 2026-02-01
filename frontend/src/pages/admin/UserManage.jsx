import { useState, useEffect } from 'react'
import api from '../../api/client'

export default function UserManage() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editingUser, setEditingUser] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)

  useEffect(() => {
    loadUsers()
  }, [])

  const loadUsers = async () => {
    try {
      const res = await api.get('/api/admin/users')
      setUsers(res.data.users || [])
    } catch (err) {
      setError(err.response?.data?.error || '加载用户列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleToggleActive = async (user) => {
    if (user.role === 'admin' && user.is_active) {
      alert('不能禁用管理员账户')
      return
    }

    setActionLoading(true)
    try {
      await api.put(`/api/admin/users/${user.id}`, {
        is_active: !user.is_active,
      })
      loadUsers()
    } catch (err) {
      alert(err.response?.data?.error || '操作失败')
    } finally {
      setActionLoading(false)
    }
  }

  const handleChangeRole = async (user, newRole) => {
    setActionLoading(true)
    try {
      await api.put(`/api/admin/users/${user.id}`, { role: newRole })
      loadUsers()
      setEditingUser(null)
    } catch (err) {
      alert(err.response?.data?.error || '操作失败')
    } finally {
      setActionLoading(false)
    }
  }

  const handleDelete = async (user) => {
    if (user.role === 'admin') {
      alert('不能删除管理员账户')
      return
    }

    if (!confirm(`确定要删除用户 "${user.username}" 吗？该用户的所有数据将被删除。`)) {
      return
    }

    setActionLoading(true)
    try {
      await api.delete(`/api/admin/users/${user.id}`)
      loadUsers()
    } catch (err) {
      alert(err.response?.data?.error || '删除失败')
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="admin-page">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>加载中...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="admin-page">
      <div className="page-header">
        <h1>用户管理</h1>
        <p>管理平台用户账户</p>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="card">
        <div className="card-header">
          <h3>用户列表</h3>
          <span className="badge">{users.length} 个用户</span>
        </div>

        <div className="table-container">
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>用户名</th>
                <th>邮箱</th>
                <th>角色</th>
                <th>状态</th>
                <th>注册时间</th>
                <th>最后登录</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {users.map(user => (
                <tr key={user.id} className={!user.is_active ? 'row-disabled' : ''}>
                  <td>{user.id}</td>
                  <td>
                    <strong>{user.username}</strong>
                  </td>
                  <td>{user.email}</td>
                  <td>
                    {editingUser === user.id ? (
                      <select
                        value={user.role}
                        onChange={(e) => handleChangeRole(user, e.target.value)}
                        disabled={actionLoading}
                      >
                        <option value="user">普通用户</option>
                        <option value="admin">管理员</option>
                      </select>
                    ) : (
                      <span
                        className={`role-badge role-${user.role}`}
                        onClick={() => setEditingUser(user.id)}
                        title="点击修改角色"
                      >
                        {user.role === 'admin' ? '管理员' : '普通用户'}
                      </span>
                    )}
                  </td>
                  <td>
                    <span className={`status-badge ${user.is_active ? 'status-active' : 'status-inactive'}`}>
                      {user.is_active ? '启用' : '禁用'}
                    </span>
                  </td>
                  <td>{formatDate(user.created_at)}</td>
                  <td>{formatDate(user.last_login)}</td>
                  <td className="action-cell">
                    <button
                      className={`btn-small ${user.is_active ? 'btn-warning' : 'btn-success'}`}
                      onClick={() => handleToggleActive(user)}
                      disabled={actionLoading || user.role === 'admin'}
                      title={user.role === 'admin' ? '不能禁用管理员' : ''}
                    >
                      {user.is_active ? '禁用' : '启用'}
                    </button>
                    <button
                      className="btn-small btn-danger"
                      onClick={() => handleDelete(user)}
                      disabled={actionLoading || user.role === 'admin'}
                      title={user.role === 'admin' ? '不能删除管理员' : ''}
                    >
                      删除
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}
