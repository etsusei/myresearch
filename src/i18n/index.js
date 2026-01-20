import { createI18n } from 'vue-i18n'
import en from '../../i18n/en.json'
import zh from '../../i18n/zh.json'
import ja from '../../i18n/ja.json'

export const i18n = createI18n({
    legacy: false,
    locale: localStorage.getItem('lang') || 'zh',
    fallbackLocale: 'en',
    messages: {
        en,
        zh,
        ja
    }
})
