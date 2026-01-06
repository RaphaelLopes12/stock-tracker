import { defineStore } from 'pinia'
import { ref } from 'vue'
import { stockApi } from '@/services/api'

export interface Stock {
  id: number
  ticker: string
  name: string
  sector: string | null
  subsector: string | null
  is_active: boolean
  target_buy_price: number | null
  target_sell_price: number | null
  notes: string | null
  created_at: string
  updated_at: string
}

export const useStocksStore = defineStore('stocks', () => {
  const stocks = ref<Stock[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchStocks(activeOnly = true) {
    loading.value = true
    error.value = null
    try {
      const response = await stockApi.list(activeOnly)
      stocks.value = response.data
    } catch (e) {
      error.value = 'Erro ao carregar ações'
      console.error(e)
    } finally {
      loading.value = false
    }
  }

  async function addStock(ticker: string, name: string, sector?: string) {
    loading.value = true
    error.value = null
    try {
      const response = await stockApi.create({ ticker, name, sector })
      stocks.value.push(response.data)
      return response.data
    } catch (e) {
      error.value = 'Erro ao adicionar ação'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function removeStock(ticker: string) {
    loading.value = true
    error.value = null
    try {
      await stockApi.delete(ticker)
      stocks.value = stocks.value.filter((s) => s.ticker !== ticker)
    } catch (e) {
      error.value = 'Erro ao remover ação'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updateStock(ticker: string, data: {
    name?: string
    sector?: string
    is_active?: boolean
    target_buy_price?: number | null
    target_sell_price?: number | null
    notes?: string | null
  }) {
    loading.value = true
    error.value = null
    try {
      const response = await stockApi.update(ticker, data)
      const index = stocks.value.findIndex((s) => s.ticker === ticker)
      if (index !== -1) {
        stocks.value[index] = response.data
      }
      return response.data
    } catch (e) {
      error.value = 'Erro ao atualizar ação'
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    stocks,
    loading,
    error,
    fetchStocks,
    addStock,
    removeStock,
    updateStock,
  }
})
