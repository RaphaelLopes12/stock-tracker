<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { usePortfolioStore } from '@/stores/portfolio'
import { stockApi, type TransactionCreate } from '@/services/api'

const { t } = useI18n()

const emit = defineEmits<{
  close: []
  added: []
}>()

const portfolioStore = usePortfolioStore()

// Form state
const ticker = ref('')
const type = ref<'buy' | 'sell'>('buy')
const quantity = ref<number | null>(null)
const price = ref<number | null>(null)
const date = ref(new Date().toISOString().split('T')[0])
const fees = ref<number>(0)
const notes = ref('')

// UI state
const loading = ref(false)
const error = ref<string | null>(null)
const stocks = ref<Array<{ ticker: string; name: string }>>([])
const showSuggestions = ref(false)
const selectedIndex = ref(-1)

// Computed
const filteredStocks = computed(() => {
  if (!ticker.value) return stocks.value.slice(0, 10)
  const search = ticker.value.toUpperCase()
  return stocks.value
    .filter(s => s.ticker.includes(search) || s.name.toUpperCase().includes(search))
    .slice(0, 10)
})

const totalValue = computed(() => {
  if (!quantity.value || !price.value) return 0
  return quantity.value * price.value
})

const canSubmit = computed(() => {
  return (
    ticker.value.trim() !== '' &&
    quantity.value !== null &&
    quantity.value > 0 &&
    price.value !== null &&
    price.value > 0 &&
    date.value !== ''
  )
})

// Load stocks for autocomplete
onMounted(async () => {
  try {
    const response = await stockApi.list(true)
    stocks.value = response.data.map((s: any) => ({ ticker: s.ticker, name: s.name }))
  } catch (e) {
    console.error('Erro ao carregar acoes:', e)
  }
})

// Select stock from suggestions
const selectStock = (stock: { ticker: string; name: string }) => {
  ticker.value = stock.ticker
  showSuggestions.value = false
  selectedIndex.value = -1
}

// Hide suggestions with delay (allows click to register)
const hideSuggestions = () => {
  window.setTimeout(() => {
    showSuggestions.value = false
  }, 200)
}

// Keyboard navigation for suggestions
const handleKeydown = (e: KeyboardEvent) => {
  if (!showSuggestions.value) return

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    selectedIndex.value = Math.min(selectedIndex.value + 1, filteredStocks.value.length - 1)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    selectedIndex.value = Math.max(selectedIndex.value - 1, 0)
  } else if (e.key === 'Enter' && selectedIndex.value >= 0) {
    e.preventDefault()
    selectStock(filteredStocks.value[selectedIndex.value])
  } else if (e.key === 'Escape') {
    showSuggestions.value = false
  }
}

// Submit form
const submit = async () => {
  if (!canSubmit.value) return

  loading.value = true
  error.value = null

  try {
    const data: TransactionCreate = {
      ticker: ticker.value.toUpperCase(),
      type: type.value,
      quantity: quantity.value!,
      price: price.value!,
      date: date.value,
      fees: fees.value,
      notes: notes.value || undefined,
    }

    await portfolioStore.addTransaction(data)
    emit('added')
  } catch (e: any) {
    error.value = e.response?.data?.detail || t('addTransaction.errorRegistering')
  } finally {
    loading.value = false
  }
}

// Format currency input
const formatCurrency = (value: number | null) => {
  if (value === null) return ''
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value)
}
</script>

<template>
  <div
    class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
    @click.self="emit('close')"
  >
    <div class="bg-gray-800 rounded-xl shadow-2xl w-full max-w-md">
      <!-- Header -->
      <div class="flex items-center justify-between p-6 border-b border-gray-700">
        <h2 class="text-xl font-semibold text-white">{{ t('addTransaction.title') }}</h2>
        <button
          @click="emit('close')"
          class="text-gray-400 hover:text-white transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Form -->
      <form @submit.prevent="submit" class="p-6 space-y-4">
        <!-- Error -->
        <div v-if="error" class="bg-red-500/20 border border-red-500/50 text-red-400 px-4 py-3 rounded-lg text-sm">
          {{ error }}
        </div>

        <!-- Type -->
        <div>
          <label class="block text-sm font-medium text-gray-400 mb-2">{{ t('addTransaction.type') }}</label>
          <div class="flex gap-2">
            <button
              type="button"
              @click="type = 'buy'"
              class="flex-1 py-2 px-4 rounded-lg font-medium transition-colors"
              :class="type === 'buy' ? 'bg-emerald-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'"
            >
              {{ t('addTransaction.buy') }}
            </button>
            <button
              type="button"
              @click="type = 'sell'"
              class="flex-1 py-2 px-4 rounded-lg font-medium transition-colors"
              :class="type === 'sell' ? 'bg-red-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'"
            >
              {{ t('addTransaction.sell') }}
            </button>
          </div>
        </div>

        <!-- Ticker -->
        <div class="relative">
          <label class="block text-sm font-medium text-gray-400 mb-2">{{ t('addTransaction.asset') }}</label>
          <input
            v-model="ticker"
            type="text"
            :placeholder="t('addTransaction.assetPlaceholder')"
            class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent uppercase"
            @focus="showSuggestions = true"
            @blur="hideSuggestions"
            @keydown="handleKeydown"
            autocomplete="off"
          />
          <!-- Suggestions dropdown -->
          <div
            v-if="showSuggestions && filteredStocks.length > 0"
            class="absolute z-10 w-full mt-1 bg-gray-700 border border-gray-600 rounded-lg shadow-lg max-h-48 overflow-y-auto"
          >
            <button
              v-for="(stock, index) in filteredStocks"
              :key="stock.ticker"
              type="button"
              class="w-full text-left px-4 py-2 hover:bg-gray-600 transition-colors"
              :class="{ 'bg-gray-600': index === selectedIndex }"
              @click="selectStock(stock)"
            >
              <span class="font-medium text-white">{{ stock.ticker }}</span>
              <span class="text-gray-400 text-sm ml-2">{{ stock.name }}</span>
            </button>
          </div>
        </div>

        <!-- Quantity and Price -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-400 mb-2">{{ t('addTransaction.quantity') }}</label>
            <input
              v-model.number="quantity"
              type="number"
              min="1"
              step="1"
              placeholder="100"
              class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-400 mb-2">{{ t('addTransaction.pricePerUnit') }}</label>
            <input
              v-model.number="price"
              type="number"
              min="0.01"
              step="0.01"
              placeholder="35.50"
              class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
        </div>

        <!-- Total -->
        <div v-if="totalValue > 0" class="bg-gray-700/50 rounded-lg p-3">
          <p class="text-sm text-gray-400">{{ t('addTransaction.totalValue') }}</p>
          <p class="text-xl font-semibold text-white">{{ formatCurrency(totalValue) }}</p>
        </div>

        <!-- Date -->
        <div>
          <label class="block text-sm font-medium text-gray-400 mb-2">{{ t('addTransaction.date') }}</label>
          <input
            v-model="date"
            type="date"
            class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>

        <!-- Fees -->
        <div>
          <label class="block text-sm font-medium text-gray-400 mb-2">{{ t('addTransaction.feesOptional') }}</label>
          <input
            v-model.number="fees"
            type="number"
            min="0"
            step="0.01"
            placeholder="0.00"
            class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>

        <!-- Notes -->
        <div>
          <label class="block text-sm font-medium text-gray-400 mb-2">{{ t('addTransaction.notesOptional') }}</label>
          <textarea
            v-model="notes"
            rows="2"
            :placeholder="t('addTransaction.notesPlaceholder')"
            class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
          ></textarea>
        </div>

        <!-- Actions -->
        <div class="flex gap-3 pt-4">
          <button
            type="button"
            @click="emit('close')"
            class="flex-1 py-2 px-4 bg-gray-700 text-white rounded-lg font-medium hover:bg-gray-600 transition-colors"
          >
            {{ t('common.cancel') }}
          </button>
          <button
            type="submit"
            :disabled="!canSubmit || loading"
            class="flex-1 py-2 px-4 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            :class="type === 'buy' ? 'bg-emerald-600 hover:bg-emerald-700 text-white' : 'bg-red-600 hover:bg-red-700 text-white'"
          >
            <span v-if="loading">{{ t('addTransaction.saving') }}</span>
            <span v-else>{{ type === 'buy' ? t('addTransaction.registerBuy') : t('addTransaction.registerSell') }}</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
