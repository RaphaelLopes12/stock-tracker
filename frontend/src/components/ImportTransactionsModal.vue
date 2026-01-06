<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { portfolioApi, type ImportResult } from '@/services/api'

const { t } = useI18n()

const emit = defineEmits<{
  close: []
  imported: []
}>()

// Estado
const file = ref<File | null>(null)
const isDragging = ref(false)
const loading = ref(false)
const result = ref<ImportResult | null>(null)
const error = ref<string | null>(null)

// Opcoes de importacao
const skipDuplicates = ref(true)
const createMissingStocks = ref(true)

// Computed
const canImport = computed(() => file.value !== null && !loading.value)

const hasResult = computed(() => result.value !== null)

const resultStatus = computed(() => {
  if (!result.value) return 'idle'
  if (result.value.success_count > 0 && result.value.error_count === 0) return 'success'
  if (result.value.success_count > 0 && result.value.error_count > 0) return 'partial'
  if (result.value.error_count > 0) return 'error'
  return 'empty'
})

// Handlers
const handleFileSelect = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (input.files && input.files.length > 0) {
    selectFile(input.files[0])
  }
}

const selectFile = (selectedFile: File) => {
  const validTypes = ['text/csv', 'text/plain', 'application/vnd.ms-excel']
  const validExtensions = ['.csv', '.txt']

  const isValidType = validTypes.includes(selectedFile.type) ||
    validExtensions.some(ext => selectedFile.name.toLowerCase().endsWith(ext))

  if (!isValidType) {
    error.value = t('common.error')
    return
  }

  file.value = selectedFile
  error.value = null
  result.value = null
}

const handleDrop = (event: DragEvent) => {
  isDragging.value = false
  const files = event.dataTransfer?.files
  if (files && files.length > 0) {
    selectFile(files[0])
  }
}

const handleDragOver = (event: DragEvent) => {
  event.preventDefault()
  isDragging.value = true
}

const handleDragLeave = () => {
  isDragging.value = false
}

const clearFile = () => {
  file.value = null
  result.value = null
  error.value = null
}

const downloadTemplate = async () => {
  try {
    const response = await portfolioApi.getImportTemplate()
    const blob = new Blob([response.data], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'template_transacoes.csv'
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (e) {
    console.error('Erro ao baixar template:', e)
  }
}

const importFile = async () => {
  if (!file.value) return

  loading.value = true
  error.value = null

  try {
    const response = await portfolioApi.importCsv(
      file.value,
      skipDuplicates.value,
      createMissingStocks.value
    )
    result.value = response.data

    if (response.data.success_count > 0) {
      emit('imported')
    }
  } catch (e: any) {
    error.value = e.response?.data?.detail || t('importTransactions.importError')
  } finally {
    loading.value = false
  }
}

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
</script>

<template>
  <div
    class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
    @click.self="emit('close')"
  >
    <div class="bg-gray-800 rounded-xl shadow-2xl w-full max-w-xl max-h-[90vh] overflow-hidden flex flex-col">
      <!-- Header -->
      <div class="flex items-center justify-between p-6 border-b border-gray-700">
        <div>
          <h2 class="text-xl font-semibold text-white">{{ t('importTransactions.title') }}</h2>
          <p class="text-sm text-gray-400 mt-1">{{ t('importTransactions.subtitle') }}</p>
        </div>
        <button
          @click="emit('close')"
          class="text-gray-400 hover:text-white transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Content -->
      <div class="p-6 overflow-y-auto flex-1 space-y-6">
        <!-- Dica de formatos -->
        <div class="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
          <div class="flex gap-3">
            <svg class="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <h3 class="font-medium text-blue-400 text-sm mb-1">{{ t('importTransactions.acceptedFormats') }}</h3>
              <p class="text-xs text-gray-400">
                {{ t('importTransactions.formatDescription') }}
              </p>
            </div>
          </div>
        </div>

        <!-- Error -->
        <div v-if="error" class="bg-red-500/20 border border-red-500/50 text-red-400 px-4 py-3 rounded-lg text-sm">
          {{ error }}
        </div>

        <!-- File Drop Zone -->
        <div
          v-if="!hasResult"
          class="border-2 border-dashed rounded-xl p-8 text-center transition-colors"
          :class="isDragging
            ? 'border-primary-500 bg-primary-500/10'
            : file
              ? 'border-emerald-500 bg-emerald-500/10'
              : 'border-gray-600 hover:border-gray-500'"
          @drop.prevent="handleDrop"
          @dragover="handleDragOver"
          @dragleave="handleDragLeave"
        >
          <div v-if="!file">
            <svg class="w-12 h-12 mx-auto text-gray-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <p class="text-gray-400 mb-2">{{ t('importTransactions.dropHere') }}</p>
            <label class="btn btn-primary cursor-pointer inline-block">
              {{ t('importTransactions.selectFile') }}
              <input
                type="file"
                accept=".csv,.txt"
                class="hidden"
                @change="handleFileSelect"
              />
            </label>
            <p class="text-xs text-gray-500 mt-3">{{ t('importTransactions.fileLimit') }}</p>
          </div>

          <div v-else class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-12 h-12 bg-emerald-500/20 rounded-lg flex items-center justify-center">
                <svg class="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div class="text-left">
                <p class="text-white font-medium">{{ file.name }}</p>
                <p class="text-xs text-gray-400">{{ formatFileSize(file.size) }}</p>
              </div>
            </div>
            <button
              @click="clearFile"
              class="p-2 text-gray-400 hover:text-red-400 transition-colors"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Options -->
        <div v-if="file && !hasResult" class="space-y-3">
          <label class="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              v-model="skipDuplicates"
              class="w-4 h-4 rounded border-gray-600 bg-gray-700 text-primary-500 focus:ring-primary-500"
            />
            <span class="text-sm text-gray-300">{{ t('importTransactions.skipDuplicates') }}</span>
          </label>
          <label class="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              v-model="createMissingStocks"
              class="w-4 h-4 rounded border-gray-600 bg-gray-700 text-primary-500 focus:ring-primary-500"
            />
            <span class="text-sm text-gray-300">{{ t('importTransactions.createMissingStocks') }}</span>
          </label>
        </div>

        <!-- Result -->
        <div v-if="hasResult && result" class="space-y-4">
          <!-- Status Banner -->
          <div
            class="rounded-lg p-4 flex items-center gap-3"
            :class="{
              'bg-emerald-500/20 border border-emerald-500/30': resultStatus === 'success',
              'bg-yellow-500/20 border border-yellow-500/30': resultStatus === 'partial',
              'bg-red-500/20 border border-red-500/30': resultStatus === 'error',
              'bg-gray-700': resultStatus === 'empty',
            }"
          >
            <div
              class="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
              :class="{
                'bg-emerald-500/30': resultStatus === 'success',
                'bg-yellow-500/30': resultStatus === 'partial',
                'bg-red-500/30': resultStatus === 'error',
                'bg-gray-600': resultStatus === 'empty',
              }"
            >
              <svg v-if="resultStatus === 'success'" class="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              <svg v-else-if="resultStatus === 'partial'" class="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <svg v-else class="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <div>
              <p class="font-medium" :class="{
                'text-emerald-400': resultStatus === 'success',
                'text-yellow-400': resultStatus === 'partial',
                'text-red-400': resultStatus === 'error',
                'text-gray-400': resultStatus === 'empty',
              }">
                {{ resultStatus === 'success' ? t('importTransactions.importCompleted') :
                   resultStatus === 'partial' ? t('importTransactions.partialImport') :
                   resultStatus === 'error' ? t('importTransactions.importError') :
                   t('importTransactions.noTransactionsImported') }}
              </p>
              <p class="text-sm text-gray-400">
                {{ result.success_count }} {{ t('importTransactions.imported') }},
                {{ result.skipped_count }} {{ t('importTransactions.skipped') }},
                {{ result.error_count }} {{ t('importTransactions.withError') }}
              </p>
            </div>
          </div>

          <!-- Warnings -->
          <div v-if="result.warnings.length > 0" class="bg-gray-700/50 rounded-lg p-4">
            <h4 class="text-sm font-medium text-gray-300 mb-2">{{ t('importTransactions.information') }}</h4>
            <ul class="space-y-1">
              <li
                v-for="(warn, idx) in result.warnings"
                :key="idx"
                class="text-xs text-gray-400 flex items-start gap-2"
              >
                <span class="text-yellow-400">•</span>
                {{ warn }}
              </li>
            </ul>
          </div>

          <!-- Errors -->
          <div v-if="result.errors.length > 0" class="bg-red-500/10 rounded-lg p-4 max-h-40 overflow-y-auto">
            <h4 class="text-sm font-medium text-red-400 mb-2">{{ t('importTransactions.errors') }}</h4>
            <ul class="space-y-1">
              <li
                v-for="(err, idx) in result.errors"
                :key="idx"
                class="text-xs text-gray-400 flex items-start gap-2"
              >
                <span class="text-red-400">•</span>
                {{ err }}
              </li>
            </ul>
          </div>

          <!-- Created Stocks -->
          <div v-if="result.created_stocks.length > 0" class="bg-blue-500/10 rounded-lg p-4">
            <h4 class="text-sm font-medium text-blue-400 mb-2">{{ t('importTransactions.createdStocks') }}</h4>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="ticker in result.created_stocks"
                :key="ticker"
                class="px-2 py-1 bg-blue-500/20 text-blue-400 text-xs rounded"
              >
                {{ ticker }}
              </span>
            </div>
            <p class="text-xs text-gray-500 mt-2">
              {{ t('importTransactions.updateStockNames') }}
            </p>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="p-6 border-t border-gray-700 flex items-center justify-between gap-4">
        <button
          @click="downloadTemplate"
          class="text-sm text-gray-400 hover:text-white transition-colors flex items-center gap-2"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          {{ t('portfolio.downloadCsvTemplate') }}
        </button>

        <div class="flex gap-3">
          <button
            v-if="hasResult"
            @click="clearFile"
            class="btn btn-secondary"
          >
            {{ t('portfolio.importAnother') }}
          </button>
          <button
            v-if="!hasResult"
            @click="emit('close')"
            class="btn btn-secondary"
          >
            {{ t('common.cancel') }}
          </button>
          <button
            v-if="!hasResult"
            @click="importFile"
            :disabled="!canImport"
            class="btn btn-primary"
          >
            <span v-if="loading" class="flex items-center gap-2">
              <svg class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
              </svg>
              {{ t('importTransactions.importing') }}
            </span>
            <span v-else>{{ t('importTransactions.import') }}</span>
          </button>
          <button
            v-if="hasResult"
            @click="emit('close')"
            class="btn btn-primary"
          >
            {{ t('importTransactions.done') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
