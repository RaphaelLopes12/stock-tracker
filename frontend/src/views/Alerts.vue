<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { alertsApi, stockApi, type Alert, type AlertCreate } from '@/services/api'
import NotificationSettings from '@/components/NotificationSettings.vue'

const { t } = useI18n()

// Estado
const alerts = ref<Alert[]>([])
const alertTypes = ref<any[]>([])
const stocks = ref<any[]>([])
const loading = ref(true)
const showModal = ref(false)
const submitting = ref(false)
const checkingAlert = ref<number | null>(null)
const checkResult = ref<any>(null)

// Form de novo alerta
const newAlert = ref<{
  ticker: string
  type: string
  operator: string
  value: string
  name: string
}>({
  ticker: '',
  type: 'price',
  operator: 'below',
  value: '',
  name: '',
})

// Tipo selecionado
const selectedType = computed(() => {
  return alertTypes.value.find(t => t.type === newAlert.value.type)
})

// Carregar dados
async function loadData() {
  loading.value = true
  try {
    const [alertsRes, typesRes, stocksRes] = await Promise.all([
      alertsApi.list(),
      alertsApi.getTypes(),
      stockApi.list(),
    ])
    alerts.value = alertsRes.data
    alertTypes.value = typesRes.data.types
    stocks.value = stocksRes.data
  } catch (e) {
    console.error('Erro ao carregar dados:', e)
  } finally {
    loading.value = false
  }
}

// Criar alerta
async function handleCreateAlert() {
  if (!newAlert.value.ticker || !newAlert.value.value) return

  submitting.value = true
  try {
    const data: AlertCreate = {
      ticker: newAlert.value.ticker,
      type: newAlert.value.type as any,
      condition: {
        operator: newAlert.value.operator as any,
        value: parseFloat(newAlert.value.value),
      },
      name: newAlert.value.name || undefined,
    }

    await alertsApi.create(data)
    showModal.value = false
    resetForm()
    await loadData()
  } catch (e: any) {
    alert(e.response?.data?.detail || t('common.error'))
  } finally {
    submitting.value = false
  }
}

// Resetar form
function resetForm() {
  newAlert.value = {
    ticker: '',
    type: 'price',
    operator: 'below',
    value: '',
    name: '',
  }
}

// Toggle ativo/inativo
async function toggleAlert(alert: Alert) {
  try {
    await alertsApi.update(alert.id, { is_active: !alert.is_active })
    await loadData()
  } catch (e) {
    console.error('Erro ao atualizar alerta:', e)
  }
}

// Deletar alerta
async function deleteAlert(alert: Alert) {
  if (!confirm(t('alerts.confirmRemove', { name: alert.name }))) return

  try {
    await alertsApi.delete(alert.id)
    await loadData()
  } catch (e) {
    console.error('Erro ao deletar alerta:', e)
  }
}

// Verificar alerta manualmente
async function checkAlert(alert: Alert) {
  checkingAlert.value = alert.id
  checkResult.value = null
  try {
    const res = await alertsApi.check(alert.id)
    checkResult.value = res.data
  } catch (e: any) {
    checkResult.value = { error: e.response?.data?.detail || t('common.error') }
  } finally {
    checkingAlert.value = null
  }
}

// Formatar tipo para exibicao
function formatAlertType(type: string): string {
  const types: Record<string, string> = {
    price: t('alerts.price'),
    change_percent: t('alerts.variation'),
    pe_ratio: t('stocks.pl'),
    dividend_yield: t('stocks.dy'),
  }
  return types[type] || type
}

// Formatar condicao
function formatCondition(alert: Alert): string {
  const op = alert.condition.operator
  const val = alert.condition.value

  if (alert.type === 'price') {
    return `${op === 'above' ? '>' : '<'} R$ ${val.toFixed(2)}`
  }
  if (alert.type === 'change_percent') {
    return `${op === 'change_up' ? '>' : '>'} ${val}%`
  }
  if (alert.type === 'pe_ratio') {
    return `${t('stocks.pl')} ${op === 'above' ? '>' : '<'} ${val}`
  }
  if (alert.type === 'dividend_yield') {
    return `${t('stocks.dy')} ${op === 'above' ? '>' : '<'} ${val}%`
  }
  return `${op} ${val}`
}

// Atualizar operadores quando tipo muda
function onTypeChange() {
  const type = selectedType.value
  if (type?.operators?.length) {
    newAlert.value.operator = type.operators[0].value
  }
}

onMounted(loadData)
</script>

<template>
  <div>
    <header class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100">{{ t('alerts.title') }}</h1>
        <p class="text-gray-600 dark:text-gray-400 mt-1">
          {{ t('alerts.subtitle') }}
        </p>
      </div>
      <button @click="showModal = true" class="btn btn-primary">
        {{ t('alerts.newAlert') }}
      </button>
    </header>

    <!-- Notificações Push -->
    <NotificationSettings class="mb-6" />

    <!-- Dica educativa -->
    <div class="card mb-6 bg-blue-500/10 border border-blue-500/20">
      <div class="flex gap-3">
        <div class="flex-shrink-0">
          <svg class="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div>
          <h3 class="font-medium text-blue-400 mb-1">{{ t('alerts.tipTitle') }}</h3>
          <p class="text-sm text-gray-400">
            {{ t('alerts.tipDescription') }}
          </p>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12 text-gray-400">
      <svg class="animate-spin h-8 w-8 mx-auto mb-2 text-primary-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      {{ t('alerts.loadingAlerts') }}
    </div>

    <!-- Lista de alertas -->
    <div v-else-if="alerts.length" class="space-y-4">
      <div
        v-for="alert in alerts"
        :key="alert.id"
        class="card"
        :class="{
          'opacity-50': !alert.is_active,
        }"
      >
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <!-- Toggle -->
            <button
              @click="toggleAlert(alert)"
              class="relative w-12 h-6 rounded-full transition-colors"
              :class="alert.is_active ? 'bg-emerald-500' : 'bg-gray-600'"
            >
              <span
                class="absolute top-1 w-4 h-4 rounded-full bg-white transition-transform"
                :class="alert.is_active ? 'left-7' : 'left-1'"
              ></span>
            </button>

            <!-- Info -->
            <div>
              <div class="flex items-center gap-2">
                <span class="font-bold text-white text-lg">{{ alert.ticker }}</span>
                <span class="text-xs px-2 py-0.5 rounded bg-gray-700 text-gray-300">
                  {{ formatAlertType(alert.type) }}
                </span>
              </div>
              <p class="text-gray-400 text-sm">{{ alert.name }}</p>
            </div>
          </div>

          <div class="flex items-center gap-6">
            <!-- Condicao -->
            <div class="text-right">
              <p class="text-xl font-bold text-white">{{ formatCondition(alert) }}</p>
              <p v-if="alert.trigger_count > 0" class="text-xs text-gray-500">
                {{ t('alerts.triggered', { n: alert.trigger_count }) }}
              </p>
            </div>

            <!-- Acoes -->
            <div class="flex items-center gap-2">
              <button
                @click="checkAlert(alert)"
                :disabled="checkingAlert === alert.id"
                class="p-2 text-gray-400 hover:text-blue-400 transition-colors"
                :title="t('alerts.checkNow')"
              >
                <svg v-if="checkingAlert === alert.id" class="animate-spin w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                </svg>
                <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </button>
              <button
                @click="deleteAlert(alert)"
                class="p-2 text-gray-400 hover:text-red-400 transition-colors"
                :title="t('alerts.remove')"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- Resultado da verificacao -->
        <div v-if="checkResult && checkResult.alert_id === alert.id" class="mt-4 pt-4 border-t border-gray-700">
          <div v-if="checkResult.error" class="text-red-400 text-sm">
            {{ checkResult.error }}
          </div>
          <div v-else class="flex items-center gap-4">
            <div
              class="px-3 py-1 rounded-full text-sm font-medium"
              :class="checkResult.triggered ? 'bg-emerald-500/20 text-emerald-400' : 'bg-gray-700 text-gray-400'"
            >
              {{ checkResult.triggered ? t('alerts.conditionMet') : t('alerts.conditionNotMet') }}
            </div>
            <p class="text-sm text-gray-400">
              {{ t('alerts.currentPrice') }}: R$ {{ checkResult.current_quote?.price?.toFixed(2) || '--' }}
            </p>
            <p v-if="checkResult.message" class="text-sm text-emerald-400">
              {{ checkResult.message }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Estado vazio -->
    <div v-else class="card text-center py-12">
      <svg class="w-16 h-16 mx-auto text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
      </svg>
      <h3 class="text-lg font-medium text-gray-300 mb-2">{{ t('alerts.noAlertsTitle') }}</h3>
      <p class="text-gray-500 mb-6 max-w-md mx-auto">
        {{ t('alerts.noAlertsDescription') }}
      </p>
      <button @click="showModal = true" class="btn btn-primary">
        {{ t('alerts.createFirstAlert') }}
      </button>
    </div>

    <!-- Modal criar alerta -->
    <div
      v-if="showModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      @click.self="showModal = false"
    >
      <div class="bg-gray-800 rounded-lg shadow-xl w-full max-w-lg">
        <div class="p-6 border-b border-gray-700">
          <h2 class="text-xl font-bold text-white">{{ t('alerts.newAlertTitle') }}</h2>
          <p class="text-sm text-gray-400 mt-1">{{ t('alerts.configureNotification') }}</p>
        </div>

        <form @submit.prevent="handleCreateAlert" class="p-6 space-y-6">
          <!-- Selecionar acao -->
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-2">{{ t('alerts.whichStock') }}</label>
            <select
              v-model="newAlert.ticker"
              class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              required
            >
              <option value="">{{ t('alerts.selectStock') }}</option>
              <option v-for="stock in stocks" :key="stock.ticker" :value="stock.ticker">
                {{ stock.ticker }} - {{ stock.name }}
              </option>
            </select>
          </div>

          <!-- Tipo de alerta -->
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-2">{{ t('alerts.alertType') }}</label>
            <div class="grid grid-cols-2 gap-3">
              <button
                v-for="type in alertTypes"
                :key="type.type"
                type="button"
                @click="newAlert.type = type.type; onTypeChange()"
                class="p-3 rounded-lg border text-left transition-all"
                :class="newAlert.type === type.type
                  ? 'border-primary-500 bg-primary-500/10'
                  : 'border-gray-600 hover:border-gray-500'"
              >
                <p class="font-medium text-white text-sm">{{ type.name }}</p>
                <p class="text-xs text-gray-400 mt-0.5 line-clamp-2">{{ type.tip }}</p>
              </button>
            </div>
          </div>

          <!-- Condicao -->
          <div v-if="selectedType" class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-2">{{ t('alerts.when') }}</label>
              <select
                v-model="newAlert.operator"
                class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500"
              >
                <option v-for="op in selectedType.operators" :key="op.value" :value="op.value">
                  {{ op.label }}
                </option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-2">{{ selectedType.value_label }}</label>
              <input
                v-model="newAlert.value"
                type="number"
                step="any"
                :placeholder="selectedType.value_placeholder"
                class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500"
                required
              />
            </div>
          </div>

          <!-- Nome opcional -->
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-2">{{ t('alerts.alertNameOptional') }}</label>
            <input
              v-model="newAlert.name"
              type="text"
              :placeholder="t('alerts.alertNamePlaceholder')"
              class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <!-- Explicacao -->
          <div v-if="selectedType" class="p-3 bg-gray-700/50 rounded-lg">
            <p class="text-sm text-gray-400">
              <strong class="text-gray-300">{{ selectedType.description }}</strong>
            </p>
          </div>

          <!-- Botoes -->
          <div class="flex justify-end gap-3 pt-4 border-t border-gray-700">
            <button
              type="button"
              @click="showModal = false; resetForm()"
              class="btn btn-secondary"
            >
              {{ t('common.cancel') }}
            </button>
            <button
              type="submit"
              :disabled="submitting || !newAlert.ticker || !newAlert.value"
              class="btn btn-primary"
            >
              {{ submitting ? t('alerts.creating') : t('alerts.createAlert') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
