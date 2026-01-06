import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  portfolioApi,
  type PortfolioHolding,
  type PortfolioSummary,
  type Transaction,
  type TransactionCreate,
} from '@/services/api'

export const usePortfolioStore = defineStore('portfolio', () => {
  // State
  const holdings = ref<PortfolioHolding[]>([])
  const summary = ref<PortfolioSummary | null>(null)
  const transactions = ref<Transaction[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Computed
  const hasHoldings = computed(() => holdings.value.length > 0)

  const totalValue = computed(() => summary.value?.current_value ?? 0)

  const totalGainLoss = computed(() => summary.value?.total_gain_loss ?? 0)

  const totalGainLossPercent = computed(() => summary.value?.total_gain_loss_percent ?? 0)

  const sortedHoldings = computed(() => {
    return [...holdings.value].sort((a, b) => {
      // Ordenar por valor atual (maior primeiro)
      const aValue = a.current_value ?? 0
      const bValue = b.current_value ?? 0
      return bValue - aValue
    })
  })

  // Actions
  async function fetchPortfolio() {
    loading.value = true
    error.value = null
    try {
      const response = await portfolioApi.get()
      holdings.value = response.data.holdings
      summary.value = response.data.summary
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Erro ao carregar portfolio'
      console.error('Erro ao carregar portfolio:', e)
    } finally {
      loading.value = false
    }
  }

  async function fetchTransactions(limit = 50, ticker?: string) {
    loading.value = true
    error.value = null
    try {
      const response = await portfolioApi.getTransactions(limit, ticker)
      transactions.value = response.data
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Erro ao carregar transações'
      console.error('Erro ao carregar transações:', e)
    } finally {
      loading.value = false
    }
  }

  async function addTransaction(data: TransactionCreate) {
    loading.value = true
    error.value = null
    try {
      const response = await portfolioApi.addTransaction(data)
      // Recarregar portfolio e transações
      await Promise.all([fetchPortfolio(), fetchTransactions()])
      return response.data
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Erro ao registrar transação'
      console.error('Erro ao registrar transação:', e)
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteTransaction(id: number) {
    loading.value = true
    error.value = null
    try {
      await portfolioApi.deleteTransaction(id)
      // Recarregar portfolio e transações
      await Promise.all([fetchPortfolio(), fetchTransactions()])
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Erro ao remover transação'
      console.error('Erro ao remover transação:', e)
      throw e
    } finally {
      loading.value = false
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    // State
    holdings,
    summary,
    transactions,
    loading,
    error,
    // Computed
    hasHoldings,
    totalValue,
    totalGainLoss,
    totalGainLossPercent,
    sortedHoldings,
    // Actions
    fetchPortfolio,
    fetchTransactions,
    addTransaction,
    deleteTransaction,
    clearError,
  }
})
