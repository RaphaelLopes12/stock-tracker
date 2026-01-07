<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { stockApi, dividendsApi, type ReceivedDividendCreate } from '@/services/api'

const { t } = useI18n()

const emit = defineEmits<{
  close: []
  added: []
}>()

const ticker = ref('')
const type = ref<'dividendo' | 'jcp' | 'bonificacao'>('dividendo')
const amount = ref<number | null>(null)
const shares = ref<number | null>(null)
const paymentDate = ref(new Date().toISOString().split('T')[0])
const exDate = ref('')
const notes = ref('')

const loading = ref(false)
const error = ref<string | null>(null)
const stocks = ref<Array<{ ticker: string; name: string }>>([])
const showSuggestions = ref(false)
const selectedIndex = ref(-1)

const filteredStocks = computed(() => {
  if (!ticker.value) return stocks.value.slice(0, 10)
  const search = ticker.value.toUpperCase()
  return stocks.value
    .filter(s => s.ticker.includes(search) || s.name.toUpperCase().includes(search))
    .slice(0, 10)
})

const perShare = computed(() => {
  if (!amount.value || !shares.value || shares.value === 0) return null
  return amount.value / shares.value
})

const canSubmit = computed(() => {
  return (
    ticker.value.trim() !== '' &&
    amount.value !== null &&
    amount.value > 0 &&
    shares.value !== null &&
    shares.value > 0 &&
    paymentDate.value !== ''
  )
})

onMounted(async () => {
  try {
    const response = await stockApi.list(true)
    stocks.value = response.data.map((s: any) => ({ ticker: s.ticker, name: s.name }))
  } catch (e) {
    console.error('Erro ao carregar acoes:', e)
  }
})

const selectStock = (stock: { ticker: string; name: string }) => {
  ticker.value = stock.ticker
  showSuggestions.value = false
  selectedIndex.value = -1
}

const hideSuggestions = () => {
  window.setTimeout(() => {
    showSuggestions.value = false
  }, 200)
}

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

const submit = async () => {
  if (!canSubmit.value) return

  loading.value = true
  error.value = null

  try {
    const data: ReceivedDividendCreate = {
      ticker: ticker.value.toUpperCase(),
      type: type.value,
      amount: amount.value!,
      shares: shares.value!,
      payment_date: paymentDate.value,
      ex_date: exDate.value || undefined,
      notes: notes.value || undefined,
    }

    await dividendsApi.create(data)
    emit('added')
  } catch (e: any) {
    error.value = e.response?.data?.detail || t('dividends.errorRegistering')
  } finally {
    loading.value = false
  }
}

const formatCurrency = (value: number | null) => {
  if (value === null) return ''
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value)
}

const typeLabel = (t: string) => {
  const labels: Record<string, string> = {
    dividendo: 'Dividendo',
    jcp: 'JCP',
    bonificacao: 'Bonificação',
  }
  return labels[t] || t
}
</script>

<template>
  <div
    class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
    @click.self="emit('close')"
  >
    <div class="bg-gray-800 rounded-xl shadow-2xl w-full max-w-md">
      <div class="flex items-center justify-between p-6 border-b border-gray-700">
        <h2 class="text-xl font-semibold text-white">{{ t('dividends.addTitle') }}</h2>
        <button
          @click="emit('close')"
          class="text-gray-400 hover:text-white transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <form @submit.prevent="submit" class="p-6 space-y-4">
        <div v-if="error" class="bg-red-500/20 border border-red-500/50 text-red-400 px-4 py-3 rounded-lg text-sm">
          {{ error }}
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-400 mb-2">{{ t('dividends.type') }}</label>
          <div class="flex gap-2">
            <button
              v-for="t in ['dividendo', 'jcp', 'bonificacao'] as const"
              :key="t"
              type="button"
              @click="type = t"
              class="flex-1 py-2 px-3 rounded-lg font-medium transition-colors text-sm"
              :class="type === t ? 'bg-emerald-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'"
            >
              {{ typeLabel(t) }}
            </button>
          </div>
        </div>

        <div class="relative">
          <label class="block text-sm font-medium text-gray-400 mb-2">{{ t('dividends.asset') }}</label>
          <input
            v-model="ticker"
            type="text"
            :placeholder="t('dividends.assetPlaceholder')"
            class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent uppercase"
            @focus="showSuggestions = true"
            @blur="hideSuggestions"
            @keydown="handleKeydown"
            autocomplete="off"
          />
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

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-400 mb-2">{{ t('dividends.totalAmount') }}</label>
            <input
              v-model.number="amount"
              type="number"
              min="0.01"
              step="0.01"
              placeholder="150.00"
              class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-400 mb-2">{{ t('dividends.shares') }}</label>
            <input
              v-model.number="shares"
              type="number"
              min="1"
              step="1"
              placeholder="100"
              class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
        </div>

        <div v-if="perShare !== null" class="bg-gray-700/50 rounded-lg p-3">
          <p class="text-sm text-gray-400">{{ t('dividends.perShare') }}</p>
          <p class="text-lg font-semibold text-emerald-400">{{ formatCurrency(perShare) }}</p>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-400 mb-2">{{ t('dividends.paymentDate') }}</label>
            <input
              v-model="paymentDate"
              type="date"
              class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-400 mb-2">{{ t('dividends.exDateOptional') }}</label>
            <input
              v-model="exDate"
              type="date"
              class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-400 mb-2">{{ t('dividends.notesOptional') }}</label>
          <textarea
            v-model="notes"
            rows="2"
            :placeholder="t('dividends.notesPlaceholder')"
            class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
          ></textarea>
        </div>

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
            class="flex-1 py-2 px-4 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="loading">{{ t('dividends.saving') }}</span>
            <span v-else>{{ t('dividends.register') }}</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
