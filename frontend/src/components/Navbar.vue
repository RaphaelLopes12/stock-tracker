<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { setLocale, getLocale } from '@/locales'

const { t } = useI18n()
const route = useRoute()

const navItems = [
  { key: 'nav.dashboard', path: '/', icon: 'home' },
  { key: 'nav.stocks', path: '/stocks', icon: 'chart' },
  { key: 'nav.portfolio', path: '/portfolio', icon: 'wallet' },
  { key: 'nav.alerts', path: '/alerts', icon: 'bell' },
]

const showLangMenu = ref(false)
const currentLocale = ref(getLocale())

const languages = [
  { code: 'pt-BR' as const, flag: '🇧🇷', label: 'PT' },
  { code: 'en' as const, flag: '🇺🇸', label: 'EN' },
  { code: 'es' as const, flag: '🇪🇸', label: 'ES' },
]

function changeLanguage(locale: 'pt-BR' | 'en' | 'es') {
  setLocale(locale)
  currentLocale.value = locale
  showLangMenu.value = false
}

function getCurrentFlag() {
  return languages.find(l => l.code === currentLocale.value)?.flag || '🌐'
}

function handleBlur() {
  window.setTimeout(() => { showLangMenu.value = false }, 150)
}

function isActive(path: string) {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}
</script>

<template>
  <!-- Desktop Navbar -->
  <nav class="hidden md:block bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
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
            {{ t(item.key) }}
          </RouterLink>

          <!-- Language Selector -->
          <div class="relative">
            <button
              @click="showLangMenu = !showLangMenu"
              @blur="handleBlur"
              class="flex items-center gap-1 text-gray-600 dark:text-gray-300 hover:text-primary-500 transition-colors px-2 py-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              :title="t('language.select')"
            >
              <span class="text-lg">{{ getCurrentFlag() }}</span>
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            <div
              v-show="showLangMenu"
              class="absolute right-0 mt-1 w-32 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-50"
            >
              <button
                v-for="lang in languages"
                :key="lang.code"
                @mousedown.prevent="changeLanguage(lang.code)"
                class="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 first:rounded-t-lg last:rounded-b-lg transition-colors"
                :class="{ 'bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400': currentLocale === lang.code }"
              >
                <span>{{ lang.flag }}</span>
                <span>{{ t(`language.${lang.code === 'pt-BR' ? 'ptBR' : lang.code}`) }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </nav>

  <!-- Mobile Header -->
  <header class="md:hidden bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-3">
    <div class="flex items-center justify-between">
      <RouterLink to="/" class="text-lg font-bold text-primary-500">
        Stock Tracker
      </RouterLink>

      <!-- Language Selector Mobile -->
      <div class="relative">
        <button
          @click="showLangMenu = !showLangMenu"
          @blur="handleBlur"
          class="flex items-center gap-1 text-gray-600 dark:text-gray-300 px-2 py-1 rounded-lg"
        >
          <span class="text-lg">{{ getCurrentFlag() }}</span>
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        <div
          v-show="showLangMenu"
          class="absolute right-0 mt-1 w-32 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-50"
        >
          <button
            v-for="lang in languages"
            :key="lang.code"
            @mousedown.prevent="changeLanguage(lang.code)"
            class="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 first:rounded-t-lg last:rounded-b-lg transition-colors"
            :class="{ 'bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400': currentLocale === lang.code }"
          >
            <span>{{ lang.flag }}</span>
            <span>{{ t(`language.${lang.code === 'pt-BR' ? 'ptBR' : lang.code}`) }}</span>
          </button>
        </div>
      </div>
    </div>
  </header>

  <!-- Mobile Bottom Navigation -->
  <nav class="md:hidden fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 z-50 safe-area-bottom">
    <div class="flex items-center justify-around h-16">
      <RouterLink
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="flex flex-col items-center justify-center flex-1 h-full transition-colors"
        :class="isActive(item.path) ? 'text-primary-500' : 'text-gray-500 dark:text-gray-400'"
      >
        <!-- Home Icon -->
        <svg v-if="item.icon === 'home'" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg>
        <!-- Chart Icon -->
        <svg v-else-if="item.icon === 'chart'" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
        </svg>
        <!-- Wallet Icon -->
        <svg v-else-if="item.icon === 'wallet'" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
        </svg>
        <!-- Bell Icon -->
        <svg v-else-if="item.icon === 'bell'" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        <span class="text-xs mt-1">{{ t(item.key) }}</span>
      </RouterLink>
    </div>
  </nav>
</template>

<style scoped>
.safe-area-bottom {
  padding-bottom: env(safe-area-inset-bottom);
}
</style>
