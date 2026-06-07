import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  maxRedirects: 5,
})

/** FastAPI list routes use trailing slash; avoid 307 redirects that break POST/auth. */
const COLLECTION_PATH = /^\/[a-z0-9_-]+$/i

function normalizeCollectionUrl(url: string | undefined): string | undefined {
  if (!url || url.startsWith('http')) return url
  const q = url.indexOf('?')
  const path = q >= 0 ? url.slice(0, q) : url
  const qs = q >= 0 ? url.slice(q) : ''
  if (COLLECTION_PATH.test(path)) {
    return `${path}/${qs}`
  }
  return url
}

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  if (config.url) {
    config.url = normalizeCollectionUrl(config.url)
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      const refresh = localStorage.getItem('refresh_token')
      if (refresh) {
        try {
          const { data } = await axios.post('/api/v1/auth/refresh-token', { refresh_token: refresh })
          localStorage.setItem('access_token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)
          original.headers.Authorization = `Bearer ${data.access_token}`
          return api(original)
        } catch {
          localStorage.clear()
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

export default api
