import { createI18n } from 'vue-i18n'
import ptBR from './pt-BR.json'
import en from './en.json'
import es from './es.json'

export type MessageSchema = typeof ptBR

// Detecta idioma do navegador ou usa salvo no localStorage
function getDefaultLocale(): string {
  const saved = localStorage.getItem('locale')
  if (saved && ['pt-BR', 'en', 'es'].includes(saved)) {
    return saved
  }

  const browserLang = navigator.language
  if (browserLang.startsWith('pt')) return 'pt-BR'
  if (browserLang.startsWith('es')) return 'es'
  return 'en'
}

const i18n = createI18n<[MessageSchema], 'pt-BR' | 'en' | 'es'>({
  legacy: false, // Composition API
  locale: getDefaultLocale(),
  fallbackLocale: 'pt-BR',
  messages: {
    'pt-BR': ptBR,
    en,
    es,
  },
})

export function setLocale(locale: 'pt-BR' | 'en' | 'es') {
  i18n.global.locale.value = locale
  localStorage.setItem('locale', locale)
  document.documentElement.lang = locale === 'pt-BR' ? 'pt-BR' : locale
}

export function getLocale() {
  return i18n.global.locale.value
}

export default i18n
