<script setup lang="ts">
import { RouterView } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import ConfirmModal from '@/components/ConfirmModal.vue'
import { useConfirm } from '@/composables/useConfirm'

const { isOpen, options, handleConfirm, handleCancel } = useConfirm()
</script>

<template>
  <div class="min-h-screen">
    <Navbar />
    <main class="container mx-auto px-4 py-6 pb-24 md:pb-8">
      <RouterView />
    </main>

    <ConfirmModal
      v-if="isOpen"
      :title="options.title"
      :message="options.message"
      :confirm-text="options.confirmText"
      :cancel-text="options.cancelText"
      :dangerous="options.dangerous"
      @confirm="handleConfirm"
      @cancel="handleCancel"
    />
  </div>
</template>
