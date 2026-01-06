<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { setLocale, getLocale } from '@/locales'

const { t } = useI18n()

const navItems = [
  { key: 'nav.dashboard', path: '/' },
  { key: 'nav.stocks', path: '/stocks' },
  { key: 'nav.portfolio', path: '/portfolio' },
  { key: 'nav.alerts', path: '/alerts' },
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
            {{ t(item.key) }}
          </RouterLink>

          <!-- Language Selector -->
          <div class="relative">
            <button
              @click="showLangMenu = !showLangMenu"
              @blur="setTimeout(() => showLangMenu = false, 150)"
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
</template>
