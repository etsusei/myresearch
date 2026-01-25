<template>
  <div class="complete-page">
    <div class="complete-container">
      <div class="success-icon">✓</div>
      <h1 class="complete-title">{{ t('completion.title') }}</h1>
      <p class="complete-message">{{ t('completion.message') }}</p>
      
      <!-- Download Section -->
      <div class="download-section">
        <p class="download-prompt">{{ t('completion.downloadPrompt') }}</p>
        <p class="email-address">your-email@example.com</p>
        <button class="btn btn-primary download-btn" @click="downloadData">
          📥 {{ t('completion.downloadButton') }}
        </button>
      </div>
      
      <button class="btn btn-secondary mt-2" @click="closeWindow">
        {{ t('completion.close') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { useSessionStore } from '../stores/session'

const { t } = useI18n()
const session = useSessionStore()

function downloadData() {
  session.downloadSessionData()
}

function closeWindow() {
  window.close()
}
</script>

<style scoped>
.complete-page {
  min-height: calc(100vh - 60px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.complete-container {
  text-align: center;
  max-width: 500px;
}

.success-icon {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: var(--success);
  color: white;
  font-size: 3rem;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1.5rem;
  animation: scale-in 0.3s ease;
}

@keyframes scale-in {
  0% { transform: scale(0); }
  100% { transform: scale(1); }
}

.complete-title {
  font-size: 2rem;
  margin-bottom: 1rem;
}

.complete-message {
  color: var(--text-secondary);
  margin-bottom: 2rem;
}

.download-section {
  background: rgba(255, 255, 255, 0.05);
  padding: 1.5rem;
  border-radius: var(--radius);
  margin-bottom: 1.5rem;
}

.download-prompt {
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
}

.email-address {
  color: var(--primary);
  font-weight: 600;
  font-size: 1.1rem;
  margin-bottom: 1rem;
}

.download-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1rem;
  padding: 0.75rem 1.5rem;
}

.mt-2 {
  margin-top: 1rem;
}
</style>
