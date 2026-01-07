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
  update: (ticker: string, data: Partial<{
    name: string
    sector: string
    is_active: boolean
    target_buy_price: number | null
    target_sell_price: number | null
    notes: string | null
  }>) => api.patch(`/stocks/${ticker}`, data),
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

// Portfolio API (carteira pessoal)
export interface TransactionCreate {
  ticker: string
  type: 'buy' | 'sell'
  quantity: number
  price: number
  date: string
  fees?: number
  notes?: string
}

export interface Transaction {
  id: number
  stock_id: number
  ticker: string
  stock_name: string
  type: 'buy' | 'sell'
  quantity: number
  price: number
  total_value: number
  date: string
  fees: number
  notes: string | null
  created_at: string
}

export interface PortfolioHolding {
  id: number
  stock_id: number
  ticker: string
  stock_name: string
  sector: string | null
  quantity: number
  average_price: number
  first_buy_date: string | null
  notes: string | null
  current_price: number | null
  current_value: number | null
  total_invested: number | null
  gain_loss: number | null
  gain_loss_percent: number | null
  change_today: number | null
}

export interface PortfolioSummary {
  total_invested: number
  current_value: number
  total_gain_loss: number
  total_gain_loss_percent: number
  holdings_count: number
  best_performer: string | null
  worst_performer: string | null
}

export interface PortfolioResponse {
  holdings: PortfolioHolding[]
  summary: PortfolioSummary
}

export interface ImportResult {
  success_count: number
  error_count: number
  skipped_count: number
  errors: string[]
  warnings: string[]
  created_stocks: string[]
}

export interface BenchmarkComparison {
  period: {
    start: string | null
    end: string | null
    days: number
  }
  portfolio: {
    return: number
  }
  benchmarks: {
    ibovespa: {
      return: number | null
      vs_portfolio: number | null
      beats: boolean | null
    }
    cdi: {
      return: number | null
      vs_portfolio: number | null
      beats: boolean | null
      annual_rate: number | null
    }
  }
  summary: {
    best_investment: string
  }
}

export const portfolioApi = {
  get: () => api.get<PortfolioResponse>('/portfolio'),
  getHoldings: () => api.get<PortfolioHolding[]>('/portfolio/holdings'),
  getSummary: () => api.get<PortfolioSummary>('/portfolio/summary'),
  getTransactions: (limit = 50, ticker?: string) =>
    api.get<Transaction[]>('/portfolio/transactions', { params: { limit, ticker } }),
  addTransaction: (data: TransactionCreate) => api.post<Transaction>('/portfolio/transaction', data),
  deleteTransaction: (id: number) => api.delete(`/portfolio/transaction/${id}`),
  getHolding: (id: number) => api.get<PortfolioHolding>(`/portfolio/${id}`),
  getBenchmark: (periodDays = 365) =>
    api.get<BenchmarkComparison>('/portfolio/benchmark', { params: { period_days: periodDays } }),
  importCsv: (file: File, skipDuplicates = true, createMissingStocks = true) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post<ImportResult>('/portfolio/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      params: { skip_duplicates: skipDuplicates, create_missing_stocks: createMissingStocks },
    })
  },
  getImportTemplate: () => api.get('/portfolio/import/template', { responseType: 'blob' }),
}

export interface PushSubscriptionCreate {
  endpoint: string
  keys: {
    p256dh: string
    auth: string
  }
}

export interface PushPreferences {
  notify_price_alerts?: boolean
  notify_dividends?: boolean
  notify_news?: boolean
}

export interface PushSubscriptionResponse {
  id: number
  endpoint: string
  is_active: boolean
  notify_price_alerts: boolean
  notify_dividends: boolean
  notify_news: boolean
  created_at: string
  last_used_at: string | null
}

export const notificationsApi = {
  getVapidKey: () => api.get<{ public_key: string }>('/notifications/vapid-key'),
  subscribe: (data: PushSubscriptionCreate) => api.post<PushSubscriptionResponse>('/notifications/subscribe', data),
  unsubscribe: (endpoint: string) => api.post('/notifications/unsubscribe', null, { params: { endpoint } }),
  getSubscription: (endpoint: string) => api.get<PushSubscriptionResponse>('/notifications/subscription', { params: { endpoint } }),
  updatePreferences: (endpoint: string, prefs: PushPreferences) =>
    api.patch<PushSubscriptionResponse>('/notifications/preferences', prefs, { params: { endpoint } }),
  sendTest: () => api.post<{ sent: number; failed: number }>('/notifications/test'),
}

export interface ReceivedDividendCreate {
  ticker: string
  type: 'dividendo' | 'jcp' | 'bonificacao'
  amount: number
  shares: number
  payment_date: string
  ex_date?: string
  notes?: string
}

export interface ReceivedDividend {
  id: number
  stock_id: number
  ticker: string
  stock_name: string
  type: string
  amount: number
  shares: number
  per_share: number
  payment_date: string
  ex_date: string | null
  notes: string | null
  created_at: string
}

export interface DividendsByStock {
  ticker: string
  stock_name: string
  total_amount: number
  count: number
}

export interface DividendsByYear {
  year: number
  total_amount: number
  count: number
}

export interface DividendsSummary {
  total_amount: number
  total_count: number
  by_stock: DividendsByStock[]
  by_year: DividendsByYear[]
  by_type: Record<string, number>
}

export const dividendsApi = {
  list: (limit = 50, ticker?: string, year?: number) =>
    api.get<ReceivedDividend[]>('/dividends', { params: { limit, ticker, year } }),
  create: (data: ReceivedDividendCreate) => api.post<ReceivedDividend>('/dividends', data),
  delete: (id: number) => api.delete(`/dividends/${id}`),
  getSummary: (year?: number) => api.get<DividendsSummary>('/dividends/summary', { params: { year } }),
}
