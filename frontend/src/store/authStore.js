import { create } from 'zustand'
import api from '../api/client'

const useAuthStore = create((set, get) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,

  // 初始化：检查本地存储的 token
  init: async () => {
    const token = localStorage.getItem('access_token')
    if (token) {
      try {
        const res = await api.get('/api/user/profile')
        set({ user: res.data, isAuthenticated: true, isLoading: false })
      } catch (e) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        set({ user: null, isAuthenticated: false, isLoading: false })
      }
    } else {
      set({ isLoading: false })
    }
  },

  // 登录
  login: async (username, password) => {
    const res = await api.post('/api/auth/login', { username, password })
    const { access_token, refresh_token, user } = res.data
    localStorage.setItem('access_token', access_token)
    localStorage.setItem('refresh_token', refresh_token)
    set({ user, isAuthenticated: true })
    return user
  },

  // 注册
  register: async (username, email, password) => {
    const res = await api.post('/api/auth/register', { username, email, password })
    return res.data
  },

  // 登出
  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({ user: null, isAuthenticated: false })
  },

  // 更新用户信息
  updateUser: (user) => {
    set({ user })
  },

  // 判断是否为管理员
  isAdmin: () => {
    const { user } = get()
    return user?.role === 'admin'
  },
}))

export default useAuthStore
