<template>
  <div id="app" :class="{ 'dark-mode': isDarkMode }">
    <header class="app-header">
      <h1 class="logo">{{ t('common.appTitle') }}</h1>
      <div class="header-controls">
        <select v-model="locale" class="lang-select">
          <option value="zh">中文</option>
          <option value="en">English</option>
          <option value="ja">日本語</option>
        </select>
      </div>
    </header>
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t, locale } = useI18n()
const isDarkMode = ref(true)

// Save language preference
watch(locale, (newLang) => {
  localStorage.setItem('lang', newLang)
})

// Load saved language
const savedLang = localStorage.getItem('lang')
if (savedLang && ['zh', 'en', 'ja'].includes(savedLang)) {
  locale.value = savedLang
}
</script>

<style scoped>
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo {
  font-size: 1.25rem;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-controls {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.lang-select {
  padding: 0.5rem 1rem;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #fff;
  cursor: pointer;
  font-size: 0.9rem;
}

.lang-select option {
  background: #1a1a2e;
  color: #fff;
}

.app-main {
  flex: 1;
  overflow: auto;
}
</style>
