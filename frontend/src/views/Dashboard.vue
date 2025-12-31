<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { quotesApi, newsApi } from '@/services/api'

interface Quote {
  price: number
  change: number
  change_percent: number
  volume: number
  pe_ratio: number | null
  dividend_yield: number | null
  fifty_two_week_high: number | null
  fifty_two_week_low: number | null
}

interface Analysis {
  score: number
  recommendation: string
  recommendation_type: 'buy' | 'hold' | 'neutral' | 'sell'
}

interface StockWithQuote {
  id: number
  ticker: string
  name: string
  sector: string
  quote: Quote | null
  analysis?: Analysis | null
}

interface NewsItem {
  title: string
  description: string
  url: string
  image: string | null
  source: string
  category: string
  published: string
}

interface MarketIndex {
  symbol: string
  name: string
  price: number
  change: number
  change_percent: number
}

const stocks = ref<StockWithQuote[]>([])
const news = ref<NewsItem[]>([])
const marketIndices = ref<MarketIndex[]>([])
const loading = ref(true)
const loadingNews = ref(true)
const error = ref<string | null>(null)
const currentLimit = ref(15)
const lastUpdate = ref<Date | null>(null)

// Computed
const topGainers = computed(() => {
  return stocks.value
    .filter(s => s.quote?.change_percent && s.quote.change_percent > 0)
    .sort((a, b) => (b.quote?.change_percent || 0) - (a.quote?.change_percent || 0))
    .slice(0, 5)
})

const topLosers = computed(() => {
  return stocks.value
    .filter(s => s.quote?.change_percent && s.quote.change_percent < 0)
    .sort((a, b) => (a.quote?.change_percent || 0) - (b.quote?.change_percent || 0))
    .slice(0, 5)
})

const bestToBuy = computed(() => {
  return stocks.value
    .filter(s => s.quote && getScore(s) >= 30)
    .sort((a, b) => getScore(b) - getScore(a))
    .slice(0, 6)
})

const sectors = computed(() => {
  const sectorMap = new Map<string, { count: number; avgChange: number }>()
  stocks.value.forEach(s => {
    if (s.sector && s.quote?.change_percent != null) {
      const existing = sectorMap.get(s.sector) || { count: 0, avgChange: 0 }
      const newCount = existing.count + 1
      const newAvg = (existing.avgChange * existing.count + s.quote.change_percent) / newCount
      sectorMap.set(s.sector, { count: newCount, avgChange: newAvg })
    }
  })
  return Array.from(sectorMap.entries())
    .map(([name, data]) => ({ name, ...data }))
    .sort((a, b) => b.avgChange - a.avgChange)
})

// Auto refresh
let refreshInterval: number | null = null

onMounted(async () => {
  await Promise.all([loadQuotes(), loadNews(), loadMarketSummary()])

  // Auto refresh a cada 5 minutos
  refreshInterval = window.setInterval(() => {
    loadQuotes()
    loadMarketSummary()
  }, 5 * 60 * 1000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})

async function loadQuotes(limit = 15) {
  loading.value = true
  error.value = null
  currentLimit.value = limit
  try {
    const response = await quotesApi.getAll(limit)
    stocks.value = response.data.map((s: StockWithQuote) => ({
      ...s,
      analysis: s.quote ? calculateQuickAnalysis(s.quote) : null
    }))
    lastUpdate.value = new Date()
  } catch (e) {
    error.value = 'Erro ao carregar cotacoes'
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function loadNews() {
  loadingNews.value = true
  try {
    const response = await newsApi.getAll(10)
    news.value = response.data.news || []
  } catch (e) {
    console.error('Erro ao carregar noticias:', e)
  } finally {
    loadingNews.value = false
  }
}

async function loadMarketSummary() {
  try {
    const response = await newsApi.getSummary()
    marketIndices.value = response.data.indices || []
  } catch (e) {
    console.error('Erro ao carregar indices:', e)
  }
}

function calculateQuickAnalysis(quote: Quote): Analysis {
  let score = 0

  if (quote.fifty_two_week_high && quote.fifty_two_week_low) {
    const range = quote.fifty_two_week_high - quote.fifty_two_week_low
    const position = range > 0 ? (quote.price - quote.fifty_two_week_low) / range : 0.5
    if (position < 0.3) score += 20
    else if (position > 0.8) score -= 10
  }

  if (quote.pe_ratio) {
    if (quote.pe_ratio < 8) score += 25
    else if (quote.pe_ratio < 15) score += 10
    else if (quote.pe_ratio > 25) score -= 15
  }

  if (quote.dividend_yield) {
    if (quote.dividend_yield > 6) score += 20
    else if (quote.dividend_yield > 3) score += 5
  }

  let recommendation = 'Neutro'
  let recommendation_type: Analysis['recommendation_type'] = 'neutral'

  if (score >= 30) {
    recommendation = 'Comprar'
    recommendation_type = 'buy'
  } else if (score <= -20) {
    recommendation = 'Cautela'
    recommendation_type = 'hold'
  }

  return { score, recommendation, recommendation_type }
}

function getScore(stock: StockWithQuote): number {
  return stock.analysis?.score || 0
}


function getScoreClass(score: number): string {
  if (score >= 30) return 'text-emerald-400'
  if (score <= -10) return 'text-red-400'
  return 'text-yellow-400'
}

function formatPrice(value: number | null | undefined): string {
  if (value == null) return '--'
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function formatPercent(value: number | null | undefined): string {
  if (value == null) return '--'
  const sign = value >= 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}%`
}


function formatTimeAgo(dateStr: string): string {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (days > 0) return `${days}d atras`
  if (hours > 0) return `${hours}h atras`
  if (minutes > 0) return `${minutes}min atras`
  return 'agora'
}

function loadMore() {
  loadQuotes(currentLimit.value + 15)
}
</script>

<template>
  <div class="space-y-6">
    <!-- Market Ticker Bar -->
    <div class="bg-gray-800/50 backdrop-blur-sm rounded-xl p-4 border border-gray-700/50">
      <div class="flex items-center justify-between flex-wrap gap-4">
        <div class="flex items-center gap-6 overflow-x-auto">
          <div
            v-for="index in marketIndices"
            :key="index.symbol"
            class="flex items-center gap-3 min-w-fit"
          >
            <span class="text-gray-400 text-sm">{{ index.name }}</span>
            <span class="text-white font-semibold">{{ index.price.toLocaleString('pt-BR') }}</span>
            <span
              :class="[
                'text-sm font-medium',
                index.change_percent >= 0 ? 'text-emerald-400' : 'text-red-400'
              ]"
            >
              {{ formatPercent(index.change_percent) }}
            </span>
          </div>
          <div v-if="marketIndices.length === 0" class="text-gray-500 text-sm">
            Carregando indices...
          </div>
        </div>
        <div v-if="lastUpdate" class="text-gray-500 text-xs">
          Atualizado: {{ lastUpdate.toLocaleTimeString('pt-BR') }}
        </div>
      </div>
    </div>

    <!-- Main Grid Layout -->
    <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
      <!-- Left Column - Stocks -->
      <div class="xl:col-span-2 space-y-6">
        <!-- Oportunidades de Compra -->
        <div v-if="bestToBuy.length > 0" class="bg-gradient-to-br from-emerald-900/30 to-gray-800/50 rounded-xl p-5 border border-emerald-500/20">
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-2">
              <div class="w-10 h-10 bg-emerald-500/20 rounded-lg flex items-center justify-center">
                <svg class="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
              <div>
                <h2 class="text-lg font-semibold text-white">Oportunidades</h2>
                <p class="text-xs text-gray-400">Acoes com melhor score</p>
              </div>
            </div>
            <span class="badge badge-buy">{{ bestToBuy.length }} acoes</span>
          </div>

          <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <RouterLink
              v-for="stock in bestToBuy"
              :key="stock.ticker"
              :to="`/stocks/${stock.ticker}`"
              class="group bg-gray-800/50 hover:bg-gray-800 rounded-lg p-4 transition-all hover:scale-[1.02] border border-transparent hover:border-emerald-500/30"
            >
              <div class="flex items-center justify-between mb-2">
                <span class="font-bold text-white group-hover:text-emerald-400 transition-colors">{{ stock.ticker }}</span>
                <span :class="['text-xs px-2 py-0.5 rounded-full', getScoreClass(stock.analysis?.score || 0), 'bg-gray-700/50']">
                  {{ stock.analysis?.score }}
                </span>
              </div>
              <p class="text-xl font-bold text-white mb-1">{{ formatPrice(stock.quote?.price) }}</p>
              <div class="flex items-center justify-between">
                <span :class="stock.quote?.change_percent && stock.quote.change_percent >= 0 ? 'text-emerald-400' : 'text-red-400'" class="text-sm">
                  {{ formatPercent(stock.quote?.change_percent) }}
                </span>
                <span class="text-xs text-gray-500">{{ stock.sector }}</span>
              </div>
            </RouterLink>
          </div>
        </div>

        <!-- Top Movers Row -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Gainers -->
          <div class="bg-gray-800/50 rounded-xl p-5 border border-gray-700/50">
            <div class="flex items-center gap-2 mb-4">
              <div class="w-8 h-8 bg-emerald-500/20 rounded-lg flex items-center justify-center">
                <svg class="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18" />
                </svg>
              </div>
              <h3 class="font-semibold text-white">Maiores Altas</h3>
            </div>
            <div class="space-y-2">
              <RouterLink
                v-for="stock in topGainers"
                :key="stock.ticker"
                :to="`/stocks/${stock.ticker}`"
                class="flex items-center justify-between p-2 rounded-lg hover:bg-gray-700/50 transition-colors"
              >
                <div class="flex items-center gap-3">
                  <span class="font-medium text-white">{{ stock.ticker }}</span>
                  <span class="text-xs text-gray-500 hidden sm:inline">{{ stock.name }}</span>
                </div>
                <span class="text-emerald-400 font-medium">{{ formatPercent(stock.quote?.change_percent) }}</span>
              </RouterLink>
              <div v-if="topGainers.length === 0" class="text-gray-500 text-sm text-center py-4">
                Nenhuma acao em alta
              </div>
            </div>
          </div>

          <!-- Losers -->
          <div class="bg-gray-800/50 rounded-xl p-5 border border-gray-700/50">
            <div class="flex items-center gap-2 mb-4">
              <div class="w-8 h-8 bg-red-500/20 rounded-lg flex items-center justify-center">
                <svg class="w-4 h-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                </svg>
              </div>
              <h3 class="font-semibold text-white">Maiores Baixas</h3>
            </div>
            <div class="space-y-2">
              <RouterLink
                v-for="stock in topLosers"
                :key="stock.ticker"
                :to="`/stocks/${stock.ticker}`"
                class="flex items-center justify-between p-2 rounded-lg hover:bg-gray-700/50 transition-colors"
              >
                <div class="flex items-center gap-3">
                  <span class="font-medium text-white">{{ stock.ticker }}</span>
                  <span class="text-xs text-gray-500 hidden sm:inline">{{ stock.name }}</span>
                </div>
                <span class="text-red-400 font-medium">{{ formatPercent(stock.quote?.change_percent) }}</span>
              </RouterLink>
              <div v-if="topLosers.length === 0" class="text-gray-500 text-sm text-center py-4">
                Nenhuma acao em baixa
              </div>
            </div>
          </div>
        </div>

        <!-- Sectors Performance -->
        <div class="bg-gray-800/50 rounded-xl p-5 border border-gray-700/50">
          <h3 class="font-semibold text-white mb-4">Performance por Setor</h3>
          <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            <div
              v-for="sector in sectors.slice(0, 8)"
              :key="sector.name"
              class="bg-gray-700/30 rounded-lg p-3"
            >
              <p class="text-xs text-gray-400 truncate mb-1">{{ sector.name }}</p>
              <p :class="['font-semibold', sector.avgChange >= 0 ? 'text-emerald-400' : 'text-red-400']">
                {{ formatPercent(sector.avgChange) }}
              </p>
              <p class="text-xs text-gray-500">{{ sector.count }} acoes</p>
            </div>
          </div>
        </div>

        <!-- Stocks Table -->
        <div class="bg-gray-800/50 rounded-xl border border-gray-700/50 overflow-hidden">
          <div class="p-4 border-b border-gray-700/50 flex items-center justify-between">
            <h3 class="font-semibold text-white">Todas as Acoes</h3>
            <button
              @click="() => loadQuotes(currentLimit)"
              class="text-sm text-primary-400 hover:text-primary-300 transition-colors"
              :disabled="loading"
            >
              {{ loading ? 'Atualizando...' : 'Atualizar' }}
            </button>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full">
              <thead class="bg-gray-900/50 text-xs text-gray-400 uppercase">
                <tr>
                  <th class="px-4 py-3 text-left">Acao</th>
                  <th class="px-4 py-3 text-right">Preco</th>
                  <th class="px-4 py-3 text-right">Variacao</th>
                  <th class="px-4 py-3 text-center hidden sm:table-cell">Score</th>
                  <th class="px-4 py-3 text-right hidden md:table-cell">P/L</th>
                  <th class="px-4 py-3 text-right hidden md:table-cell">DY</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-700/50">
                <tr v-if="loading && stocks.length === 0">
                  <td colspan="6" class="px-4 py-8 text-center text-gray-400">
                    <div class="flex items-center justify-center gap-2">
                      <svg class="animate-spin h-5 w-5 text-primary-500" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      <span>Carregando...</span>
                    </div>
                  </td>
                </tr>
                <tr
                  v-for="stock in stocks"
                  :key="stock.ticker"
                  class="hover:bg-gray-700/30 cursor-pointer transition-colors"
                  @click="$router.push(`/stocks/${stock.ticker}`)"
                >
                  <td class="px-4 py-3">
                    <div>
                      <span class="font-medium text-primary-400">{{ stock.ticker }}</span>
                      <p class="text-xs text-gray-500 truncate max-w-[150px]">{{ stock.name }}</p>
                    </div>
                  </td>
                  <td class="px-4 py-3 text-right font-medium text-white">
                    {{ formatPrice(stock.quote?.price) }}
                  </td>
                  <td class="px-4 py-3 text-right">
                    <span :class="stock.quote?.change_percent && stock.quote.change_percent >= 0 ? 'text-emerald-400' : 'text-red-400'" class="font-medium">
                      {{ formatPercent(stock.quote?.change_percent) }}
                    </span>
                  </td>
                  <td class="px-4 py-3 text-center hidden sm:table-cell">
                    <span :class="['font-medium', getScoreClass(stock.analysis?.score || 0)]">
                      {{ stock.analysis?.score || '--' }}
                    </span>
                  </td>
                  <td class="px-4 py-3 text-right text-gray-400 text-sm hidden md:table-cell">
                    {{ stock.quote?.pe_ratio?.toFixed(1) || '--' }}
                  </td>
                  <td class="px-4 py-3 text-right hidden md:table-cell">
                    <span v-if="stock.quote?.dividend_yield" class="text-emerald-400 text-sm">
                      {{ stock.quote.dividend_yield.toFixed(1) }}%
                    </span>
                    <span v-else class="text-gray-500 text-sm">--</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div v-if="stocks.length >= currentLimit" class="p-4 border-t border-gray-700/50 text-center">
            <button @click="loadMore" class="text-primary-400 hover:text-primary-300 text-sm font-medium">
              Carregar mais acoes
            </button>
          </div>
        </div>
      </div>

      <!-- Right Column - News -->
      <div class="space-y-6">
        <!-- News Feed -->
        <div class="bg-gray-800/50 rounded-xl border border-gray-700/50 overflow-hidden">
          <div class="p-4 border-b border-gray-700/50 flex items-center justify-between">
            <div class="flex items-center gap-2">
              <div class="w-8 h-8 bg-blue-500/20 rounded-lg flex items-center justify-center">
                <svg class="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
                </svg>
              </div>
              <h3 class="font-semibold text-white">Noticias do Mercado</h3>
            </div>
            <button
              @click="loadNews"
              class="text-xs text-gray-400 hover:text-white transition-colors"
              :disabled="loadingNews"
            >
              Atualizar
            </button>
          </div>

          <div class="divide-y divide-gray-700/50 max-h-[600px] overflow-y-auto">
            <div v-if="loadingNews" class="p-8 text-center text-gray-400">
              <svg class="animate-spin h-6 w-6 mx-auto mb-2 text-primary-500" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Carregando noticias...
            </div>

            <a
              v-else
              v-for="(item, idx) in news"
              :key="idx"
              :href="item.url"
              target="_blank"
              rel="noopener noreferrer"
              class="block p-4 hover:bg-gray-700/30 transition-colors group"
            >
              <div class="flex gap-3">
                <div v-if="item.image" class="flex-shrink-0">
                  <img
                    :src="item.image"
                    :alt="item.title"
                    class="w-16 h-16 object-cover rounded-lg bg-gray-700"
                    @error="(e: Event) => (e.target as HTMLImageElement).style.display = 'none'"
                  />
                </div>
                <div class="flex-1 min-w-0">
                  <h4 class="text-sm font-medium text-white group-hover:text-primary-400 transition-colors line-clamp-2 mb-1">
                    {{ item.title }}
                  </h4>
                  <p class="text-xs text-gray-400 line-clamp-2 mb-2">{{ item.description }}</p>
                  <div class="flex items-center gap-2 text-xs text-gray-500">
                    <span class="px-2 py-0.5 bg-gray-700/50 rounded">{{ item.source }}</span>
                    <span>{{ formatTimeAgo(item.published) }}</span>
                  </div>
                </div>
              </div>
            </a>

            <div v-if="!loadingNews && news.length === 0" class="p-8 text-center text-gray-500">
              Nenhuma noticia disponivel
            </div>
          </div>
        </div>

        <!-- Quick Stats -->
        <div class="grid grid-cols-2 gap-3">
          <div class="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
            <p class="text-xs text-gray-400 mb-1">Acoes Monitoradas</p>
            <p class="text-2xl font-bold text-white">{{ stocks.length }}</p>
          </div>
          <div class="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
            <p class="text-xs text-gray-400 mb-1">Setores</p>
            <p class="text-2xl font-bold text-white">{{ sectors.length }}</p>
          </div>
          <div class="bg-emerald-500/10 rounded-xl p-4 border border-emerald-500/20">
            <p class="text-xs text-emerald-400 mb-1">Em Alta</p>
            <p class="text-2xl font-bold text-emerald-400">{{ topGainers.length }}</p>
          </div>
          <div class="bg-red-500/10 rounded-xl p-4 border border-red-500/20">
            <p class="text-xs text-red-400 mb-1">Em Baixa</p>
            <p class="text-2xl font-bold text-red-400">{{ topLosers.length }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
