<template>
  <div class="explore-page">
    <div class="explore-container">
      <!-- Left Panel: Controls -->
      <aside class="control-panel card" :class="{ disabled: isControlsLocked }">
        <h3 class="panel-title">{{ t('explorer.selectGenre') }}</h3>
        <select v-model="selectedGenre" class="form-select" :disabled="isControlsLocked">
          <option v-for="g in genres" :key="g" :value="g">{{ t(`genres.${g}`) || g }}</option>
        </select>
        
        <h3 class="panel-title mt-2">{{ t('explorer.selectEmotion') }}</h3>
        <select v-model="selectedEmotion" class="form-select" :disabled="isControlsLocked">
          <option v-for="e in emotions" :key="e" :value="e">{{ t(`emotions.${e}`) || e }}</option>
        </select>
        
        <h3 class="panel-title mt-2">{{ t('explorer.selectVersion') }}</h3>
        <div class="version-toggle">
          <button 
            class="version-btn" 
            :class="{ active: session.currentVersion === 'A' }"
            @click="switchVersion('A')"
            :disabled="isControlsLocked"
          >
            {{ t('common.versionA') }}
          </button>
          <button 
            class="version-btn"
            :class="{ active: session.currentVersion === 'B' }"
            @click="switchVersion('B')"
            :disabled="isControlsLocked"
          >
            {{ t('common.versionB') }}
          </button>
        </div>
        
        <button 
          class="btn btn-primary mt-2 analyze-btn" 
          @click="handleAnalyzeClick"
          :disabled="isLoading || (isControlsLocked && session.taskStep !== 'free_setup' && !isTransition)"
        >
          <span v-if="isLoading" class="spinner"></span>
          <span v-else>{{ t('common.analyze') }}</span>
        </button>
        
        <!-- Analysis Info -->
        <div class="analysis-info mt-2" v-if="analysisResult">
          <p class="info-text">{{ selectedGenre }} + {{ selectedEmotion }}</p>
          <p class="info-text">{{ t('common.total') || 'Total' }}: {{ analysisResult.count }} {{ t('common.songs') || 'songs' }}</p>
          <p class="info-text">K = {{ analysisResult.k }}</p>
        </div>

        <!-- Player -->
        <div class="player-section mt-3">
          <h3 class="panel-title">{{ t('explorer.nowPlaying') }}</h3>
          <p class="song-id">{{ currentSong || '-' }}</p>
          
          <!-- Loading State -->
          <div v-if="isLoadingAudio" class="loading-indicator">
            <span class="spinner"></span>
            <span>{{ t('ui.loadingMusic') }}</span>
          </div>
          
          <!-- Error State -->
          <div v-else-if="audioError" class="error-indicator">
            <span>⚠️ {{ t('ui.loadFailed') }}</span>
          </div>
          
          <audio 
            ref="audioPlayer" 
            @timeupdate="onTimeUpdate"
            @ended="onAudioEnded"
            @loadedmetadata="onAudioLoaded"
            @canplay="onAudioCanPlay"
            @error="onAudioError"
          ></audio>
          <div class="player-controls">
            <button class="player-btn" @click="togglePlay" :disabled="!currentSong || isLoadingAudio">
              {{ isPlaying ? '⏸' : '▶' }}
            </button>
            <button class="player-btn" @click="stopPlay" :disabled="!currentSong">■</button>
            <!-- Like Button -->
            <button 
              class="player-btn like-btn" 
              :class="{ liked: currentSong && session.isLiked(currentSong) }"
              @click="toggleLike"
              :disabled="!currentSong"
            >
              {{ currentSong && session.isLiked(currentSong) ? '❤️' : '🤍' }}
            </button>
          </div>
          <div class="progress-bar" @click="seekAudio">
            <div class="progress-fill" :style="{ width: progress + '%' }"></div>
          </div>
          <div class="time-display">{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</div>
          
          <!-- Progress Tracking -->
          <div class="task-progress mt-2">
            <p class="progress-text">{{ t('task.progress.listened').replace('{count}', session.getListenedCount()) }}</p>
            <p class="progress-text" v-if="session.currentTaskType === 'free'">{{ t('task.progress.liked').replace('{count}', session.getLikedCount()).replace('{total}', '3') }}</p>
          </div>
        </div>
        
        <!-- Cluster Reps -->
        <div class="cluster-reps mt-3" v-if="clusterReps.length > 0">
          <h3 class="panel-title">{{ t('explorer.clusterReps') }}</h3>
          <div 
            v-for="(rep, i) in clusterReps" 
            :key="i"
            class="cluster-rep-item"
            :class="{ active: currentSong === rep.id }"
            @click="playSong(rep.id)"
          >
            <span class="cluster-label" :style="{ background: getClusterColor(i) }">C{{ i + 1 }}</span>
            <span class="cluster-song">{{ rep.id }}</span>
          </div>
        </div>
      </aside>

      <!-- Center: Scatter Plot -->
      <main class="plot-area">
        <div class="plot-header">
          <span class="plot-title">{{ selectedGenre }} - {{ selectedEmotion }}</span>
          <span class="plot-subtitle">{{ stepInstruction }}</span>
        </div>
        
        <!-- Toast Notification -->
        <div class="toast-notification" v-if="toastMessage">
            {{ toastMessage }}
        </div>

        <div class="plot-wrapper">
          <!-- Y-axis: polarity at top/bottom, label in center -->
          <div class="y-axis-outer">
            <div class="y-pole-top" v-html="yAxisHighHtml"></div>
            <div class="y-axis-name">{{ axisLabels.y }} (r≈{{ axisLabels.yR }})</div>
            <div class="y-pole-bottom" v-html="yAxisLowHtml"></div>
          </div>
          <div class="plot-container" ref="plotContainer">
            <canvas ref="plotCanvas" @click="handlePlotClick" @mousemove="handlePlotHover"></canvas>
            
            <!-- Transition Overlay -->
            <div class="transition-overlay" v-if="isTransition">
                <div class="transition-card">
                    <h2>{{ t('transition.title') }}</h2>
                    <p>{{ t('transition.intro') }}</p>
                    <p v-html="t('transition.step1')"></p>
                    <button class="btn btn-primary" @click="handleTransitionNext">{{ t('transition.start') }}</button>
                </div>
            </div>
            
             <!-- Welcome Overlay (Initial) -->
             <div class="transition-overlay" v-if="session.taskStep === 'welcome'">
                <div class="transition-card">
                    <h2>{{ t('welcome.title') }}</h2>
                    <p>{{ t('welcome.intro') }}</p>
                    <p>{{ t('welcome.step1') }}</p>
                    <button class="btn btn-primary" @click="startExperiment">{{ t('welcome.start') }}</button>
                </div>
            </div>
          </div>
        </div>
        <!-- X-axis label (horizontal below) -->
        <div class="x-axis-container">
          <span class="axis-pole left">{{ axisLabels.xLow }}</span>
          <span class="axis-name">{{ axisLabels.x }} (r≈{{ axisLabels.xR }})</span>
          <span class="axis-pole right">{{ axisLabels.xHigh }}</span>
        </div>
      </main>

      <!-- Right: Questionnaire -->
      <aside class="questionnaire-panel card" v-if="session.taskStep !== 'welcome' && session.taskStep !== 'transition'">
        <h3 class="panel-title">
             {{ currentStepTitle }}
             <span v-if="session.currentVersion">({{ t('common.version' + session.currentVersion) }})</span>
        </h3>
        
        <div class="scrollable-questions">
            <div class="question-item" v-for="q in currentQuestions" :key="q.id">
              <p class="question-text">{{ t(`newQuestions.${q.id}`, { genre: t(`genres.${selectedGenre}`), emotion: t(`emotions.${selectedEmotion}`) }) || t(`questionnaire.${q.id}`, { genre: t(`genres.${selectedGenre}`), emotion: t(`emotions.${selectedEmotion}`) }) }}</p>
              
              <!-- Text Area for Open Questions -->
              <div v-if="q.type === 'text'" class="text-input-group">
                 <textarea 
                  :value="session.getResponse(q.id)"
                  @input="e => session.setResponse(q.id, e.target.value)"
                  class="feedback-input"
                  rows="3"
                ></textarea>
              </div>

              <!-- Likert Scale for Rating Questions -->
              <div v-else class="likert-group">
                <button 
                  v-for="n in 5" 
                  :key="n"
                  class="likert-option"
                  :class="{ selected: session.getResponse(q.id) === n }"
                  @click="session.setResponse(q.id, n)"
                >
                  {{ n }}
                </button>
              </div>
            </div>
            
            <!-- Final Specific Questions -->
            <div class="final-questions" v-if="session.taskStep === 'final'">
               <div class="question-item">
                   <p class="question-text">{{ t('newQuestions.easierToFind') }}</p>
                   <div class="preference-options">
                        <button v-for="opt in preferenceOptions" :key="opt" 
                            class="preference-btn" 
                            :class="{ selected: session.getFinalResponse('discovery') === opt }"
                            @click="session.setFinalResponse('discovery', opt)">
                            {{ t(`questionnaire.preferenceOptions.${opt}`) }}
                        </button>
                   </div>
               </div>
               <div class="question-item">
                   <p class="question-text">{{ t('newQuestions.betterAxisLabels') }}</p>
                    <div class="preference-options">
                        <button v-for="opt in preferenceOptions" :key="opt" 
                            class="preference-btn" 
                             :class="{ selected: session.getFinalResponse('axis') === opt }"
                            @click="session.setFinalResponse('axis', opt)">
                            {{ t(`questionnaire.preferenceOptions.${opt}`) }}
                        </button>
                   </div>
               </div>
               <div class="question-item">
                   <p class="question-text">{{ t('newQuestions.betterLayout') }}</p>
                    <div class="preference-options">
                        <button v-for="opt in preferenceOptions" :key="opt" 
                            class="preference-btn" 
                            :class="{ selected: session.getFinalResponse('layout') === opt }"
                            @click="session.setFinalResponse('layout', opt)">
                            {{ t(`questionnaire.preferenceOptions.${opt}`) }}
                        </button>
                   </div>
               </div>
               <div class="question-item">
                   <p class="question-text">{{ t('newQuestions.overallPreference') }}</p>
                   <div class="preference-options">
                        <button v-for="opt in preferenceOptions" :key="opt" 
                            class="preference-btn" 
                            :class="{ selected: session.getFinalResponse('overall') === opt }"
                            @click="session.setFinalResponse('overall', opt)">
                            {{ t(`questionnaire.preferenceOptions.${opt}`) }}
                        </button>
                   </div>
               </div>
               <div class="question-item">
                   <p class="question-text">{{ t('newQuestions.explainChoice') }}</p>
                    <textarea 
                      :value="session.getFinalResponse('comment')"
                      @input="e => session.setFinalResponse('comment', e.target.value)"
                      class="feedback-input"
                      rows="3"
                    ></textarea>
               </div>
            </div>
        </div>

        <div class="panel-footer mt-2">
            <button 
                v-if="session.taskStep === 'final'"
                class="btn submit-btn"
                :class="{
                  'btn-primary': !session.isSubmitting && session.submitStatus === null,
                  'btn-success': session.submitStatus === 'success',
                  'btn-error': session.submitStatus === 'error'
                }"
                :disabled="session.isSubmitting"
                @click="handleSubmit"
              >
                <span v-if="session.isSubmitting" class="spinner"></span>
                <span v-else-if="session.submitStatus === 'success'">✓ {{ t('common.submitSuccess') }}</span>
                <span v-else-if="session.submitStatus === 'error'">✗ {{ t('common.submitError') }}</span>
                <span v-else>{{ t('common.submit') }}</span>
            </button>
            <button 
                v-else
                class="btn btn-primary next-btn" 
                @click="nextTaskStep"
                :disabled="!canProceed"
            >
                {{ t('common.next') }}
            </button>
             <p v-if="!canProceed" class="text-xs text-red-400 mt-1">
                {{ validationMessage }}
             </p>
        </div>
        
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useSessionStore } from '../stores/session'

const { t, locale } = useI18n()
const router = useRouter()
const session = useSessionStore()

// API base URL
const API_BASE = ''
const MUSIC_API_BASE = 'https://neon.zeabur.app'

// Refs
const plotCanvas = ref(null)
const plotContainer = ref(null)
const audioPlayer = ref(null)

// Data
const genres = ref([])
const emotions = ref([])

// Questions Configuration
const questionsGuided = [
  { id: 'genreEmotionMatch' },
  { id: 'transitionNatural' },
  { id: 'hasJump', type: 'text' }, // Assuming yes/no + text, simplifying to text for layout
  { id: 'axisUnderstandable' }
]

const questionsFree = [
  { id: 'genreEmotionMatchFree' },
  { id: 'discoverability' },
  { id: 'serendipity' },
  { id: 'coherence' },
  { id: 'satisfaction' },
  { id: 'axisNavigation' },
  { id: 'clusterDistinct' }
]

const preferenceOptions = ['a', 'b', 'same']

// State
const selectedGenre = ref('POP')
const selectedEmotion = ref('Happiness')
const isLoading = ref(false)
const analysisResult = ref(null)
const plotData = ref([])
const clusterReps = ref([])
const axisLabels = ref({
  x: 'PC1', xR: '0.00', xLow: '', xHigh: '',
  y: 'PC2', yR: '0.00', yLow: '', yHigh: ''
})

// UI State
const toastMessage = ref('')
const isTransition = computed(() => session.taskStep === 'transition')

// Controls Locking
const isControlsLocked = computed(() => {
    // Locked during Welcome, Guided Tasks, Transition, and Final
    return ['welcome', 'guided_A', 'guided_B', 'final'].includes(session.taskStep)
})

// Current Questions based on Step
const currentQuestions = computed(() => {
    if (session.taskStep.includes('guided')) return questionsGuided
    if (session.taskStep.includes('free')) return questionsFree
    return []
})

const currentStepTitle = computed(() => {
     if (session.taskStep.includes('guided')) return t('ui.guidedTask')
     if (session.taskStep.includes('free')) return t('ui.freeExplore')
     if (session.taskStep === 'final') return t('questionnaire.preference')
     return ''
})

const stepInstruction = computed(() => {
    if (session.taskStep.includes('guided')) return t('task.guidedInstruction')
    if (session.taskStep.includes('free')) return t('task.freeExploreInstruction')
    return t('explorer.clickToPlay')
})

// Audio state
const currentSong = ref(null)
const isPlaying = ref(false)
const isLoadingAudio = ref(false)
const audioError = ref(null)
const progress = ref(0)
const currentTime = ref(0)
const duration = ref(30)
// Initialize these as refs to be safe
const songDuration = ref(0)
const startOffset = ref(0)

// Plot coordinate mapping
const plotBounds = ref({ minX: -6, maxX: 6, minY: -5, maxY: 5 })
const clusterColors = ['#667eea', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#06b6d4']

function getClusterColor(index) {
  return clusterColors[index % clusterColors.length]
}

const yAxisHighHtml = computed(() => axisLabels.value.yHigh.replace(/ \/ /g, '<br>'))
const yAxisLowHtml = computed(() => axisLabels.value.yLow.replace(/ \/ /g, '<br>'))

// Load initial data
onMounted(async () => {
  await loadInfo()
  
  // If coming from Welcome Page (Guided A), auto-start
  if (session.taskStep === 'guided_A') {
      runAnalysis()
  }

  window.addEventListener('resize', drawPlot)
})

onUnmounted(() => {
    window.removeEventListener('resize', drawPlot)
})

async function loadInfo() {
  try {
    const res = await fetch(`${API_BASE}/api/info`)
    const data = await res.json()
    genres.value = data.genres
    emotions.value = data.emotions
    
    // Default selection for Guided Task (Pop + Happiness)
    // Find Pop and Happiness in lists or fallback
    if (genres.value.includes('POP')) selectedGenre.value = 'POP'
    if (emotions.value.includes('Happiness')) selectedEmotion.value = 'Happiness'
    
  } catch (err) {
      console.error('Failed to load info', err)
       genres.value = ['POP']
       emotions.value = ['Happiness']
  }
}

// ═══════════════════════════════════════════════════════════
// Wizard Flow Logic
// ═══════════════════════════════════════════════════════════

function startExperiment() {
    session.initSession()
    session.taskStep = 'guided_A'
    session.currentTaskType = 'guided'
    session.currentVersion = 'A'
    runAnalysis() // Auto-run for guided
}

function handleTransitionNext() {
    session.taskStep = 'free_setup' // A pseudo-state where we wait for user to select and click Analyze
    // We remain in free_setup until analyze passes
    // Reset selection to force user choice? Or keep defaults?
    // Let's keep defaults but user can change.
}

async function handleAnalyzeClick() {
    // 1. Interactive Pre-check
    if (session.taskStep === 'free_setup' || session.taskStep.includes('free')) {
        isLoading.value = true
        try {
            const res = await fetch(`${API_BASE}/api/check`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    genre: selectedGenre.value,
                    emotion: selectedEmotion.value
                })
            })
            const data = await res.json()
            
            if (!data.valid) {
                showToast(t('ui.insufficientSongs'))
                isLoading.value = false
                return 
            }
            
            // If valid, proceed to analysis
            runAnalysis()
        } catch (err) {
            console.error('Check failed:', err)
            // If check fails (e.g. network), try running analysis anyway? 
            // Or show error. Let's try analysis as fallback or show error.
            // Safer to just try analysis or show generic error.
            runAnalysis() // Fallback
        }
    } else {
        runAnalysis()
    }
}

function nextTaskStep() {
    session.resetListenedForTask() // Clear listening progress for next step
    
    switch (session.taskStep) {
        case 'guided_A':
            session.taskStep = 'guided_B'
            session.currentVersion = 'B'
            switchVersion('B')
            break
        case 'guided_B':
            session.taskStep = 'transition'
            // Hide plot data?
            break
        case 'free_A':
             session.taskStep = 'free_B'
             session.currentVersion = 'B'
             switchVersion('B')
             break
        case 'free_B':
            session.taskStep = 'final'
            break
    }
}

const canProceed = computed(() => {
    // Validation Logic
    if (session.taskStep.includes('guided')) {
        return session.canProceedFromGuided()
    }
    if (session.taskStep.includes('free')) {
        // Check questions answered
        // Check listening requirements
        return session.canProceedFromFree()
    }
    return true
})

const validationMessage = computed(() => {
    if (canProceed.value) return ''
    if (session.taskStep.includes('guided')) {
        return t('task.progress.minRequired', { min: 1 })
    }
    if (session.taskStep.includes('free')) {
        return t('task.progress.minRequired', { min: 3 })
    }
    return ''
})


// ═══════════════════════════════════════════════════════════
// Analysis
// ═══════════════════════════════════════════════════════════

function switchVersion(version) {
  session.currentVersion = version
  if (selectedGenre.value && selectedEmotion.value) {
    runAnalysis()
  }
}

async function runAnalysis(isManualCheck = false) {
  if (!selectedGenre.value || !selectedEmotion.value) return
  
  isLoading.value = true
  toastMessage.value = ''
  
  // Use session state for request
  session.currentGenre = selectedGenre.value
  session.currentEmotion = selectedEmotion.value
  
  // Determine version based on step if needed, or rely on session.currentVersion
  // In Wizard flow, session.currentVersion controls the request
  
  try {
    const res = await fetch(`${API_BASE}/api/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        genre: selectedGenre.value,
        emotion: selectedEmotion.value,
        version: session.currentVersion,
        version_mapping: session.versionMapping,
        auto_k: true,
        manual_k: 3
      })
    })
    
    const data = await res.json()
    
    // Check for "Too few songs" error
    if (data.error && data.count < 3) {
         if (isManualCheck) {
             showToast(t('ui.insufficientSongs'))
             return // Don't proceed
         }
    }
    
    // If we are in free_setup and analysis succeeded (count >= 3), start Free A
    if (session.taskStep === 'free_setup' && !data.error) {
        session.taskStep = 'free_A'
        session.currentTaskType = 'free'
        session.currentVersion = 'A'
        // Need to ensure we analyze for Version A specifically if we were just checking
        // But logic is: User selects -> Analyze. If they are in setup, they start A.
        // If currentVersion was A, good.
    }

    if (data.error) {
      console.error('Analysis error:', data.error)
      plotData.value = []
      clusterReps.value = []
      drawPlot()
      return
    }
    
    analysisResult.value = data
    plotData.value = data.points
    clusterReps.value = data.cluster_reps.map((rep, i) => ({
      ...rep,
      color: getClusterColor(i)
    }))
    
    // Update axis labels
    if (data.axis) {
       updateAxisLabels(data.axis)
    }
    
    // Calculate plot bounds
    calculateBounds()
    
    await nextTick()
    drawPlot()
    
  } catch (err) {
    console.error('Analysis failed:', err)
    if (isManualCheck) showToast(t('ui.loadFailed'))
  } finally {
    isLoading.value = false
  }
}

function showToast(msg) {
    toastMessage.value = msg
    setTimeout(() => { toastMessage.value = '' }, 3000)
}

function updateAxisLabels(axisData) {
      const lang = locale.value
      const getLabel = (obj) => {
        if (typeof obj === 'string') return obj
        return obj?.[lang] || obj?.en || 'PC'
      }
      const getPolarity = (obj, key) => {
        if (!obj) return ''
        const langObj = obj[lang] || obj.en || obj
        const val = langObj?.[key] || langObj || ''
        return typeof val === 'string' ? val.split('\n').join(' / ') : ''
      }
      axisLabels.value = {
        x: getLabel(axisData.x.label),
        xR: axisData.x.r || '0.00',
        xLow: getPolarity(axisData.x.polarity, 'low'),
        xHigh: getPolarity(axisData.x.polarity, 'high'),
        y: getLabel(axisData.y.label),
        yR: axisData.y.r || '0.00',
        yLow: getPolarity(axisData.y.polarity, 'low'),
        yHigh: getPolarity(axisData.y.polarity, 'high')
      }
}

function calculateBounds() {
    if (plotData.value.length > 0) {
      const xs = plotData.value.map(p => p.x)
      const ys = plotData.value.map(p => p.y)
      const margin = 0.5
      plotBounds.value = {
        minX: Math.min(...xs) - margin,
        maxX: Math.max(...xs) + margin,
        minY: Math.min(...ys) - margin,
        maxY: Math.max(...ys) + margin
      }
    }
}

// ═══════════════════════════════════════════════════════════
// Plot Logic (Keep existing)
// ═══════════════════════════════════════════════════════════
function drawPlot() {
  const canvas = plotCanvas.value
  const container = plotContainer.value
  if (!canvas || !container) return
  
  const rect = container.getBoundingClientRect()
  const dpr = window.devicePixelRatio || 1
  
  canvas.width = rect.width * dpr
  canvas.height = rect.height * dpr
  canvas.style.width = rect.width + 'px'
  canvas.style.height = rect.height + 'px'
  
  const ctx = canvas.getContext('2d')
  ctx.scale(dpr, dpr)
  
  const width = rect.width
  const height = rect.height
  const padding = { left: 50, right: 20, top: 20, bottom: 40 }
  const plotWidth = width - padding.left - padding.right
  const plotHeight = height - padding.top - padding.bottom
  
  ctx.fillStyle = 'rgba(15, 15, 26, 0.9)'
  ctx.fillRect(0, 0, width, height)
  
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)'
  ctx.lineWidth = 1
  
  for (let i = 0; i <= 10; i++) {
    const x = padding.left + (i / 10) * plotWidth
    ctx.beginPath()
    ctx.moveTo(x, padding.top)
    ctx.lineTo(x, height - padding.bottom)
    ctx.stroke()
    
    const y = padding.top + (i / 10) * plotHeight
    ctx.beginPath()
    ctx.moveTo(padding.left, y)
    ctx.lineTo(width - padding.right, y)
    ctx.stroke()
  }
  
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)'
  ctx.lineWidth = 2
  ctx.beginPath()
  ctx.moveTo(padding.left, height - padding.bottom)
  ctx.lineTo(width - padding.right, height - padding.bottom)
  ctx.moveTo(padding.left, height - padding.bottom)
  ctx.lineTo(padding.left, padding.top)
  ctx.stroke()
  
  if (plotData.value.length === 0) {
    ctx.fillStyle = 'rgba(255, 255, 255, 0.5)'
    ctx.font = '14px Inter'
    ctx.textAlign = 'center'
    ctx.fillText(analysisResult.value?.error || (session.taskStep === 'transition' ? 'Ready to free explore' : 'No data'), width / 2, height / 2)
    return
  }
  
  const { minX, maxX, minY, maxY } = plotBounds.value
  
  function toCanvasX(x) {
    return padding.left + ((x - minX) / (maxX - minX)) * plotWidth
  }
  
  function toCanvasY(y) {
    return height - padding.bottom - ((y - minY) / (maxY - minY)) * plotHeight
  }
  
  for (const point of plotData.value) {
    const px = toCanvasX(point.x)
    const py = toCanvasY(point.y)
    
    const listenedState = session.getListenedState(point.id)
    const isLiked = session.isLiked(point.id)
    const isCurrentSong = point.id === currentSong.value
    
    ctx.beginPath()
    ctx.arc(px, py, 5, 0, Math.PI * 2)
    
    if (listenedState === 'listened') {
      ctx.fillStyle = point.color + 'AA'
      ctx.fill()
      ctx.strokeStyle = '#10b981'
      ctx.lineWidth = 2
      ctx.stroke()
    } else if (listenedState === 'skipped') {
      ctx.fillStyle = point.color + '88'
      ctx.fill()
      ctx.strokeStyle = '#6b7280'
      ctx.lineWidth = 1.5
      ctx.stroke()
    } else {
      ctx.fillStyle = point.color
      ctx.fill()
    }
    
    if (isCurrentSong) {
      ctx.strokeStyle = 'white'
      ctx.lineWidth = 3
      ctx.stroke()
    }
    
    if (isLiked) {
      ctx.fillStyle = '#ef4444'
      ctx.font = '10px sans-serif'
      ctx.fillText('❤', px - 5, py - 8)
    }
  }
  
  for (let i = 0; i < clusterReps.value.length; i++) {
    const rep = clusterReps.value[i]
    const px = toCanvasX(rep.x)
    const py = toCanvasY(rep.y)
    drawStar(ctx, px, py, 5, 12, 6, rep.color)
  }
  
  ctx.fillStyle = 'rgba(255, 255, 255, 0.5)'
  ctx.font = '10px Inter'
  ctx.textAlign = 'center'
  
  const xStep = (maxX - minX) / 5
  for (let i = 0; i <= 5; i++) {
    const val = minX + i * xStep
    const x = toCanvasX(val)
    ctx.fillText(val.toFixed(1), x, height - padding.bottom + 15)
  }
  
  ctx.textAlign = 'right'
  const yStep = (maxY - minY) / 5
  for (let i = 0; i <= 5; i++) {
    const val = minY + i * yStep
    const y = toCanvasY(val)
    ctx.fillText(val.toFixed(1), padding.left - 5, y + 3)
  }
}

function resultColor(i) { return clusterColors[i % clusterColors.length] }

function drawStar(ctx, cx, cy, spikes, outerRadius, innerRadius, color) {
  let rot = Math.PI / 2 * 3
  let x = cx
  let y = cy
  const step = Math.PI / spikes

  ctx.beginPath()
  ctx.moveTo(cx, cy - outerRadius)
  
  for (let i = 0; i < spikes; i++) {
    x = cx + Math.cos(rot) * outerRadius
    y = cy + Math.sin(rot) * outerRadius
    ctx.lineTo(x, y)
    rot += step

    x = cx + Math.cos(rot) * innerRadius
    y = cy + Math.sin(rot) * innerRadius
    ctx.lineTo(x, y)
    rot += step
  }
  
  ctx.lineTo(cx, cy - outerRadius)
  ctx.closePath()
  ctx.fillStyle = color
  ctx.fill()
  ctx.strokeStyle = 'white'
  ctx.lineWidth = 1.5
  ctx.stroke()
}

// ═══════════════════════════════════════════════════════════
// Interaction Logic
// ═══════════════════════════════════════════════════════════

function handlePlotClick(event) {
  // Disable clicks in transition or welcome
  if (session.taskStep === 'welcome' || session.taskStep === 'transition') return

  const canvas = plotCanvas.value
  const rect = canvas.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  
  const padding = { left: 50, right: 20, top: 20, bottom: 40 }
  const plotWidth = rect.width - padding.left - padding.right
  const plotHeight = rect.height - padding.top - padding.bottom
  
  const { minX, maxX, minY, maxY } = plotBounds.value
  
  for (const point of plotData.value) {
    const px = padding.left + ((point.x - minX) / (maxX - minX)) * plotWidth
    const py = rect.height - padding.bottom - ((point.y - minY) / (maxY - minY)) * plotHeight
    
    if (Math.abs(x - px) < 10 && Math.abs(y - py) < 10) {
      playSong(point.id, point.x, point.y)
      break
    }
  }
}

function handlePlotHover(event) {
  if (session.taskStep === 'welcome' || session.taskStep === 'transition') return
  const canvas = plotCanvas.value
  const rect = canvas.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  const padding = { left: 50, right: 20, top: 20, bottom: 40 }
  const plotWidth = rect.width - padding.left - padding.right
  const plotHeight = rect.height - padding.top - padding.bottom
  
  const { minX, maxX, minY, maxY } = plotBounds.value
  
  let isOverPoint = false
  for (const point of plotData.value) {
    const px = padding.left + ((point.x - minX) / (maxX - minX)) * plotWidth
    const py = rect.height - padding.bottom - ((point.y - minY) / (maxY - minY)) * plotHeight
    if (Math.abs(x - px) < 10 && Math.abs(y - py) < 10) {
      isOverPoint = true
      break
    }
  }
  canvas.style.cursor = isOverPoint ? 'pointer' : 'default'
}

let audioInitialized = false
function onAudioCanPlay() {
  if (audioInitialized) return
  audioInitialized = true
  
  const audio = audioPlayer.value
  isLoadingAudio.value = false
  songDuration.value = audio.duration
  startOffset.value = Math.max(0, (songDuration.value / 2) - 15)
  audio.currentTime = startOffset.value
  duration.value = 30
  audio.play()
  isPlaying.value = true
  session.recordPlayStart(currentSong.value)
  drawPlot()
}

function onAudioError(e) {
  console.error('Audio error:', e)
  isLoadingAudio.value = false
  audioError.value = 'Failed'
  audioInitialized = false
}

function onTimeUpdate() {
  const audio = audioPlayer.value
  if (!audio) return
  const elapsed = audio.currentTime - startOffset.value
  currentTime.value = Math.max(0, elapsed)
  if (duration.value > 0) progress.value = (currentTime.value / duration.value) * 100
  if (elapsed >= 30) {
    audio.pause()
    isPlaying.value = false
    session.recordPlayEnd()
  }
}

function onAudioLoaded() {
  const audio = audioPlayer.value
  if (audio) duration.value = Math.min(audio.duration, 30)
}

function onAudioEnded() { isPlaying.value = false; session.recordPlayEnd() }

async function playSong(songId, x = null, y = null) {
  session.recordPlayEnd()
  currentSong.value = songId
  isLoadingAudio.value = true
  audioError.value = null
  audioInitialized = false
  
  if (x !== null && y !== null) session.recordClick(songId, x, y)
  
  try {
    const url = `${MUSIC_API_BASE}/song/url?id=${songId}`
    const res = await fetch(url)
    const data = await res.json()
    if (data.data && data.data[0] && data.data[0].url) {
      const audio = audioPlayer.value
      audio.src = data.data[0].url
      audio.load()
    } else {
      isLoadingAudio.value = false
      audioError.value = 'No URL'
    }
  } catch (err) {
    isLoadingAudio.value = false
    audioError.value = 'Error'
  }
}

function toggleLike() {
  if (currentSong.value) {
    session.toggleLike(currentSong.value)
    drawPlot()
  }
}

function togglePlay() {
  const audio = audioPlayer.value
  if (!audio || !currentSong.value) return
  if (isPlaying.value) {
    audio.pause()
    isPlaying.value = false
  } else {
    if (audio.currentTime >= startOffset.value + 30 || audio.currentTime < startOffset.value) audio.currentTime = startOffset.value
    audio.play()
    isPlaying.value = true
  }
}
function stopPlay() {
  const audio = audioPlayer.value
  if (!audio) return
  audio.pause()
  audio.currentTime = 0
  isPlaying.value = false
  progress.value = 0
  currentTime.value = 0
}
function seekAudio() {}

function formatTime(s) {
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return `${m}:${sec.toString().padStart(2, '0')}`
}

async function handleSubmit() {
    const success = await session.submitSession()
    if (success) {
        setTimeout(() => {
            router.push('/complete')
        }, 1500)
    }
}
</script>

<style scoped>
/* Reuse existing styles plus new wizard styles */
.explore-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #0f0f1a;
  color: #fff;
  overflow: hidden;
}

.explore-container {
  flex: 1;
  display: flex;
  gap: 1rem;
  padding: 1rem;
  height: 100%;
}

.card {
  background: rgba(30, 30, 40, 0.8);
  border-radius: 12px;
  padding: 1.5rem;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
}

.control-panel { width: 280px; transition: opacity 0.3s; }
.control-panel.disabled { opacity: 0.6; pointer-events: none; }

.questionnaire-panel { width: 320px; display: flex; flex-direction: column; }
.plot-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: rgba(20, 20, 30, 0.5);
  border-radius: 12px;
  padding: 1rem;
  position: relative;
}

.scrollable-questions {
    flex: 1;
    overflow-y: auto;
    padding-right: 8px;
}

.panel-footer {
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    padding-top: 1rem;
}

.transition-overlay {
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.85);
    z-index: 10;
    display: flex;
    justify-content: center;
    align-items: center;
    border-radius: 8px;
}

.transition-card {
    background: #1e1e28;
    padding: 2rem;
    border-radius: 12px;
    text-align: center;
    max-width: 400px;
    border: 1px solid rgba(255,255,255,0.2);
}

.toast-notification {
    position: absolute;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(239, 68, 68, 0.9);
    color: white;
    padding: 10px 20px;
    border-radius: 20px;
    z-index: 100;
    font-weight: bold;
    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    border: 1px solid rgba(255,255,255,0.2);
}

/* Original styles below */
.panel-title { font-size: 0.9rem; font-weight: 600; color: #a0a0b0; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.05em; }
.form-select { width: 100%; padding: 0.6rem; background: #2a2a35; border: 1px solid #4ade8055; border-radius: 6px; color: #fff; margin-bottom: 0.5rem; }
.version-toggle { display: flex; gap: 0.5rem; }
.version-btn { flex: 1; padding: 0.6rem; background: #2a2a35; border: 1px solid transparent; border-radius: 6px; color: #a0a0b0; cursor: pointer; transition: all 0.2s; }
.version-btn.active { background: #4ade80; color: #000; font-weight: bold; }
.analyze-btn { width: 100%; font-weight: bold; padding: 0.8rem; background: #6366f1; border: none; border-radius: 6px; cursor: pointer; color: white; transition: background 0.2s; }
.analyze-btn:disabled { background: #4b4b5a; cursor: not-allowed; }

.plot-wrapper { flex: 1; display: flex; overflow: hidden; position: relative; }
.plot-container { flex: 1; position: relative; }
.plot-header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.5rem; }
.plot-title { font-size: 1.5rem; font-weight: bold; }
.plot-subtitle { color: #a0a0b0; font-size: 0.9rem; }

.y-axis-outer { width: 60px; display: flex; flex-direction: column; align-items: center; justify-content: space-between; padding: 20px 0; border-right: 1px solid rgba(255,255,255,0.1); margin-right: 10px; }
.y-pole-top, .y-pole-bottom { font-size: 0.8rem; color: #4ade80; text-align: center; font-weight: bold; min-height: 40px; }
.y-axis-name { writing-mode: vertical-lr; text-orientation: mixed; color: #a0a0b0; font-size: 0.8rem; letter-spacing: 2px; }

.x-axis-container { height: 40px; display: flex; justify-content: space-between; align-items: center; padding: 0 60px 0 80px; margin-top: 5px; border-top: 1px solid rgba(255,255,255,0.1); }
.axis-pole { font-size: 0.8rem; color: #4ade80; font-weight: bold; }
.axis-name { color: #a0a0b0; font-size: 0.8rem; letter-spacing: 2px; }

.question-item { margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid rgba(255,255,255,0.05); }
.question-text { font-size: 0.95rem; margin-bottom: 0.8rem; line-height: 0.8 rem; }
.likert-group { display: flex; justify-content: space-between; gap: 0.5rem; }
.likert-option { width: 36px; height: 36px; border-radius: 50%; border: 1px solid #4a4a5a; background: transparent; color: #fff; cursor: pointer; transition: all 0.2s; }
.likert-option:hover { border-color: #6366f1; }
.likert-option.selected { background: #6366f1; border-color: #6366f1; transform: scale(1.1); }
.feedback-input { width: 100%; background: #2a2a35; border: 1px solid #4a4a5a; border-radius: 6px; padding: 0.8rem; color: white; font-family: inherit; }

.preference-options { display: flex; flex-direction: column; gap: 0.5rem; }
.preference-btn { padding: 0.8rem; background: #2a2a35; border: 1px solid #4a4a5a; border-radius: 6px; color: #fff; text-align: left; cursor: pointer; }
.preference-btn.selected { background: #4ade80; color: #000; border-color: #4ade80; font-weight: bold; }

.spinner { display: inline-block; width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3); border-radius: 50%; border-top-color: #fff; animation: spin 1s linear infinite; margin-right: 0.5rem; }
@keyframes spin { to { transform: rotate(360deg); } }

.cluster-reps { margin-top: 1rem; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 1rem; }
.cluster-rep-item { display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem; border-radius: 6px; cursor: pointer; transition: background 0.2s; }
.cluster-rep-item:hover { background: rgba(255,255,255,0.05); }
.cluster-rep-item.active { background: rgba(99, 102, 241, 0.2); }
.cluster-label { font-size: 0.7rem; padding: 2px 6px; border-radius: 4px; color: #fff; font-weight: bold; width: 28px; text-align: center; }
.cluster-song { font-size: 0.85rem; color: #ccc; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.player-section { background: rgba(0,0,0,0.2); padding: 1rem; border-radius: 8px; }
.song-id { font-family: monospace; font-size: 0.9rem; color: #4ade80; margin-bottom: 0.5rem; }
.player-controls { display: flex; gap: 1rem; margin-bottom: 0.5rem; }
.player-btn { width: 36px; height: 36px; border-radius: 50%; border: none; background: #4b4b5a; color: white; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.2s; }
.player-btn:hover:not(:disabled) { background: #6366f1; transform: scale(1.1); }
.player-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.like-btn.liked { background: #fca5a5; }
.progress-bar { height: 4px; background: rgba(255,255,255,0.2); border-radius: 2px; cursor: pointer; position: relative; }
.progress-fill { height: 100%; background: #4ade80; border-radius: 2px; position: absolute; left: 0; top: 0; }
.time-display { font-size: 0.75rem; color: #888; text-align: right; margin-top: 4px; }
.loading-indicator, .error-indicator { font-size: 0.8rem; color: #fbbf24; margin-bottom: 0.5rem; display: flex; align-items: center; }
.error-indicator { color: #ef4444; }
.task-progress { font-size: 0.8rem; color: #94a3b8; border-top: 1px solid rgba(255,255,255,0.1); margin-top: 0.5rem; padding-top: 0.5rem; }
</style>
