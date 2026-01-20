<template>
  <div class="complete-page">
    <div class="complete-container">
      <div class="success-icon">✓</div>
      <h1 class="complete-title">{{ t('completion.title') }}</h1>
      <p class="complete-message">{{ t('completion.message') }}</p>
      
      <button class="btn btn-secondary" @click="closeWindow">
        {{ t('completion.close') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

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
</style>
