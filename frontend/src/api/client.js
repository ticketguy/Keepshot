import axios from 'axios'

const api = axios.create({ baseURL: '/api/v1' })

// Attach JWT from persisted Zustand store
api.interceptors.request.use((config) => {
  try {
    const raw = localStorage.getItem('ks_auth')
    if (raw) {
      const { state } = JSON.parse(raw)
      if (state?.token) config.headers.Authorization = `Bearer ${state.token}`
    }
  } catch (_) {}
  return config
})

// On 401, clear auth and send to login
api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('ks_auth')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// ── Auth ───────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (username, password) => {
    const form = new URLSearchParams({ username, password })
    return api.post('/auth/token', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
  },
  register: (username, password) =>
    api.post('/auth/register', { username, password }),
}

// ── Bookmarks ──────────────────────────────────────────────────────────────────
export const bookmarksApi = {
  list: (params) => api.get('/bookmarks', { params }),
  get: (id) => api.get(`/bookmarks/${id}`),
  create: (data) => api.post('/bookmarks', data),
  update: (id, data) => api.patch(`/bookmarks/${id}`, data),
  delete: (id) => api.delete(`/bookmarks/${id}`),
}

// ── Notifications ──────────────────────────────────────────────────────────────
export const notificationsApi = {
  list: (params) => api.get('/notifications', { params }),
  markRead: (id) => api.patch(`/notifications/${id}`, { read: true }),
  markAllRead: () => api.post('/notifications/mark-all-read'),
  delete: (id) => api.delete(`/notifications/${id}`),
}

export default api
