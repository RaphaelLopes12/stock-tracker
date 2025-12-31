<script setup lang="ts">
import type { Stock } from '@/stores/stocks'

defineProps<{
  stock: Stock
}>()
</script>

<template>
  <RouterLink
    :to="`/stocks/${stock.ticker}`"
    class="card hover:shadow-lg transition-shadow cursor-pointer"
  >
    <div class="flex items-start justify-between">
      <div>
        <h3 class="text-lg font-bold text-gray-900">{{ stock.ticker }}</h3>
        <p class="text-sm text-gray-500 truncate max-w-[200px]">{{ stock.name }}</p>
      </div>
      <span
        v-if="stock.sector"
        class="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded"
      >
        {{ stock.sector }}
      </span>
    </div>

    <div class="mt-4 pt-4 border-t">
      <div class="flex items-baseline justify-between">
        <span class="text-2xl font-bold">R$ --</span>
        <span class="text-sm text-gray-500">--</span>
      </div>
    </div>
  </RouterLink>
</template>
