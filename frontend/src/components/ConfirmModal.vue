<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

interface Props {
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  confirmClass?: string
  dangerous?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  confirmText: '',
  cancelText: '',
  confirmClass: '',
  dangerous: false,
})

const emit = defineEmits<{
  confirm: []
  cancel: []
}>()

const resolvedTitle = props.title || t('common.confirm')
const resolvedConfirmText = props.confirmText || t('common.confirm')
const resolvedCancelText = props.cancelText || t('common.cancel')
const buttonClass = props.confirmClass || (props.dangerous ? 'bg-red-600 hover:bg-red-700' : 'bg-primary-600 hover:bg-primary-700')
</script>

<template>
  <div
    class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
    @click.self="emit('cancel')"
  >
    <div class="bg-gray-800 rounded-xl shadow-2xl w-full max-w-sm animate-in fade-in zoom-in duration-200">
      <div class="p-6">
        <div class="flex items-center gap-3 mb-4">
          <div
            class="w-10 h-10 rounded-full flex items-center justify-center"
            :class="dangerous ? 'bg-red-500/20' : 'bg-primary-500/20'"
          >
            <svg
              v-if="dangerous"
              class="w-5 h-5 text-red-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <svg
              v-else
              class="w-5 h-5 text-primary-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 class="text-lg font-semibold text-white">{{ resolvedTitle }}</h3>
        </div>

        <p class="text-gray-300 text-sm mb-6 ml-13">{{ message }}</p>

        <div class="flex gap-3 justify-end">
          <button
            @click="emit('cancel')"
            class="px-4 py-2 bg-gray-700 text-white rounded-lg font-medium hover:bg-gray-600 transition-colors"
          >
            {{ resolvedCancelText }}
          </button>
          <button
            @click="emit('confirm')"
            class="px-4 py-2 text-white rounded-lg font-medium transition-colors"
            :class="buttonClass"
          >
            {{ resolvedConfirmText }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
