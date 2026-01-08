<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { dividendsApi, type DividendCalendarResponse } from '@/services/api'

const { t, n } = useI18n()
const router = useRouter()

const loading = ref(true)
const error = ref<string | null>(null)
const calendarData = ref<DividendCalendarResponse | null>(null)

const stocksWithDividends = computed(() => {
  if (!calendarData.value) return []
  return calendarData.value.by_stock
    .filter(s => s.dividend_yield || s.history.length > 0)
    .sort((a, b) => (b.dividend_yield || 0) - (a.dividend_yield || 0))
})

const recentDividends = computed(() => {
  if (!calendarData.value) return []
  return calendarData.value.upcoming.filter(d => d.type === 'recent')
})

const upcomingDividends = computed(() => {
  if (!calendarData.value) return []
  return calendarData.value.upcoming.filter(d => d.type === 'upcoming')
})

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr + 'T12:00:00')
  return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

const formatCurrency = (value: number) => {
  return n(value, 'currency', 'pt-BR')
}

const goToStock = (ticker: string) => {
  router.push(`/stocks/${ticker}`)
}

const loadCalendar = async () => {
  loading.value = true
  error.value = null
  try {
    const response = await dividendsApi.getCalendar()
    calendarData.value = response.data
  } catch (err) {
    error.value = t('dividendCalendar.errorLoading')
    console.error('Error loading dividend calendar:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadCalendar()
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-white">{{ t('dividendCalendar.title') }}</h1>
        <p class="text-gray-400 text-sm mt-1">{{ t('dividendCalendar.subtitle') }}</p>
      </div>
      <button
        @click="loadCalendar"
        :disabled="loading"
        class="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors disabled:opacity-50"
      >
        <svg
          class="w-4 h-4"
          :class="{ 'animate-spin': loading }"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        {{ t('common.update') }}
      </button>
    </div>

    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
      <span class="ml-3 text-gray-400">{{ t('dividendCalendar.loading') }}</span>
    </div>

    <div v-else-if="error" class="bg-red-500/10 border border-red-500/30 rounded-xl p-6 text-center">
      <p class="text-red-400">{{ error }}</p>
      <button
        @click="loadCalendar"
        class="mt-4 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors"
      >
        {{ t('common.retry') || 'Tentar novamente' }}
      </button>
    </div>

    <template v-else>
      <div v-if="upcomingDividends.length > 0" class="bg-gray-800/50 rounded-xl border border-gray-700/50 overflow-hidden">
        <div class="p-4 border-b border-gray-700/50">
          <h2 class="text-lg font-semibold text-white flex items-center gap-2">
            <svg class="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            {{ t('dividendCalendar.upcoming') }}
          </h2>
        </div>
        <div class="divide-y divide-gray-700/50">
          <div
            v-for="div in upcomingDividends"
            :key="`${div.ticker}-${div.ex_date}`"
            @click="goToStock(div.ticker)"
            class="p-4 flex items-center justify-between hover:bg-gray-700/30 cursor-pointer transition-colors"
          >
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center">
                <span class="text-green-400 font-bold text-sm">{{ div.ticker.slice(0, 4) }}</span>
              </div>
              <div>
                <p class="font-medium text-white">{{ div.ticker }}</p>
                <p class="text-sm text-gray-400">{{ div.name || t('dividendCalendar.noName') }}</p>
              </div>
            </div>
            <div class="text-right">
              <p class="text-sm text-gray-400">{{ t('dividendCalendar.exDate') }}</p>
              <p class="font-medium text-white">{{ formatDate(div.ex_date) }}</p>
              <p v-if="div.dividend_yield" class="text-xs text-green-400">DY: {{ div.dividend_yield.toFixed(2) }}%</p>
            </div>
          </div>
        </div>
      </div>

      <div v-if="recentDividends.length > 0" class="bg-gray-800/50 rounded-xl border border-gray-700/50 overflow-hidden">
        <div class="p-4 border-b border-gray-700/50">
          <h2 class="text-lg font-semibold text-white flex items-center gap-2">
            <svg class="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {{ t('dividendCalendar.recent') }}
          </h2>
        </div>
        <div class="divide-y divide-gray-700/50">
          <div
            v-for="div in recentDividends"
            :key="`${div.ticker}-${div.ex_date}`"
            @click="goToStock(div.ticker)"
            class="p-4 flex items-center justify-between hover:bg-gray-700/30 cursor-pointer transition-colors"
          >
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                <span class="text-blue-400 font-bold text-sm">{{ div.ticker.slice(0, 4) }}</span>
              </div>
              <div>
                <p class="font-medium text-white">{{ div.ticker }}</p>
                <p class="text-sm text-gray-400">{{ div.name || t('dividendCalendar.noName') }}</p>
              </div>
            </div>
            <div class="text-right">
              <p class="text-sm text-gray-400">{{ formatDate(div.ex_date) }}</p>
              <p v-if="div.value_per_share" class="font-medium text-green-400">
                {{ formatCurrency(div.value_per_share) }}/{{ t('dividendCalendar.share') }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-gray-800/50 rounded-xl border border-gray-700/50 overflow-hidden">
        <div class="p-4 border-b border-gray-700/50">
          <h2 class="text-lg font-semibold text-white flex items-center gap-2">
            <svg class="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
            </svg>
            {{ t('dividendCalendar.topDividendYield') }}
          </h2>
          <p class="text-sm text-gray-400 mt-1">{{ t('dividendCalendar.topDividendYieldDesc') }}</p>
        </div>

        <div v-if="stocksWithDividends.length === 0" class="p-8 text-center">
          <p class="text-gray-400">{{ t('dividendCalendar.noData') }}</p>
        </div>

        <div v-else class="divide-y divide-gray-700/50">
          <div
            v-for="stock in stocksWithDividends.slice(0, 10)"
            :key="stock.ticker"
            @click="goToStock(stock.ticker)"
            class="p-4 flex items-center justify-between hover:bg-gray-700/30 cursor-pointer transition-colors"
          >
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-yellow-500/20 flex items-center justify-center">
                <span class="text-yellow-400 font-bold text-sm">{{ stock.ticker.slice(0, 4) }}</span>
              </div>
              <div>
                <p class="font-medium text-white">{{ stock.ticker }}</p>
                <p class="text-sm text-gray-400">{{ stock.stock_name || stock.name || t('dividendCalendar.noName') }}</p>
              </div>
            </div>
            <div class="text-right">
              <p v-if="stock.dividend_yield" class="font-medium text-green-400 text-lg">
                {{ stock.dividend_yield.toFixed(2) }}%
              </p>
              <p v-else class="text-gray-500">-</p>
              <p class="text-xs text-gray-400">
                {{ stock.history.length }} {{ t('dividendCalendar.paymentsLastYear') }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div v-if="stocksWithDividends.length > 0" class="bg-gray-800/30 rounded-lg p-4 border border-gray-700/30">
        <p class="text-sm text-gray-400 flex items-start gap-2">
          <svg class="w-4 h-4 mt-0.5 flex-shrink-0 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {{ t('dividendCalendar.disclaimer') }}
        </p>
      </div>
    </template>
  </div>
</template>
