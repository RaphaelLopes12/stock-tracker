/// <reference lib="webworker" />
import { precacheAndRoute, cleanupOutdatedCaches } from 'workbox-precaching'
import { clientsClaim } from 'workbox-core'
import { registerRoute } from 'workbox-routing'
import { NetworkFirst } from 'workbox-strategies'
import { ExpirationPlugin } from 'workbox-expiration'

declare let self: ServiceWorkerGlobalScope

self.skipWaiting()
clientsClaim()

precacheAndRoute(self.__WB_MANIFEST)
cleanupOutdatedCaches()

registerRoute(
  ({ url }) => url.pathname.startsWith('/api/'),
  new NetworkFirst({
    cacheName: 'api-cache',
    plugins: [
      new ExpirationPlugin({
        maxEntries: 100,
        maxAgeSeconds: 60 * 5,
      }),
    ],
  })
)

interface PushPayload {
  title: string
  body: string
  icon?: string
  badge?: string
  tag?: string
  data?: {
    type?: string
    ticker?: string
    url?: string
  }
  actions?: Array<{ action: string; title: string }>
  require_interaction?: boolean
}

self.addEventListener('push', (event: PushEvent) => {
  if (!event.data) return

  try {
    const payload: PushPayload = event.data.json()

    const options = {
      body: payload.body,
      icon: payload.icon || '/pwa-192x192.png',
      badge: payload.badge || '/pwa-192x192.png',
      tag: payload.tag,
      data: payload.data,
      actions: payload.actions,
      requireInteraction: payload.require_interaction || false,
      vibrate: [200, 100, 200],
    } as NotificationOptions

    event.waitUntil(self.registration.showNotification(payload.title, options))
  } catch {
  }
})

self.addEventListener('notificationclick', (event: NotificationEvent) => {
  event.notification.close()

  const data = event.notification.data
  let targetUrl = '/'

  if (event.action === 'view' && data?.url) {
    targetUrl = data.url
  } else if (event.action === 'dismiss') {
    return
  } else if (data?.url) {
    targetUrl = data.url
  }

  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          client.navigate(targetUrl)
          return client.focus()
        }
      }
      return self.clients.openWindow(targetUrl)
    })
  )
})

self.addEventListener('notificationclose', () => {})
