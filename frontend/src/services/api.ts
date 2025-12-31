import axios from 'axios'

// Em produção, usa a URL configurada; em dev, usa o proxy
const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'

const api = axios.create({
  baseURL,
  timeout: 60000, // 60 segundos para cotações em lote
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export default api

// Stock API
export const stockApi = {
  list: (activeOnly = true) => api.get('/stocks', { params: { active_only: activeOnly } }),
  get: (ticker: string) => api.get(`/stocks/${ticker}`),
  create: (data: { ticker: string; name: string; sector?: string }) => api.post('/stocks', data),
  update: (ticker: string, data: Partial<{ name: string; sector: string; is_active: boolean }>) =>
    api.patch(`/stocks/${ticker}`, data),
  delete: (ticker: string) => api.delete(`/stocks/${ticker}`),
}

// Fundamentals API
export const fundamentalsApi = {
  get: (ticker: string, limit = 30) =>
    api.get(`/fundamentals/${ticker}`, { params: { limit } }),
  latest: (ticker: string) => api.get(`/fundamentals/${ticker}/latest`),
}

// Quotes API (cotações em tempo real)
export const quotesApi = {
  getAll: (limit = 20) => api.get('/quotes', { params: { limit } }),
  get: (ticker: string) => api.get(`/quotes/${ticker}`),
  getAnalysis: (ticker: string) => api.get(`/quotes/${ticker}/analysis`),
  getHistory: (ticker: string, period = '6mo') => api.get(`/quotes/${ticker}/history`, { params: { period } }),
  getBySector: (sector: string) => api.get(`/quotes/sector/${sector}`),
}

// News API (noticias do mercado)
export const newsApi = {
  getAll: (limit = 20) => api.get('/news', { params: { limit } }),
  getForStock: (ticker: string, limit = 5) => api.get(`/news/stock/${ticker}`, { params: { limit } }),
  getSummary: () => api.get('/news/summary'),
}

// Alerts API (alertas de preco e indicadores)
export interface AlertCondition {
  operator: 'above' | 'below' | 'change_up' | 'change_down'
  value: number
}

export interface AlertCreate {
  ticker: string
  name?: string
  type: 'price' | 'change_percent' | 'pe_ratio' | 'dividend_yield'
  condition: AlertCondition
  cooldown_hours?: number
}

export interface Alert {
  id: number
  ticker: string
  name: string | null
  type: string
  condition: AlertCondition
  is_active: boolean
  last_triggered_at: string | null
  trigger_count: number
  cooldown_hours: number
  created_at: string
}

export const alertsApi = {
  list: (activeOnly = false) => api.get('/alerts', { params: { active_only: activeOnly } }),
  get: (id: number) => api.get(`/alerts/${id}`),
  getTypes: () => api.get('/alerts/types'),
  getHistory: (limit = 50) => api.get('/alerts/history', { params: { limit } }),
  create: (data: AlertCreate) => api.post('/alerts', data),
  update: (id: number, data: Partial<{ name: string; is_active: boolean; condition: AlertCondition; cooldown_hours: number }>) =>
    api.patch(`/alerts/${id}`, data),
  delete: (id: number) => api.delete(`/alerts/${id}`),
  check: (id: number) => api.post(`/alerts/${id}/check`),
}
