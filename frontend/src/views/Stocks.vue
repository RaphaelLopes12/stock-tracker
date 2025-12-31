<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useStocksStore } from '@/stores/stocks'

const stocksStore = useStocksStore()

const showAddModal = ref(false)
const newStock = ref({ ticker: '', name: '', sector: '' })
const submitting = ref(false)

onMounted(() => {
  stocksStore.fetchStocks()
})

async function handleAddStock() {
  if (!newStock.value.ticker || !newStock.value.name) return

  submitting.value = true
  try {
    await stocksStore.addStock(
      newStock.value.ticker,
      newStock.value.name,
      newStock.value.sector || undefined
    )
    showAddModal.value = false
    newStock.value = { ticker: '', name: '', sector: '' }
  } catch (e) {
    console.error(e)
  } finally {
    submitting.value = false
  }
}

async function handleRemoveStock(ticker: string) {
  if (confirm(`Remover ${ticker}?`)) {
    await stocksStore.removeStock(ticker)
  }
}
</script>

<template>
  <div>
    <header class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100">Ações</h1>
        <p class="text-gray-600 dark:text-gray-400 mt-1">Gerencie as ações que você acompanha</p>
      </div>
      <button @click="showAddModal = true" class="btn btn-primary">
        + Adicionar Ação
      </button>
    </header>

    <!-- Stocks Table -->
    <div class="card overflow-hidden">
      <table class="w-full">
        <thead class="bg-gray-50 dark:bg-gray-800/50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Ticker</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Nome</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Setor</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Ações</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
          <tr v-for="stock in stocksStore.stocks" :key="stock.id" class="hover:bg-gray-50 dark:hover:bg-gray-800/30">
            <td class="px-6 py-4">
              <RouterLink :to="`/stocks/${stock.ticker}`" class="font-bold text-primary-600 dark:text-primary-400 hover:underline">
                {{ stock.ticker }}
              </RouterLink>
            </td>
            <td class="px-6 py-4 text-gray-900 dark:text-gray-100">{{ stock.name }}</td>
            <td class="px-6 py-4 text-gray-500 dark:text-gray-400">{{ stock.sector || '-' }}</td>
            <td class="px-6 py-4">
              <span
                :class="[
                  'text-xs px-2 py-1 rounded',
                  stock.is_active
                    ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400',
                ]"
              >
                {{ stock.is_active ? 'Ativo' : 'Inativo' }}
              </span>
            </td>
            <td class="px-6 py-4 text-right">
              <button
                @click="handleRemoveStock(stock.ticker)"
                class="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300 text-sm"
              >
                Remover
              </button>
            </td>
          </tr>
          <tr v-if="stocksStore.stocks.length === 0">
            <td colspan="5" class="px-6 py-12 text-center text-gray-500 dark:text-gray-400">
              Nenhuma ação cadastrada
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Add Modal -->
    <div
      v-if="showAddModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="showAddModal = false"
    >
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md p-6">
        <h2 class="text-xl font-bold mb-4 text-gray-900 dark:text-gray-100">Adicionar Ação</h2>

        <form @submit.prevent="handleAddStock" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Ticker</label>
            <input
              v-model="newStock.ticker"
              type="text"
              placeholder="Ex: WEGE3"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              required
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome</label>
            <input
              v-model="newStock.name"
              type="text"
              placeholder="Ex: WEG S.A."
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              required
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Setor (opcional)</label>
            <input
              v-model="newStock.sector"
              type="text"
              placeholder="Ex: Bens Industriais"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          <div class="flex justify-end gap-3 pt-4">
            <button type="button" @click="showAddModal = false" class="btn btn-secondary">
              Cancelar
            </button>
            <button type="submit" :disabled="submitting" class="btn btn-primary">
              {{ submitting ? 'Salvando...' : 'Adicionar' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
