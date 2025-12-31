<script setup lang="ts">
import { RouterLink } from 'vue-router'

const navItems = [
  { name: 'Dashboard', path: '/' },
  { name: 'Acoes', path: '/stocks' },
  { name: 'Carteira', path: '/portfolio' },
  { name: 'Alertas', path: '/alerts' },
]
</script>

<template>
  <nav class="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
    <div class="container mx-auto px-4">
      <div class="flex items-center justify-between h-16">
        <RouterLink to="/" class="text-xl font-bold text-primary-500">
          Stock Tracker
        </RouterLink>

        <div class="flex items-center space-x-6">
          <RouterLink
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            class="text-gray-600 dark:text-gray-300 hover:text-primary-500 transition-colors"
            active-class="text-primary-500 font-medium"
          >
            {{ item.name }}
          </RouterLink>
        </div>
      </div>
    </div>
  </nav>
</template>
