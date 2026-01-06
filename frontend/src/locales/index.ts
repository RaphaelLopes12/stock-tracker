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

const i18n = createI18n({
  legacy: false,
  locale: getDefaultLocale(),
  fallbackLocale: 'pt-BR',
  messages: {
    'pt-BR': ptBR,
    en,
    es,
  },
})

export function setLocale(locale: 'pt-BR' | 'en' | 'es') {
  (i18n.global.locale as unknown as { value: string }).value = locale
  localStorage.setItem('locale', locale)
  document.documentElement.lang = locale === 'pt-BR' ? 'pt-BR' : locale
}

export function getLocale(): 'pt-BR' | 'en' | 'es' {
  return (i18n.global.locale as unknown as { value: string }).value as 'pt-BR' | 'en' | 'es'
}

export default i18n
