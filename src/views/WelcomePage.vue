<template>
  <div class="welcome-page">
    <div class="welcome-container">
      <h1 class="welcome-title">{{ t('welcome.title') }}</h1>
      <p class="welcome-intro">{{ t('welcome.intro') }}</p>
      
      <div class="instructions-card card">
        <h2 class="instructions-title">{{ t('welcome.instructions') }}</h2>
        <ol class="instructions-list">
          <li>{{ t('welcome.step1') }}</li>
          <li>{{ t('welcome.step2') }}</li>
          <li>{{ t('welcome.step3') }}</li>
          <li>{{ t('welcome.step4') }}</li>
          <li>{{ t('welcome.step5') }}</li>
          <li>{{ t('welcome.step6') }}</li>
        </ol>
        
        <div class="task-requirement">
          <strong>{{ t('welcome.taskRequirement') }}</strong>
        </div>
        
        <p class="estimated-time text-muted">{{ t('welcome.estimatedTime') }}</p>
      </div>
      
      <button class="btn btn-primary start-btn" @click="startExperiment">
        {{ t('welcome.start') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useSessionStore } from '../stores/session'

const { t } = useI18n()
const router = useRouter()
const session = useSessionStore()

function startExperiment() {
  // Initialize session
  session.initSession()
  
  // Set initial Wizard state
  session.taskStep = 'guided_A'
  session.currentTaskType = 'guided'
  session.currentVersion = 'A'
  
  router.push('/explore')
}
</script>

<style scoped>
.welcome-page {
  min-height: calc(100vh - 60px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.welcome-container {
  max-width: 600px;
  text-align: center;
}

.welcome-title {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 1rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.welcome-intro {
  color: var(--text-secondary);
  margin-bottom: 2rem;
  font-size: 1.1rem;
}

.instructions-card {
  text-align: left;
  margin-bottom: 2rem;
}

.instructions-title {
  font-size: 1.2rem;
  margin-bottom: 1rem;
  color: var(--primary);
}

.instructions-list {
  padding-left: 1.5rem;
  color: var(--text-secondary);
}

.instructions-list li {
  margin-bottom: 0.75rem;
}

.task-requirement {
  margin-top: 1.5rem;
  padding: 1rem;
  background: rgba(102, 126, 234, 0.1);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--primary);
  color: var(--text-primary);
}

.estimated-time {
  margin-top: 1rem;
  font-size: 0.9rem;
}

.start-btn {
  font-size: 1.1rem;
  padding: 1rem 3rem;
}
</style>
