<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { stockApi, quotesApi, newsApi } from '@/services/api'

const { t } = useI18n()
const route = useRoute()
const ticker = route.params.ticker as string

const stock = ref<any>(null)
const quote = ref<any>(null)
const analysis = ref<any>(null)
const history = ref<any[]>([])
const news = ref<any[]>([])
const selectedPeriod = ref('6mo')
const loadingHistory = ref(false)
const loadingNews = ref(false)
const loading = ref(true)
const error = ref<string | null>(null)

// Price targets editing
const editingTargets = ref(false)
const savingTargets = ref(false)
const editTargetBuy = ref<string>('')
const editTargetSell = ref<string>('')
const editNotes = ref<string>('')

// Chart interactivity
const chartContainer = ref<HTMLElement | null>(null)
const hoveredIndex = ref<number | null>(null)
const tooltipX = ref(0)
const tooltipY = ref(0)

const periods = [
  { value: '1mo', label: '1M' },
  { value: '3mo', label: '3M' },
  { value: '6mo', label: '6M' },
  { value: '1y', label: '1A' },
  { value: '2y', label: '2A' },
]

async function loadHistory(period: string) {
  loadingHistory.value = true
  selectedPeriod.value = period
  try {
    const res = await quotesApi.getHistory(ticker, period)
    history.value = res.data.data || []
  } catch (e) {
    history.value = []
  } finally {
    loadingHistory.value = false
  }
}

async function loadNews() {
  loadingNews.value = true
  try {
    const res = await newsApi.getForStock(ticker, 5)
    news.value = res.data.news || []
  } catch (e) {
    news.value = []
  } finally {
    loadingNews.value = false
  }
}

function formatNewsDate(dateStr: string | null): string {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffHours < 1) return t('common.now')
  if (diffHours < 24) return t('common.hoursAgo', { n: diffHours })
  if (diffDays < 7) return t('common.daysAgo', { n: diffDays })
  return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })
}

const chartData = computed(() => {
  if (!history.value.length) return null

  const prices = history.value.map(h => h.close).filter(p => p != null)
  if (!prices.length) return null

  const minPrice = Math.min(...prices)
  const maxPrice = Math.max(...prices)
  const range = maxPrice - minPrice || 1

  const width = 600
  const height = 200
  const padding = 10

  const points = history.value
    .map((h, i) => {
      if (h.close == null) return null
      const x = padding + (i / (history.value.length - 1)) * (width - 2 * padding)
      const y = height - padding - ((h.close - minPrice) / range) * (height - 2 * padding)
      return `${x},${y}`
    })
    .filter(p => p != null)
    .join(' ')

  const firstPrice = prices[0]
  const lastPrice = prices[prices.length - 1]
  const isPositive = lastPrice >= firstPrice

  // Calcular pontos individuais para interatividade
  const dataPoints = history.value
    .map((h, i) => {
      if (h.close == null) return null
      const x = padding + (i / (history.value.length - 1)) * (width - 2 * padding)
      const y = height - padding - ((h.close - minPrice) / range) * (height - 2 * padding)
      return { x, y, index: i }
    })
    .filter(p => p != null) as { x: number; y: number; index: number }[]

  return { points, minPrice, maxPrice, width, height, isPositive, dataPoints, padding }
})

// Dados do ponto hover
const hoveredData = computed(() => {
  if (hoveredIndex.value === null || !history.value.length) return null
  const item = history.value[hoveredIndex.value]
  if (!item) return null

  const firstPrice = history.value[0]?.close
  const change = firstPrice ? item.close - firstPrice : 0
  const changePercent = firstPrice ? (change / firstPrice) * 100 : 0

  return {
    date: item.date,
    close: item.close,
    open: item.open,
    high: item.high,
    low: item.low,
    volume: item.volume,
    change,
    changePercent,
  }
})

function handleChartMouseMove(event: MouseEvent) {
  if (!chartContainer.value || !chartData.value) return

  const rect = chartContainer.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const relativeX = x / rect.width

  // Encontrar o indice mais proximo
  const index = Math.round(relativeX * (history.value.length - 1))
  hoveredIndex.value = Math.max(0, Math.min(index, history.value.length - 1))

  // Posicao do tooltip
  tooltipX.value = x
  tooltipY.value = event.clientY - rect.top
}

function handleChartMouseLeave() {
  hoveredIndex.value = null
}

onMounted(async () => {
  try {
    const [stockRes, analysisRes] = await Promise.all([
      stockApi.get(ticker),
      quotesApi.getAnalysis(ticker).catch(() => null),
    ])
    stock.value = stockRes.data
    if (analysisRes?.data) {
      quote.value = analysisRes.data.quote
      analysis.value = analysisRes.data.analysis
    }
    // Carregar historico e noticias em paralelo
    await Promise.all([
      loadHistory('6mo'),
      loadNews(),
    ])
  } catch (e) {
    error.value = t('stockDetail.errorLoadingData')
  } finally {
    loading.value = false
  }
})

function getRecommendationBadgeClass(type: string): string {
  switch (type) {
    case 'buy': return 'badge-buy'
    case 'sell': return 'badge-sell'
    case 'hold': return 'badge-hold'
    default: return 'badge-neutral'
  }
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

function formatVolume(value: number | null | undefined): string {
  if (value == null) return '--'
  if (value >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(1)}B`
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`
  return value.toString()
}

function formatMarketCap(value: number | null | undefined): string {
  if (value == null) return '--'
  if (value >= 1_000_000_000_000) return `R$ ${(value / 1_000_000_000_000).toFixed(1)} tri`
  if (value >= 1_000_000_000) return `R$ ${(value / 1_000_000_000).toFixed(1)} bi`
  if (value >= 1_000_000) return `R$ ${(value / 1_000_000).toFixed(1)} mi`
  return formatPrice(value)
}

// Controle de tooltip ativo
const activeTooltip = ref<string | null>(null)

function showTooltip(key: string) {
  activeTooltip.value = key
}

function hideTooltip() {
  activeTooltip.value = null
}

// Helper functions for valuation labels
function getPlLabel(peRatio: number | null | undefined): string {
  if (!peRatio) return t('common.noData')
  if (peRatio < 15) return t('stockDetail.cheap')
  if (peRatio > 25) return t('stockDetail.expensive')
  return t('stockDetail.fair')
}

function getDyLabel(dy: number | null | undefined): string {
  if (!dy) return t('common.noData')
  if (dy > 6) return t('stockDetail.excellent')
  if (dy > 3) return t('stockDetail.good')
  return t('stockDetail.low')
}

function getCapLabel(marketCap: number | null | undefined): string {
  if (!marketCap) return '--'
  if (marketCap > 50000000000) return t('stockDetail.largeCap')
  if (marketCap > 10000000000) return t('stockDetail.midCap')
  return t('stockDetail.smallCap')
}

function getPlSummaryLabel(peRatio: number | null | undefined): string {
  if (!peRatio) return t('common.noData')
  if (peRatio < 15) return t('stockDetail.attractive')
  if (peRatio > 25) return t('stockDetail.expensive')
  return t('stockDetail.fair')
}

// Price targets functions
function startEditingTargets() {
  editTargetBuy.value = stock.value?.target_buy_price?.toString() || ''
  editTargetSell.value = stock.value?.target_sell_price?.toString() || ''
  editNotes.value = stock.value?.notes || ''
  editingTargets.value = true
}

function cancelEditingTargets() {
  editingTargets.value = false
}

async function saveTargets() {
  savingTargets.value = true
  try {
    const data: any = {
      target_buy_price: editTargetBuy.value ? parseFloat(editTargetBuy.value) : null,
      target_sell_price: editTargetSell.value ? parseFloat(editTargetSell.value) : null,
      notes: editNotes.value || null,
    }
    const response = await stockApi.update(ticker, data)
    stock.value = response.data
    editingTargets.value = false
  } catch (e) {
    console.error('Error saving targets:', e)
  } finally {
    savingTargets.value = false
  }
}

// Computed for price target analysis
const buyTargetAnalysis = computed(() => {
  if (!stock.value?.target_buy_price || !quote.value?.price) return null
  const target = parseFloat(stock.value.target_buy_price)
  const current = quote.value.price
  const diff = ((current - target) / target) * 100
  return {
    target,
    diff: Math.abs(diff).toFixed(1),
    isBelow: current < target,
    isAbove: current > target,
    isGood: current <= target,
  }
})

const sellTargetAnalysis = computed(() => {
  if (!stock.value?.target_sell_price || !quote.value?.price) return null
  const target = parseFloat(stock.value.target_sell_price)
  const current = quote.value.price
  const diff = ((current - target) / target) * 100
  return {
    target,
    diff: Math.abs(diff).toFixed(1),
    isBelow: current < target,
    isAbove: current > target,
    isGood: current >= target,
  }
})
</script>

<template>
  <div>
    <div v-if="loading" class="text-center py-12 text-gray-400">
      <div class="flex items-center justify-center gap-2">
        <svg class="animate-spin h-6 w-6 text-primary-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span>{{ t('common.loading') }}</span>
      </div>
    </div>

    <div v-else-if="error" class="text-center py-12 text-red-400">
      {{ error }}
    </div>

    <div v-else-if="stock">
      <!-- Header -->
      <header class="mb-8">
        <RouterLink to="/" class="text-primary-400 hover:text-primary-300 text-sm mb-2 inline-flex items-center gap-1">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
          {{ t('common.back') }}
        </RouterLink>
        <div class="flex items-start justify-between mt-2">
          <div>
            <h1 class="text-4xl font-bold text-white">{{ stock.ticker }}</h1>
            <p class="text-gray-400 mt-1 text-lg">{{ stock.name }}</p>
            <span v-if="stock.sector" class="text-xs bg-gray-700 text-gray-300 px-2 py-1 rounded mt-2 inline-block">
              {{ stock.sector }}
            </span>
          </div>
          <div class="text-right">
            <p class="text-5xl font-bold text-white">{{ formatPrice(quote?.price) }}</p>
            <p
              :class="[
                'text-xl font-medium mt-1',
                quote?.change_percent >= 0 ? 'text-emerald-400' : 'text-red-400',
              ]"
            >
              {{ formatPercent(quote?.change_percent) }}
              <span class="text-gray-500 text-sm">({{ formatPrice(quote?.change) }})</span>
            </p>
          </div>
        </div>
      </header>

      <!-- Price Targets & Notes Card -->
      <div class="card mb-8 border border-gray-700">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-white">{{ t('stockDetail.priceTargets') }}</h3>
          <button
            v-if="!editingTargets"
            @click="startEditingTargets"
            class="text-sm text-primary-400 hover:text-primary-300 transition-colors"
          >
            {{ t('stockDetail.editTargets') }}
          </button>
        </div>

        <!-- View Mode -->
        <div v-if="!editingTargets">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <!-- Buy Target -->
            <div class="p-4 rounded-lg" :class="buyTargetAnalysis?.isGood ? 'bg-emerald-500/10 border border-emerald-500/30' : 'bg-gray-700/50'">
              <p class="text-sm text-gray-400 mb-1">{{ t('stockDetail.targetBuyPrice') }}</p>
              <p class="text-2xl font-bold" :class="buyTargetAnalysis?.isGood ? 'text-emerald-400' : 'text-white'">
                {{ stock.target_buy_price ? formatPrice(parseFloat(stock.target_buy_price)) : t('stockDetail.notDefined') }}
              </p>
              <div v-if="buyTargetAnalysis" class="mt-2">
                <span v-if="buyTargetAnalysis.isGood" class="text-emerald-400 text-sm font-medium">
                  {{ t('stockDetail.goodToBuy') }}
                </span>
                <span v-else-if="buyTargetAnalysis.isAbove" class="text-gray-400 text-sm">
                  {{ t('stockDetail.aboveTarget', { percent: buyTargetAnalysis.diff }) }}
                </span>
              </div>
            </div>

            <!-- Sell Target -->
            <div class="p-4 rounded-lg" :class="sellTargetAnalysis?.isGood ? 'bg-emerald-500/10 border border-emerald-500/30' : 'bg-gray-700/50'">
              <p class="text-sm text-gray-400 mb-1">{{ t('stockDetail.targetSellPrice') }}</p>
              <p class="text-2xl font-bold" :class="sellTargetAnalysis?.isGood ? 'text-emerald-400' : 'text-white'">
                {{ stock.target_sell_price ? formatPrice(parseFloat(stock.target_sell_price)) : t('stockDetail.notDefined') }}
              </p>
              <div v-if="sellTargetAnalysis" class="mt-2">
                <span v-if="sellTargetAnalysis.isGood" class="text-emerald-400 text-sm font-medium">
                  {{ t('stockDetail.goodToSell') }}
                </span>
                <span v-else-if="sellTargetAnalysis.isBelow" class="text-gray-400 text-sm">
                  {{ t('stockDetail.belowTarget', { percent: sellTargetAnalysis.diff }) }}
                </span>
              </div>
            </div>
          </div>

          <!-- Notes -->
          <div class="border-t border-gray-700 pt-4">
            <p class="text-sm text-gray-400 mb-2">{{ t('stockDetail.investmentNotes') }}</p>
            <p v-if="stock.notes" class="text-gray-300 whitespace-pre-wrap">{{ stock.notes }}</p>
            <p v-else class="text-gray-500 italic">{{ t('stockDetail.noNotes') }}</p>
          </div>
        </div>

        <!-- Edit Mode -->
        <div v-else>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label class="block text-sm text-gray-400 mb-1">{{ t('stockDetail.targetBuyPrice') }}</label>
              <input
                v-model="editTargetBuy"
                type="number"
                step="0.01"
                class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:border-primary-500 focus:outline-none"
                placeholder="0.00"
              />
            </div>
            <div>
              <label class="block text-sm text-gray-400 mb-1">{{ t('stockDetail.targetSellPrice') }}</label>
              <input
                v-model="editTargetSell"
                type="number"
                step="0.01"
                class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:border-primary-500 focus:outline-none"
                placeholder="0.00"
              />
            </div>
          </div>
          <div class="mb-4">
            <label class="block text-sm text-gray-400 mb-1">{{ t('stockDetail.investmentNotes') }}</label>
            <textarea
              v-model="editNotes"
              rows="3"
              class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:border-primary-500 focus:outline-none resize-none"
              :placeholder="t('stockDetail.notesPlaceholder')"
            ></textarea>
          </div>
          <div class="flex justify-end gap-3">
            <button
              @click="cancelEditingTargets"
              class="px-4 py-2 text-gray-400 hover:text-white transition-colors"
            >
              {{ t('common.cancel') }}
            </button>
            <button
              @click="saveTargets"
              :disabled="savingTargets"
              class="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors disabled:opacity-50"
            >
              {{ savingTargets ? t('stockDetail.saving') : t('stockDetail.saveTargets') }}
            </button>
          </div>
        </div>
      </div>

      <!-- Analysis Card - Destaque Visual -->
      <div v-if="analysis" class="card mb-8" :class="{
        'border-l-4 border-emerald-500 bg-emerald-500/5': analysis.recommendation_type === 'buy',
        'border-l-4 border-yellow-500 bg-yellow-500/5': analysis.recommendation_type === 'neutral',
        'border-l-4 border-red-500 bg-red-500/5': analysis.recommendation_type === 'hold',
      }">
        <div class="flex items-start justify-between mb-6">
          <div>
            <h2 class="text-lg font-medium text-gray-400 mb-2">{{ t('stockDetail.recommendation') }}</h2>
            <div class="flex items-center gap-4">
              <span :class="['badge text-lg px-4 py-2', getRecommendationBadgeClass(analysis.recommendation_type)]">
                {{ analysis.recommendation }}
              </span>
            </div>
          </div>
          <div class="text-right relative group" @mouseenter="showTooltip('score')" @mouseleave="hideTooltip()">
            <span class="text-sm text-gray-500 flex items-center justify-end gap-1">
              {{ t('stockDetail.buyScore') }}
              <svg class="w-3.5 h-3.5 text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
              </svg>
            </span>
            <p :class="['text-5xl font-bold', getScoreClass(analysis.score)]">
              {{ analysis.score }}
            </p>
            <div v-show="activeTooltip === 'score'" class="absolute z-30 bottom-full right-0 mb-2 w-64 p-3 bg-gray-900 border border-gray-700 rounded-lg shadow-xl text-xs text-gray-300 leading-relaxed text-left">
              {{ t('tooltips.score') }}
              <div class="absolute top-full right-4 w-2 h-2 bg-gray-900 border-r border-b border-gray-700 transform rotate-45 -mt-1"></div>
            </div>
          </div>
        </div>

        <!-- Sinais -->
        <div v-if="analysis.signals?.length" class="border-t border-gray-700 pt-4">
          <h3 class="text-sm font-medium text-gray-400 mb-3">{{ t('stockDetail.indicators') }}</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div
              v-for="(signal, idx) in analysis.signals"
              :key="idx"
              class="flex items-center gap-3 p-2 rounded"
              :class="{
                'bg-emerald-500/10': signal.type === 'positive',
                'bg-yellow-500/10': signal.type === 'warning',
                'bg-blue-500/10': signal.type === 'info',
                'bg-gray-500/10': signal.type === 'neutral',
              }"
            >
              <span
                :class="[
                  'w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold',
                  {
                    'bg-emerald-500/20 text-emerald-400': signal.type === 'positive',
                    'bg-yellow-500/20 text-yellow-400': signal.type === 'warning',
                    'bg-blue-500/20 text-blue-400': signal.type === 'info',
                    'bg-gray-500/20 text-gray-400': signal.type === 'neutral',
                  }
                ]"
              >
                <template v-if="signal.type === 'positive'">+</template>
                <template v-else-if="signal.type === 'warning'">!</template>
                <template v-else-if="signal.type === 'info'">i</template>
                <template v-else>-</template>
              </span>
              <span class="text-gray-300 text-sm">{{ signal.message }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Quote Details -->
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
        <div class="card relative group" @mouseenter="showTooltip('abertura')" @mouseleave="hideTooltip()">
          <p class="text-sm text-gray-500 flex items-center gap-1">
            {{ t('stockDetail.opening') }}
            <svg class="w-3.5 h-3.5 text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
            </svg>
          </p>
          <p class="text-xl font-bold text-white">{{ formatPrice(quote?.open) }}</p>
          <div v-show="activeTooltip === 'abertura'" class="absolute z-30 bottom-full left-0 mb-2 w-64 p-3 bg-gray-900 border border-gray-700 rounded-lg shadow-xl text-xs text-gray-300 leading-relaxed">
            {{ t('tooltips.opening') }}
            <div class="absolute top-full left-4 w-2 h-2 bg-gray-900 border-r border-b border-gray-700 transform rotate-45 -mt-1"></div>
          </div>
        </div>
        <div class="card relative group" @mouseenter="showTooltip('maxima')" @mouseleave="hideTooltip()">
          <p class="text-sm text-gray-500 flex items-center gap-1">
            {{ t('stockDetail.high') }}
            <svg class="w-3.5 h-3.5 text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
            </svg>
          </p>
          <p class="text-xl font-bold text-emerald-400">{{ formatPrice(quote?.high) }}</p>
          <div v-show="activeTooltip === 'maxima'" class="absolute z-30 bottom-full left-0 mb-2 w-64 p-3 bg-gray-900 border border-gray-700 rounded-lg shadow-xl text-xs text-gray-300 leading-relaxed">
            {{ t('tooltips.high') }}
            <div class="absolute top-full left-4 w-2 h-2 bg-gray-900 border-r border-b border-gray-700 transform rotate-45 -mt-1"></div>
          </div>
        </div>
        <div class="card relative group" @mouseenter="showTooltip('minima')" @mouseleave="hideTooltip()">
          <p class="text-sm text-gray-500 flex items-center gap-1">
            {{ t('stockDetail.low') }}
            <svg class="w-3.5 h-3.5 text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
            </svg>
          </p>
          <p class="text-xl font-bold text-red-400">{{ formatPrice(quote?.low) }}</p>
          <div v-show="activeTooltip === 'minima'" class="absolute z-30 bottom-full left-0 mb-2 w-64 p-3 bg-gray-900 border border-gray-700 rounded-lg shadow-xl text-xs text-gray-300 leading-relaxed">
            {{ t('tooltips.low') }}
            <div class="absolute top-full left-4 w-2 h-2 bg-gray-900 border-r border-b border-gray-700 transform rotate-45 -mt-1"></div>
          </div>
        </div>
        <div class="card relative group" @mouseenter="showTooltip('fechAnterior')" @mouseleave="hideTooltip()">
          <p class="text-sm text-gray-500 flex items-center gap-1">
            {{ t('stockDetail.previousClose') }}
            <svg class="w-3.5 h-3.5 text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
            </svg>
          </p>
          <p class="text-xl font-bold text-white">{{ formatPrice(quote?.previous_close) }}</p>
          <div v-show="activeTooltip === 'fechAnterior'" class="absolute z-30 bottom-full left-0 mb-2 w-64 p-3 bg-gray-900 border border-gray-700 rounded-lg shadow-xl text-xs text-gray-300 leading-relaxed">
            {{ t('tooltips.previousClose') }}
            <div class="absolute top-full left-4 w-2 h-2 bg-gray-900 border-r border-b border-gray-700 transform rotate-45 -mt-1"></div>
          </div>
        </div>
        <div class="card relative group" @mouseenter="showTooltip('volume')" @mouseleave="hideTooltip()">
          <p class="text-sm text-gray-500 flex items-center gap-1">
            {{ t('stockDetail.volume') }}
            <svg class="w-3.5 h-3.5 text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
            </svg>
          </p>
          <p class="text-xl font-bold text-white">{{ formatVolume(quote?.volume) }}</p>
          <div v-show="activeTooltip === 'volume'" class="absolute z-30 bottom-full left-0 mb-2 w-64 p-3 bg-gray-900 border border-gray-700 rounded-lg shadow-xl text-xs text-gray-300 leading-relaxed">
            {{ t('tooltips.volume') }}
            <div class="absolute top-full left-4 w-2 h-2 bg-gray-900 border-r border-b border-gray-700 transform rotate-45 -mt-1"></div>
          </div>
        </div>
        <div class="card relative group" @mouseenter="showTooltip('marketCap')" @mouseleave="hideTooltip()">
          <p class="text-sm text-gray-500 flex items-center gap-1">
            {{ t('stockDetail.marketCap') }}
            <svg class="w-3.5 h-3.5 text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
            </svg>
          </p>
          <p class="text-xl font-bold text-white">{{ formatMarketCap(quote?.market_cap) }}</p>
          <div v-show="activeTooltip === 'marketCap'" class="absolute z-30 bottom-full left-0 mb-2 w-64 p-3 bg-gray-900 border border-gray-700 rounded-lg shadow-xl text-xs text-gray-300 leading-relaxed">
            {{ t('tooltips.marketCap') }}
            <div class="absolute top-full left-4 w-2 h-2 bg-gray-900 border-r border-b border-gray-700 transform rotate-45 -mt-1"></div>
          </div>
        </div>
      </div>

      <!-- Indicators -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div class="card relative group" @mouseenter="showTooltip('pl')" @mouseleave="hideTooltip()">
          <p class="text-sm text-gray-500 flex items-center gap-1">
            {{ t('stocks.pl') }}
            <svg class="w-3.5 h-3.5 text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
            </svg>
          </p>
          <p class="text-2xl font-bold" :class="{
            'text-emerald-400': quote?.pe_ratio && quote.pe_ratio < 15,
            'text-yellow-400': quote?.pe_ratio && quote.pe_ratio >= 15 && quote.pe_ratio <= 25,
            'text-red-400': quote?.pe_ratio && quote.pe_ratio > 25,
            'text-white': !quote?.pe_ratio
          }">
            {{ quote?.pe_ratio?.toFixed(1) || '--' }}
          </p>
          <p class="text-xs text-gray-500 mt-1">
            {{ getPlLabel(quote?.pe_ratio) }}
          </p>
          <div v-show="activeTooltip === 'pl'" class="absolute z-30 bottom-full left-0 mb-2 w-72 p-3 bg-gray-900 border border-gray-700 rounded-lg shadow-xl text-xs text-gray-300 leading-relaxed">
            {{ t('tooltips.pl') }}
            <div class="absolute top-full left-4 w-2 h-2 bg-gray-900 border-r border-b border-gray-700 transform rotate-45 -mt-1"></div>
          </div>
        </div>
        <div class="card relative group" @mouseenter="showTooltip('dy')" @mouseleave="hideTooltip()">
          <p class="text-sm text-gray-500 flex items-center gap-1">
            {{ t('stockDetail.dividendYield') }}
            <svg class="w-3.5 h-3.5 text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
            </svg>
          </p>
          <p class="text-2xl font-bold" :class="{ 'text-emerald-400': quote?.dividend_yield > 5, 'text-white': !(quote?.dividend_yield > 5) }">
            {{ quote?.dividend_yield ? `${quote.dividend_yield.toFixed(1)}%` : '--' }}
          </p>
          <p class="text-xs text-gray-500 mt-1">
            {{ getDyLabel(quote?.dividend_yield) }}
          </p>
          <div v-show="activeTooltip === 'dy'" class="absolute z-30 bottom-full left-0 mb-2 w-72 p-3 bg-gray-900 border border-gray-700 rounded-lg shadow-xl text-xs text-gray-300 leading-relaxed">
            {{ t('tooltips.dy') }}
            <div class="absolute top-full left-4 w-2 h-2 bg-gray-900 border-r border-b border-gray-700 transform rotate-45 -mt-1"></div>
          </div>
        </div>
        <div class="card relative group" @mouseenter="showTooltip('min52')" @mouseleave="hideTooltip()">
          <p class="text-sm text-gray-500 flex items-center gap-1">
            {{ t('stockDetail.min52Weeks') }}
            <svg class="w-3.5 h-3.5 text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
            </svg>
          </p>
          <p class="text-2xl font-bold text-red-400">{{ formatPrice(quote?.fifty_two_week_low) }}</p>
          <div v-show="activeTooltip === 'min52'" class="absolute z-30 bottom-full left-0 mb-2 w-64 p-3 bg-gray-900 border border-gray-700 rounded-lg shadow-xl text-xs text-gray-300 leading-relaxed">
            {{ t('tooltips.min52') }}
            <div class="absolute top-full left-4 w-2 h-2 bg-gray-900 border-r border-b border-gray-700 transform rotate-45 -mt-1"></div>
          </div>
        </div>
        <div class="card relative group" @mouseenter="showTooltip('max52')" @mouseleave="hideTooltip()">
          <p class="text-sm text-gray-500 flex items-center gap-1">
            {{ t('stockDetail.max52Weeks') }}
            <svg class="w-3.5 h-3.5 text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
            </svg>
          </p>
          <p class="text-2xl font-bold text-emerald-400">{{ formatPrice(quote?.fifty_two_week_high) }}</p>
          <div v-show="activeTooltip === 'max52'" class="absolute z-30 bottom-full left-0 mb-2 w-64 p-3 bg-gray-900 border border-gray-700 rounded-lg shadow-xl text-xs text-gray-300 leading-relaxed">
            {{ t('tooltips.max52') }}
            <div class="absolute top-full left-4 w-2 h-2 bg-gray-900 border-r border-b border-gray-700 transform rotate-45 -mt-1"></div>
          </div>
        </div>
      </div>

      <!-- Price Position Bar -->
      <div v-if="quote?.fifty_two_week_low && quote?.fifty_two_week_high" class="card mb-8 relative">
        <h3 class="text-lg font-semibold mb-4 text-white flex items-center gap-2 group" @mouseenter="showTooltip('range52')" @mouseleave="hideTooltip()">
          {{ t('stockDetail.positionIn52WeekRange') }}
          <svg class="w-4 h-4 text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity cursor-help" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
          </svg>
          <div v-show="activeTooltip === 'range52'" class="absolute z-30 top-10 left-0 w-72 p-3 bg-gray-900 border border-gray-700 rounded-lg shadow-xl text-xs text-gray-300 leading-relaxed font-normal">
            {{ t('tooltips.range52') }}
          </div>
        </h3>
        <div class="relative h-8">
          <div class="absolute inset-0 h-3 top-1/2 -translate-y-1/2 bg-gradient-to-r from-red-500/30 via-yellow-500/30 to-emerald-500/30 rounded-full"></div>
          <div
            class="absolute top-1/2 -translate-y-1/2 w-5 h-5 bg-primary-500 rounded-full border-2 border-white shadow-lg transform -translate-x-1/2 z-10"
            :style="{
              left: `${Math.min(Math.max(((quote.price - quote.fifty_two_week_low) / (quote.fifty_two_week_high - quote.fifty_two_week_low)) * 100, 0), 100)}%`
            }"
          ></div>
        </div>
        <div class="flex justify-between mt-3 text-sm">
          <span class="text-red-400">{{ formatPrice(quote.fifty_two_week_low) }}</span>
          <span class="font-bold text-primary-400">{{ t('stockDetail.currentPrice') }}: {{ formatPrice(quote.price) }}</span>
          <span class="text-emerald-400">{{ formatPrice(quote.fifty_two_week_high) }}</span>
        </div>
        <p class="text-center text-gray-500 text-sm mt-2">
          {{
            ((quote.price - quote.fifty_two_week_low) / (quote.fifty_two_week_high - quote.fifty_two_week_low) * 100).toFixed(0)
          }}{{ t('stockDetail.ofRange') }}
        </p>
      </div>

      <!-- Resumo Rapido -->
      <div class="card mb-8 border border-gray-700">
        <h3 class="text-lg font-semibold mb-4 text-white">{{ t('stockDetail.quickSummary') }}</h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="p-4 rounded-lg" :class="{
            'bg-emerald-500/10 border border-emerald-500/20': quote?.pe_ratio && quote.pe_ratio < 15,
            'bg-yellow-500/10 border border-yellow-500/20': quote?.pe_ratio && quote.pe_ratio >= 15 && quote.pe_ratio <= 25,
            'bg-red-500/10 border border-red-500/20': quote?.pe_ratio && quote.pe_ratio > 25,
            'bg-gray-700/50': !quote?.pe_ratio
          }">
            <p class="text-sm text-gray-400">{{ t('stockDetail.valuation') }}</p>
            <p class="text-lg font-bold text-white">
              {{ getPlSummaryLabel(quote?.pe_ratio) }}
            </p>
          </div>
          <div class="p-4 rounded-lg" :class="{
            'bg-emerald-500/10 border border-emerald-500/20': quote?.dividend_yield > 6,
            'bg-yellow-500/10 border border-yellow-500/20': quote?.dividend_yield > 3 && quote?.dividend_yield <= 6,
            'bg-gray-700/50': !quote?.dividend_yield || quote?.dividend_yield <= 3
          }">
            <p class="text-sm text-gray-400">{{ t('stockDetail.dividends') }}</p>
            <p class="text-lg font-bold text-white">
              {{ getDyLabel(quote?.dividend_yield) }}
            </p>
          </div>
          <div class="p-4 rounded-lg bg-gray-700/50">
            <p class="text-sm text-gray-400">{{ t('stockDetail.marketPosition') }}</p>
            <p class="text-lg font-bold text-white">
              {{ getCapLabel(quote?.market_cap) }}
            </p>
          </div>
        </div>
      </div>

      <!-- Grafico de Historico -->
      <div class="card mb-8">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-white">{{ t('stockDetail.priceHistory') }}</h3>
          <div class="flex gap-2">
            <button
              v-for="p in periods"
              :key="p.value"
              @click="loadHistory(p.value)"
              :class="[
                'px-3 py-1 text-sm rounded-lg transition-colors',
                selectedPeriod === p.value
                  ? 'bg-primary-500 text-white'
                  : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
              ]"
            >
              {{ p.label }}
            </button>
          </div>
        </div>

        <div v-if="loadingHistory" class="h-64 flex items-center justify-center text-gray-400">
          <svg class="animate-spin h-6 w-6 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          {{ t('common.loading') }}
        </div>

        <div
          v-else-if="chartData"
          ref="chartContainer"
          class="relative cursor-crosshair"
          @mousemove="handleChartMouseMove"
          @mouseleave="handleChartMouseLeave"
        >
          <svg :viewBox="`0 0 ${chartData.width} ${chartData.height}`" class="w-full h-64">
            <!-- Grid lines -->
            <line x1="10" y1="10" x2="10" :y2="chartData.height - 10" stroke="#374151" stroke-width="1" />
            <line x1="10" :y1="chartData.height - 10" :x2="chartData.width - 10" :y2="chartData.height - 10" stroke="#374151" stroke-width="1" />

            <!-- Gradient fill -->
            <defs>
              <linearGradient :id="`gradient-${ticker}`" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" :stop-color="chartData.isPositive ? '#10b981' : '#ef4444'" stop-opacity="0.3" />
                <stop offset="100%" :stop-color="chartData.isPositive ? '#10b981' : '#ef4444'" stop-opacity="0" />
              </linearGradient>
            </defs>

            <!-- Area fill -->
            <polygon
              :points="`10,${chartData.height - 10} ${chartData.points} ${chartData.width - 10},${chartData.height - 10}`"
              :fill="`url(#gradient-${ticker})`"
            />

            <!-- Line -->
            <polyline
              :points="chartData.points"
              fill="none"
              :stroke="chartData.isPositive ? '#10b981' : '#ef4444'"
              stroke-width="2"
              stroke-linejoin="round"
              stroke-linecap="round"
            />

            <!-- Hover vertical line -->
            <line
              v-if="hoveredIndex !== null && chartData.dataPoints[hoveredIndex]"
              :x1="chartData.dataPoints[hoveredIndex].x"
              :y1="chartData.padding"
              :x2="chartData.dataPoints[hoveredIndex].x"
              :y2="chartData.height - chartData.padding"
              stroke="#6b7280"
              stroke-width="1"
              stroke-dasharray="4,4"
            />

            <!-- Hover point -->
            <circle
              v-if="hoveredIndex !== null && chartData.dataPoints[hoveredIndex]"
              :cx="chartData.dataPoints[hoveredIndex].x"
              :cy="chartData.dataPoints[hoveredIndex].y"
              r="6"
              :fill="chartData.isPositive ? '#10b981' : '#ef4444'"
              stroke="white"
              stroke-width="2"
            />
          </svg>

          <!-- Tooltip -->
          <div
            v-if="hoveredData"
            class="absolute z-20 pointer-events-none bg-gray-800 border border-gray-600 rounded-lg shadow-xl p-3 min-w-[180px]"
            :style="{
              left: `${Math.min(tooltipX + 15, (chartContainer?.offsetWidth || 500) - 200)}px`,
              top: '10px',
            }"
          >
            <p class="text-gray-400 text-xs mb-1">{{ hoveredData.date }}</p>
            <p class="text-white text-lg font-bold">{{ formatPrice(hoveredData.close) }}</p>
            <p
              :class="[
                'text-sm font-medium',
                hoveredData.changePercent >= 0 ? 'text-emerald-400' : 'text-red-400'
              ]"
            >
              {{ hoveredData.changePercent >= 0 ? '+' : '' }}{{ hoveredData.changePercent.toFixed(2) }}%
              <span class="text-gray-500">({{ formatPrice(hoveredData.change) }})</span>
            </p>
            <div class="mt-2 pt-2 border-t border-gray-700 grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
              <span class="text-gray-500">{{ t('stockDetail.opening') }}</span>
              <span class="text-gray-300 text-right">{{ formatPrice(hoveredData.open) }}</span>
              <span class="text-gray-500">{{ t('stockDetail.high') }}</span>
              <span class="text-emerald-400 text-right">{{ formatPrice(hoveredData.high) }}</span>
              <span class="text-gray-500">{{ t('stockDetail.low') }}</span>
              <span class="text-red-400 text-right">{{ formatPrice(hoveredData.low) }}</span>
              <span class="text-gray-500">{{ t('stockDetail.volume') }}</span>
              <span class="text-gray-300 text-right">{{ formatVolume(hoveredData.volume) }}</span>
            </div>
          </div>

          <!-- Price labels -->
          <div class="absolute top-2 left-4 text-xs text-gray-500">{{ formatPrice(chartData.maxPrice) }}</div>
          <div class="absolute bottom-2 left-4 text-xs text-gray-500">{{ formatPrice(chartData.minPrice) }}</div>

          <!-- Period info -->
          <div class="flex justify-between text-xs text-gray-500 mt-2 px-2">
            <span>{{ history[0]?.date || '' }}</span>
            <span>{{ history.length }} {{ t('stockDetail.days') }}</span>
            <span>{{ history[history.length - 1]?.date || '' }}</span>
          </div>
        </div>

        <div v-else class="h-64 flex items-center justify-center text-gray-500">
          {{ t('stockDetail.noHistoryData') }}
        </div>
      </div>

      <!-- Ultimas Noticias -->
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-white">{{ t('stockDetail.relatedNews') }}</h3>
          <span v-if="news.length && news[0]?.is_market_news" class="text-xs text-gray-500 bg-gray-700 px-2 py-1 rounded">
            {{ t('stockDetail.marketNews') }}
          </span>
        </div>

        <div v-if="loadingNews" class="flex items-center justify-center py-8 text-gray-400">
          <svg class="animate-spin h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          {{ t('stockDetail.searchingNews') }}
        </div>

        <div v-else-if="news.length" class="space-y-4">
          <a
            v-for="(item, idx) in news"
            :key="idx"
            :href="item.url"
            target="_blank"
            rel="noopener noreferrer"
            class="block p-4 rounded-lg bg-gray-800/50 hover:bg-gray-700/50 transition-colors border border-gray-700/50 hover:border-gray-600"
          >
            <div class="flex gap-4">
              <div v-if="item.image" class="flex-shrink-0">
                <img
                  :src="item.image"
                  :alt="item.title"
                  class="w-20 h-20 object-cover rounded-lg"
                  @error="($event.target as HTMLImageElement).style.display = 'none'"
                />
              </div>
              <div class="flex-1 min-w-0">
                <h4 class="text-white font-medium text-sm leading-tight line-clamp-2 mb-1">
                  {{ item.title }}
                </h4>
                <p v-if="item.description" class="text-gray-400 text-xs line-clamp-2 mb-2">
                  {{ item.description }}
                </p>
                <div class="flex items-center gap-3 text-xs text-gray-500">
                  <span class="px-2 py-0.5 bg-gray-700 rounded">{{ item.source }}</span>
                  <span v-if="item.published">{{ formatNewsDate(item.published) }}</span>
                </div>
              </div>
              <div class="flex-shrink-0 self-center">
                <svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </div>
            </div>
          </a>
        </div>

        <div v-else class="py-8 text-center">
          <svg class="w-12 h-12 mx-auto text-gray-600 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
          </svg>
          <p class="text-gray-500 text-sm">{{ t('stockDetail.noNewsFound', { ticker: stock?.ticker }) }}</p>
          <p class="text-gray-600 text-xs mt-1">{{ t('stockDetail.newsFilteredByMentions') }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
