<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { usePushNotifications } from '@/composables/usePushNotifications'

const { t } = useI18n()
const {
  isSupported,
  isSubscribed,
  canSubscribe,
  permission,
  loading,
  error,
  subscribe,
  unsubscribe,
  updatePreferences,
} = usePushNotifications()

const prefs = ref({
  notify_price_alerts: true,
  notify_dividends: true,
  notify_news: false,
})

const showPrefs = ref(false)
const testLoading = ref(false)
const testResult = ref<string | null>(null)

async function handleToggle() {
  if (isSubscribed.value) {
    await unsubscribe()
    showPrefs.value = false
  } else {
    const success = await subscribe()
    if (success) {
      showPrefs.value = true
    }
  }
}

async function handlePrefChange() {
  await updatePreferences(prefs.value)
}

async function handleTest() {
  testLoading.value = true
  testResult.value = null
  try {
    const reg = await navigator.serviceWorker.ready
    await reg.showNotification('Teste de Notificacao', {
      body: 'Se voce esta vendo isso, as notificacoes estao funcionando!',
      icon: '/pwa-192x192.png',
      badge: '/pwa-192x192.png',
      tag: 'test-notification',
      data: { type: 'test', url: '/alerts' },
    })
    testResult.value = t('notifications.testSent')
  } catch {
    testResult.value = t('notifications.testFailed')
  } finally {
    testLoading.value = false
    setTimeout(() => {
      testResult.value = null
    }, 5000)
  }
}

watch(isSubscribed, (subscribed) => {
  if (subscribed) {
    showPrefs.value = true
  }
})
</script>

<template>
  <div class="bg-gray-800/50 rounded-xl border border-gray-700/50 overflow-hidden">
    <div class="p-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
            <svg class="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          </div>
          <div>
            <h3 class="font-semibold text-white">{{ t('notifications.title') }}</h3>
            <p class="text-xs text-gray-400">{{ t('notifications.subtitle') }}</p>
          </div>
        </div>

        <div v-if="!isSupported" class="text-xs text-red-400">
          {{ t('notifications.notSupported') }}
        </div>

        <div v-else-if="permission === 'denied'" class="text-xs text-red-400">
          {{ t('notifications.blocked') }}
        </div>

        <button
          v-else
          @click="handleToggle"
          :disabled="loading"
          class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-gray-900"
          :class="isSubscribed ? 'bg-purple-600' : 'bg-gray-600'"
        >
          <span
            class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform"
            :class="isSubscribed ? 'translate-x-6' : 'translate-x-1'"
          />
        </button>
      </div>

      <p v-if="error" class="mt-2 text-xs text-red-400">{{ error }}</p>

      <div v-if="isSubscribed && showPrefs" class="mt-4 pt-4 border-t border-gray-700/50 space-y-3">
        <p class="text-xs text-gray-400 mb-3">{{ t('notifications.prefsTitle') }}</p>

        <label class="flex items-center justify-between cursor-pointer group">
          <div class="flex items-center gap-2">
            <span class="text-lg">🎯</span>
            <span class="text-sm text-gray-300 group-hover:text-white transition-colors">
              {{ t('notifications.priceAlerts') }}
            </span>
          </div>
          <input
            type="checkbox"
            v-model="prefs.notify_price_alerts"
            @change="handlePrefChange"
            class="w-4 h-4 rounded border-gray-600 bg-gray-700 text-purple-600 focus:ring-purple-500 focus:ring-offset-gray-900"
          />
        </label>

        <label class="flex items-center justify-between cursor-pointer group">
          <div class="flex items-center gap-2">
            <span class="text-lg">💰</span>
            <span class="text-sm text-gray-300 group-hover:text-white transition-colors">
              {{ t('notifications.dividends') }}
            </span>
          </div>
          <input
            type="checkbox"
            v-model="prefs.notify_dividends"
            @change="handlePrefChange"
            class="w-4 h-4 rounded border-gray-600 bg-gray-700 text-purple-600 focus:ring-purple-500 focus:ring-offset-gray-900"
          />
        </label>

        <label class="flex items-center justify-between cursor-pointer group">
          <div class="flex items-center gap-2">
            <span class="text-lg">📰</span>
            <span class="text-sm text-gray-300 group-hover:text-white transition-colors">
              {{ t('notifications.news') }}
            </span>
          </div>
          <input
            type="checkbox"
            v-model="prefs.notify_news"
            @change="handlePrefChange"
            class="w-4 h-4 rounded border-gray-600 bg-gray-700 text-purple-600 focus:ring-purple-500 focus:ring-offset-gray-900"
          />
        </label>

        <div class="pt-3 mt-3 border-t border-gray-700/50">
          <button
            @click="handleTest"
            :disabled="testLoading"
            class="w-full py-2 px-4 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-600/50 text-white text-sm font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            <svg v-if="testLoading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>{{ testLoading ? t('notifications.testing') : t('notifications.sendTest') }}</span>
          </button>
          <p v-if="testResult" class="mt-2 text-xs text-center" :class="testResult === t('notifications.testSent') ? 'text-green-400' : 'text-red-400'">
            {{ testResult }}
          </p>
        </div>
      </div>
    </div>

    <div v-if="!isSubscribed && canSubscribe" class="bg-gray-900/30 px-4 py-3 border-t border-gray-700/30">
      <p class="text-xs text-gray-500">
        {{ t('notifications.hint') }}
      </p>
    </div>
  </div>
</template>
