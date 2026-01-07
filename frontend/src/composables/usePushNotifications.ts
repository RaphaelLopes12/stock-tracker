import { ref, computed, onMounted } from 'vue'
import { notificationsApi } from '@/services/api'

const isSupported = ref(false)
const permission = ref<NotificationPermission>('default')
const subscription = ref<PushSubscription | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const vapidKey = ref<string | null>(null)

const isSubscribed = computed(() => !!subscription.value)
const canSubscribe = computed(() => isSupported.value && permission.value !== 'denied')

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
  const rawData = window.atob(base64)
  const outputArray = new Uint8Array(rawData.length)
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i)
  }
  return outputArray
}

async function checkSupport() {
  isSupported.value = 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window

  if (isSupported.value) {
    permission.value = Notification.permission

    try {
      const response = await notificationsApi.getVapidKey()
      vapidKey.value = response.data.public_key
    } catch (e) {
      console.error('Failed to get VAPID key:', e)
    }

    const registration = await navigator.serviceWorker.ready
    subscription.value = await registration.pushManager.getSubscription()
  }
}

async function requestPermission(): Promise<boolean> {
  if (!isSupported.value) return false

  try {
    const result = await Notification.requestPermission()
    permission.value = result
    return result === 'granted'
  } catch (e) {
    error.value = 'Erro ao solicitar permissão'
    return false
  }
}

async function subscribe(): Promise<boolean> {
  if (!isSupported.value || !vapidKey.value) {
    error.value = 'Push notifications não suportadas'
    return false
  }

  loading.value = true
  error.value = null

  try {
    if (permission.value !== 'granted') {
      const granted = await requestPermission()
      if (!granted) {
        error.value = 'Permissão negada'
        return false
      }
    }

    const registration = await navigator.serviceWorker.ready
    const pushSubscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(vapidKey.value) as BufferSource,
    })

    const p256dh = pushSubscription.getKey('p256dh')
    const auth = pushSubscription.getKey('auth')

    if (!p256dh || !auth) {
      throw new Error('Failed to get subscription keys')
    }

    await notificationsApi.subscribe({
      endpoint: pushSubscription.endpoint,
      keys: {
        p256dh: btoa(String.fromCharCode(...new Uint8Array(p256dh))),
        auth: btoa(String.fromCharCode(...new Uint8Array(auth))),
      },
    })

    subscription.value = pushSubscription
    return true
  } catch (e: any) {
    error.value = e.message || 'Erro ao ativar notificações'
    console.error('Subscribe error:', e)
    return false
  } finally {
    loading.value = false
  }
}

async function unsubscribe(): Promise<boolean> {
  if (!subscription.value) return true

  loading.value = true
  error.value = null

  try {
    await notificationsApi.unsubscribe(subscription.value.endpoint)
    await subscription.value.unsubscribe()
    subscription.value = null
    return true
  } catch (e: any) {
    error.value = e.message || 'Erro ao desativar notificações'
    return false
  } finally {
    loading.value = false
  }
}

async function updatePreferences(prefs: {
  notify_price_alerts?: boolean
  notify_dividends?: boolean
  notify_news?: boolean
}): Promise<boolean> {
  if (!subscription.value) return false

  loading.value = true
  error.value = null

  try {
    await notificationsApi.updatePreferences(subscription.value.endpoint, prefs)
    return true
  } catch (e: any) {
    error.value = e.message || 'Erro ao atualizar preferências'
    return false
  } finally {
    loading.value = false
  }
}

export function usePushNotifications() {
  onMounted(() => {
    checkSupport()
  })

  return {
    isSupported,
    isSubscribed,
    canSubscribe,
    permission,
    loading,
    error,
    subscribe,
    unsubscribe,
    requestPermission,
    updatePreferences,
    checkSupport,
  }
}
