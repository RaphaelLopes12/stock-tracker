<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { usePortfolioStore } from '@/stores/portfolio'
import AddTransactionModal from '@/components/AddTransactionModal.vue'
import ImportTransactionsModal from '@/components/ImportTransactionsModal.vue'

const { t } = useI18n()
const store = usePortfolioStore()

const showAddModal = ref(false)
const showImportModal = ref(false)
const showTransactions = ref(false)

// Formatters
const formatCurrency = (value: number | null) => {
  if (value === null || value === undefined) return '--'
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value)
}

const formatPercent = (value: number | null) => {
  if (value === null || value === undefined) return '--'
  const sign = value >= 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}%`
}

const formatDate = (dateStr: string | null) => {
  if (!dateStr) return '--'
  return new Date(dateStr).toLocaleDateString('pt-BR')
}

const formatQuantity = (qty: number) => {
  return new Intl.NumberFormat('pt-BR').format(qty)
}

// Classes dinamicas para cores
const gainLossClass = (value: number | null) => {
  if (value === null || value === undefined) return 'text-gray-400'
  if (value > 0) return 'text-emerald-400'
  if (value < 0) return 'text-red-400'
  return 'text-gray-400'
}

// Benchmark state
const showBenchmark = ref(false)

// Load data
onMounted(async () => {
  await Promise.all([store.fetchPortfolio(), store.fetchTransactions()])
  // Load benchmark after portfolio
  if (store.hasHoldings) {
    store.fetchBenchmark()
  }
})

// Toggle benchmark section
const toggleBenchmark = () => {
  showBenchmark.value = !showBenchmark.value
  if (showBenchmark.value && !store.benchmark) {
    store.fetchBenchmark()
  }
}

// Handle transaction added
const handleTransactionAdded = () => {
  showAddModal.value = false
}

// Handle import completed
const handleImportCompleted = async () => {
  await Promise.all([store.fetchPortfolio(), store.fetchTransactions()])
}

// Toggle transactions section
const toggleTransactions = () => {
  showTransactions.value = !showTransactions.value
}

// Delete transaction with confirmation
const deleteTransaction = async (id: number) => {
  if (confirm(t('portfolio.confirmDeleteTransaction'))) {
    await store.deleteTransaction(id)
  }
}
</script>

<template>
  <div>
    <!-- Header -->
    <header class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100">{{ t('portfolio.title') }}</h1>
        <p class="text-gray-600 dark:text-gray-400 mt-1">{{ t('portfolio.subtitle') }}</p>
      </div>
      <div class="flex items-center gap-3">
        <button @click="showImportModal = true" class="btn btn-secondary flex items-center gap-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
          {{ t('portfolio.importCsv') }}
        </button>
        <button @click="showAddModal = true" class="btn btn-primary">
          {{ t('portfolio.newTransaction') }}
        </button>
      </div>
    </header>

    <!-- Loading -->
    <div v-if="store.loading && !store.hasHoldings" class="text-center py-12 text-gray-400">
      <svg class="animate-spin h-8 w-8 mx-auto mb-2 text-primary-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      {{ t('portfolio.loadingPortfolio') }}
    </div>

    <!-- Empty State -->
    <div v-else-if="!store.hasHoldings && !store.loading" class="card text-center py-12">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mx-auto text-gray-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <h3 class="text-lg font-medium text-gray-300 mb-2">{{ t('portfolio.emptyTitle') }}</h3>
      <p class="text-gray-500 mb-6 max-w-md mx-auto">
        {{ t('portfolio.emptyDescription') }}
      </p>
      <div class="flex items-center justify-center gap-3">
        <button @click="showImportModal = true" class="btn btn-secondary">
          {{ t('portfolio.importCsv') }}
        </button>
        <button @click="showAddModal = true" class="btn btn-primary">
          {{ t('portfolio.registerPurchase') }}
        </button>
      </div>
    </div>

    <!-- Portfolio Content -->
    <template v-else>
      <!-- Summary Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <!-- Total Investido -->
        <div class="bg-gray-800/50 backdrop-blur-sm rounded-xl p-5 border border-gray-700/50">
          <div class="flex items-center gap-3 mb-3">
            <div class="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
              <svg class="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <p class="text-gray-400 text-sm">{{ t('portfolio.totalInvested') }}</p>
          </div>
          <p class="text-2xl font-bold text-white">
            {{ formatCurrency(store.summary?.total_invested ?? 0) }}
          </p>
        </div>

        <!-- Valor Atual -->
        <div class="bg-gray-800/50 backdrop-blur-sm rounded-xl p-5 border border-gray-700/50">
          <div class="flex items-center gap-3 mb-3">
            <div class="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
              <svg class="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <p class="text-gray-400 text-sm">{{ t('portfolio.currentValue') }}</p>
          </div>
          <p class="text-2xl font-bold text-white">
            {{ formatCurrency(store.summary?.current_value ?? 0) }}
          </p>
        </div>

        <!-- Lucro/Prejuizo -->
        <div
          class="backdrop-blur-sm rounded-xl p-5 border"
          :class="(store.summary?.total_gain_loss ?? 0) >= 0
            ? 'bg-emerald-500/10 border-emerald-500/30'
            : 'bg-red-500/10 border-red-500/30'"
        >
          <div class="flex items-center gap-3 mb-3">
            <div
              class="w-10 h-10 rounded-lg flex items-center justify-center"
              :class="(store.summary?.total_gain_loss ?? 0) >= 0 ? 'bg-emerald-500/20' : 'bg-red-500/20'"
            >
              <svg
                v-if="(store.summary?.total_gain_loss ?? 0) >= 0"
                class="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
              <svg
                v-else
                class="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
              </svg>
            </div>
            <p class="text-gray-400 text-sm">{{ t('portfolio.gainLoss') }}</p>
          </div>
          <p class="text-2xl font-bold" :class="gainLossClass(store.summary?.total_gain_loss ?? 0)">
            {{ formatCurrency(store.summary?.total_gain_loss ?? 0) }}
            <span class="text-sm font-normal ml-2">
              ({{ formatPercent(store.summary?.total_gain_loss_percent ?? 0) }})
            </span>
          </p>
        </div>
      </div>

      <!-- Benchmark Comparison Section -->
      <div class="bg-gray-800/50 rounded-xl border border-gray-700/50 overflow-hidden mb-6">
        <button
          @click="toggleBenchmark"
          class="w-full p-4 flex items-center justify-between text-left hover:bg-gray-700/30 transition-colors"
        >
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 bg-indigo-500/20 rounded-lg flex items-center justify-center">
              <svg class="w-4 h-4 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div>
              <h3 class="font-semibold text-white">{{ t('portfolio.benchmarkTitle') }}</h3>
              <p class="text-xs text-gray-400">{{ t('portfolio.benchmarkSubtitle') }}</p>
            </div>
          </div>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-5 w-5 text-gray-400 transition-transform"
            :class="{ 'rotate-180': showBenchmark }"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
          </svg>
        </button>

        <div v-if="showBenchmark" class="border-t border-gray-700/50 p-4">
          <!-- Loading -->
          <div v-if="store.loadingBenchmark" class="text-center py-4 text-gray-400">
            <svg class="animate-spin h-6 w-6 mx-auto mb-2 text-indigo-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ t('portfolio.loadingBenchmark') }}
          </div>

          <!-- Benchmark Content -->
          <div v-else-if="store.benchmark" class="space-y-4">
            <!-- Period Info -->
            <div class="text-xs text-gray-400 text-center">
              {{ t('portfolio.periodDays', { days: store.benchmark.period.days }) }}
            </div>

            <!-- Comparison Cards -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <!-- Portfolio -->
              <div class="bg-gray-900/50 rounded-lg p-4 text-center border border-gray-700/30">
                <p class="text-xs text-gray-400 mb-1">{{ t('portfolio.yourPortfolio') }}</p>
                <p class="text-2xl font-bold" :class="gainLossClass(store.benchmark.portfolio.return)">
                  {{ formatPercent(store.benchmark.portfolio.return) }}
                </p>
              </div>

              <!-- Ibovespa -->
              <div class="bg-gray-900/50 rounded-lg p-4 text-center border border-gray-700/30">
                <p class="text-xs text-gray-400 mb-1">Ibovespa</p>
                <p class="text-2xl font-bold" :class="gainLossClass(store.benchmark.benchmarks.ibovespa.return)">
                  {{ store.benchmark.benchmarks.ibovespa.return !== null ? formatPercent(store.benchmark.benchmarks.ibovespa.return) : '--' }}
                </p>
                <p
                  v-if="store.benchmark.benchmarks.ibovespa.vs_portfolio !== null"
                  class="text-xs mt-1"
                  :class="store.benchmark.benchmarks.ibovespa.beats ? 'text-red-400' : 'text-emerald-400'"
                >
                  {{ store.benchmark.benchmarks.ibovespa.beats ? t('portfolio.losingToBenchmark') : t('portfolio.beatingBenchmark') }}
                  ({{ formatPercent(Math.abs(store.benchmark.benchmarks.ibovespa.vs_portfolio)) }})
                </p>
              </div>

              <!-- CDI -->
              <div class="bg-gray-900/50 rounded-lg p-4 text-center border border-gray-700/30">
                <p class="text-xs text-gray-400 mb-1">CDI</p>
                <p class="text-2xl font-bold" :class="gainLossClass(store.benchmark.benchmarks.cdi.return)">
                  {{ store.benchmark.benchmarks.cdi.return !== null ? formatPercent(store.benchmark.benchmarks.cdi.return) : '--' }}
                </p>
                <p
                  v-if="store.benchmark.benchmarks.cdi.vs_portfolio !== null"
                  class="text-xs mt-1"
                  :class="store.benchmark.benchmarks.cdi.beats ? 'text-red-400' : 'text-emerald-400'"
                >
                  {{ store.benchmark.benchmarks.cdi.beats ? t('portfolio.losingToBenchmark') : t('portfolio.beatingBenchmark') }}
                  ({{ formatPercent(Math.abs(store.benchmark.benchmarks.cdi.vs_portfolio)) }})
                </p>
                <p v-if="store.benchmark.benchmarks.cdi.annual_rate" class="text-xs text-gray-500 mt-1">
                  {{ t('portfolio.annualRate') }}: {{ store.benchmark.benchmarks.cdi.annual_rate }}%
                </p>
              </div>
            </div>

            <!-- Best Investment Summary -->
            <div
              v-if="store.benchmark.summary.best_investment"
              class="text-center py-3 rounded-lg"
              :class="{
                'bg-emerald-500/10 border border-emerald-500/20': store.benchmark.summary.best_investment === 'portfolio',
                'bg-yellow-500/10 border border-yellow-500/20': store.benchmark.summary.best_investment !== 'portfolio'
              }"
            >
              <p class="text-sm">
                <span class="text-gray-400">{{ t('portfolio.bestInvestment') }}:</span>
                <span
                  class="font-semibold ml-1"
                  :class="{
                    'text-emerald-400': store.benchmark.summary.best_investment === 'portfolio',
                    'text-yellow-400': store.benchmark.summary.best_investment !== 'portfolio'
                  }"
                >
                  {{
                    store.benchmark.summary.best_investment === 'portfolio'
                      ? t('portfolio.yourPortfolio')
                      : store.benchmark.summary.best_investment === 'ibovespa'
                        ? 'Ibovespa'
                        : 'CDI'
                  }}
                </span>
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Dica educativa -->
      <div class="card mb-6 bg-blue-500/10 border border-blue-500/20">
        <div class="flex gap-3">
          <div class="flex-shrink-0">
            <svg class="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h3 class="font-medium text-blue-400 mb-1">{{ t('portfolio.tipTitle') }}</h3>
            <p class="text-sm text-gray-400">
              {{ t('portfolio.tipDescription') }}
            </p>
          </div>
        </div>
      </div>

      <!-- Holdings Table -->
      <div class="bg-gray-800/50 rounded-xl border border-gray-700/50 overflow-hidden mb-6">
        <div class="p-4 border-b border-gray-700/50 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 bg-primary-500/20 rounded-lg flex items-center justify-center">
              <svg class="w-4 h-4 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </div>
            <h3 class="font-semibold text-white">{{ t('portfolio.holdings') }}</h3>
          </div>
          <span class="text-xs px-2 py-1 rounded bg-gray-700 text-gray-300">
            {{ t('portfolio.nAssets', { n: store.holdings.length }) }}
          </span>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gray-900/50 text-xs text-gray-400 uppercase">
              <tr>
                <th class="px-4 py-3 text-left">{{ t('portfolio.asset') }}</th>
                <th class="px-4 py-3 text-right">{{ t('portfolio.quantity') }}</th>
                <th class="px-4 py-3 text-right hidden sm:table-cell">{{ t('portfolio.avgPrice') }}</th>
                <th class="px-4 py-3 text-right hidden md:table-cell">{{ t('portfolio.currentPrice') }}</th>
                <th class="px-4 py-3 text-right">{{ t('portfolio.totalValue') }}</th>
                <th class="px-4 py-3 text-right">{{ t('portfolio.result') }}</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-700/50">
              <tr
                v-for="holding in store.sortedHoldings"
                :key="holding.id"
                class="hover:bg-gray-700/30 cursor-pointer transition-colors"
                @click="$router.push(`/stocks/${holding.ticker}`)"
              >
                <!-- Ativo -->
                <td class="px-4 py-4">
                  <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-primary-600 to-primary-800 flex items-center justify-center text-white font-bold text-sm">
                      {{ holding.ticker.slice(0, 2) }}
                    </div>
                    <div>
                      <p class="font-semibold text-primary-400">{{ holding.ticker }}</p>
                      <p class="text-xs text-gray-500 truncate max-w-[150px]">{{ holding.stock_name }}</p>
                    </div>
                  </div>
                </td>

                <!-- Quantidade -->
                <td class="px-4 py-4 text-right text-white font-medium">
                  {{ formatQuantity(holding.quantity) }}
                </td>

                <!-- Preco Medio -->
                <td class="px-4 py-4 text-right text-gray-300 hidden sm:table-cell">
                  {{ formatCurrency(holding.average_price) }}
                </td>

                <!-- Preco Atual -->
                <td class="px-4 py-4 text-right hidden md:table-cell">
                  <span class="text-white">{{ formatCurrency(holding.current_price) }}</span>
                  <span
                    v-if="holding.change_today !== null"
                    class="text-xs ml-1"
                    :class="gainLossClass(holding.change_today)"
                  >
                    {{ formatPercent(holding.change_today) }}
                  </span>
                </td>

                <!-- Valor Total -->
                <td class="px-4 py-4 text-right text-white font-medium">
                  {{ formatCurrency(holding.current_value) }}
                </td>

                <!-- Resultado -->
                <td class="px-4 py-4 text-right">
                  <div :class="gainLossClass(holding.gain_loss)">
                    <span class="font-medium">{{ formatCurrency(holding.gain_loss) }}</span>
                    <span class="text-xs block">{{ formatPercent(holding.gain_loss_percent) }}</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Transactions Section -->
      <div class="bg-gray-800/50 rounded-xl border border-gray-700/50 overflow-hidden">
        <button
          @click="toggleTransactions"
          class="w-full p-4 flex items-center justify-between text-left hover:bg-gray-700/30 transition-colors"
        >
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 bg-yellow-500/20 rounded-lg flex items-center justify-center">
              <svg class="w-4 h-4 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
              </svg>
            </div>
            <h3 class="font-semibold text-white">{{ t('portfolio.transactionHistory') }}</h3>
          </div>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-5 w-5 text-gray-400 transition-transform"
            :class="{ 'rotate-180': showTransactions }"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
          </svg>
        </button>

        <div v-if="showTransactions" class="border-t border-gray-700/50">
          <div v-if="store.transactions.length === 0" class="text-center py-8 text-gray-400">
            {{ t('portfolio.noTransactions') }}
          </div>

          <div v-else class="overflow-x-auto">
            <table class="w-full">
              <thead class="bg-gray-900/50 text-xs text-gray-400 uppercase">
                <tr>
                  <th class="px-4 py-3 text-left">{{ t('portfolio.date') }}</th>
                  <th class="px-4 py-3 text-left">{{ t('portfolio.type') }}</th>
                  <th class="px-4 py-3 text-left">{{ t('portfolio.asset') }}</th>
                  <th class="px-4 py-3 text-right">{{ t('portfolio.quantity') }}</th>
                  <th class="px-4 py-3 text-right hidden sm:table-cell">{{ t('portfolio.unitPrice') }}</th>
                  <th class="px-4 py-3 text-right">{{ t('portfolio.total') }}</th>
                  <th class="px-4 py-3 text-right w-10"></th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-700/50">
                <tr
                  v-for="trans in store.transactions"
                  :key="trans.id"
                  class="hover:bg-gray-700/30 transition-colors"
                >
                  <td class="px-4 py-3 text-gray-300">{{ formatDate(trans.date) }}</td>
                  <td class="px-4 py-3">
                    <span
                      class="text-xs px-2 py-1 rounded font-medium"
                      :class="trans.type === 'buy'
                        ? 'bg-emerald-500/20 text-emerald-400'
                        : 'bg-red-500/20 text-red-400'"
                    >
                      {{ trans.type === 'buy' ? t('portfolio.buy') : t('portfolio.sell') }}
                    </span>
                  </td>
                  <td class="px-4 py-3 text-white font-medium">{{ trans.ticker }}</td>
                  <td class="px-4 py-3 text-right text-white">{{ formatQuantity(trans.quantity) }}</td>
                  <td class="px-4 py-3 text-right text-gray-300 hidden sm:table-cell">{{ formatCurrency(trans.price) }}</td>
                  <td class="px-4 py-3 text-right text-white font-medium">{{ formatCurrency(trans.total_value) }}</td>
                  <td class="px-4 py-3 text-right">
                    <button
                      @click.stop="deleteTransaction(trans.id)"
                      class="p-2 text-gray-500 hover:text-red-400 transition-colors"
                      :title="t('portfolio.removeTransaction')"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
                      </svg>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </template>

    <!-- Add Transaction Modal -->
    <AddTransactionModal
      v-if="showAddModal"
      @close="showAddModal = false"
      @added="handleTransactionAdded"
    />

    <!-- Import Transactions Modal -->
    <ImportTransactionsModal
      v-if="showImportModal"
      @close="showImportModal = false"
      @imported="handleImportCompleted"
    />
  </div>
</template>
