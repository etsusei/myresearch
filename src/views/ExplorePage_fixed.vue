<template>
  <div class="explore-page">
    <div class="explore-container">
      <!-- Left Panel: Controls -->
      <aside class="control-panel card">
        <h3 class="panel-title">{{ t('explorer.selectGenre') }}</h3>
        <select v-model="selectedGenre" class="form-select">
          <option v-for="g in genres" :key="g" :value="g">{{ t(`genres.${g}`) || g }}</option>
        </select>
        
        <h3 class="panel-title mt-2">{{ t('explorer.selectEmotion') }}</h3>
        <select v-model="selectedEmotion" class="form-select">
          <option v-for="e in emotions" :key="e" :value="e">{{ t(`emotions.${e}`) || e }}</option>
        </select>
        
        <h3 class="panel-title mt-2">{{ t('explorer.selectVersion') }}</h3>
        <div class="version-toggle">
          <button 
            class="version-btn" 
            :class="{ active: session.currentVersion === 'A' }"
            @click="switchVersion('A')"
          >
            {{ t('common.versionA') }}
          </button>
          <button 
            class="version-btn"
            :class="{ active: session.currentVersion === 'B' }"
            @click="switchVersion('B')"
          >
            {{ t('common.versionB') }}
          </button>
        </div>
        
        <button 
          class="btn btn-primary mt-2 analyze-btn" 
          @click="runAnalysis"
          :disabled="isLoading"
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
          <audio 
            ref="audioPlayer" 
            @timeupdate="onTimeUpdate"
            @ended="onAudioEnded"
            @loadedmetadata="onAudioLoaded"
            @error="onAudioError"
            crossorigin="anonymous"
          ></audio>
          <div class="player-controls">
            <button class="player-btn" @click="togglePlay" :disabled="!currentSong">
              {{ isPlaying ? '⏸' : '▶' }}
            </button>
            <button class="player-btn" @click="stopPlay" :disabled="!currentSong">■</button>
          </div>
          <div class="progress-bar" @click="seekAudio">
            <div class="progress-fill" :style="{ width: progress + '%' }"></div>
          </div>
          <div class="time-display">{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</div>
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
          <span class="plot-subtitle">({{ t('explorer.clickToPlay') || 'Click any point to Play' }})</span>
        </div>
        <div class="plot-wrapper">
          <!-- Y-axis label (vertical on left) -->
          <div class="y-axis-container">
            <div class="y-axis-label-vertical">
              <span class="axis-pole-label">{{ currentAxisLabels.yHigh }}</span>
              <span class="axis-name">[{{ t('explorer.secondaryAxis') }}] {{ currentAxisLabels.y }} (r≈{{ currentAxisLabels.yR }})</span>
              <span class="axis-pole-label">{{ currentAxisLabels.yLow }}</span>
            </div>
          </div>
          
          <!-- Plot canvas -->
          <div class="plot-container" ref="plotContainer">
            <canvas ref="plotCanvas" @click="handlePlotClick"></canvas>
          </div>
        </div>
        
        <!-- X-axis label (horizontal below) -->
        <div class="x-axis-container">
          <span class="axis-pole-label">{{ currentAxisLabels.xLow }}</span>
          <span class="axis-name">[{{ t('explorer.primaryAxis') }}] {{ currentAxisLabels.x }} (r≈{{ currentAxisLabels.xR }})</span>
          <span class="axis-pole-label">{{ currentAxisLabels.xHigh }}</span>
        </div>
      </main>

      <!-- Right: Questionnaire -->
      <aside class="questionnaire-panel card">
        <h3 class="panel-title">{{ t('questionnaire.rateExperience') }} ({{ t('common.version' + session.currentVersion) }})</h3>
        
        <div class="question-item" v-for="q in questions" :key="q.id">
          <p class="question-text">{{ t(`questionnaire.${q.id}`) }}</p>
          <div class="likert-group">
            <button 
              v-for="n in 5" 
              :key="n"
              class="likert-option"
              :class="{ selected: session.responses[`version${session.currentVersion}`][q.id] === n }"
              @click="session.setResponse(q.id, n)"
            >
              {{ n }}
            </button>
          </div>
        </div>
        
        <!-- Final questions (after both versions explored) -->
        <div class="final-questions mt-3" v-if="showFinalQuestions">
          <h3 class="panel-title highlight">{{ t('questionnaire.preference') }}</h3>
          <div class="preference-options">
            <button 
              v-for="opt in preferenceOptions" 
              :key="opt"
              class="preference-btn"
              :class="{ selected: session.responses.final.preference === opt }"
              @click="session.setFinalResponse('preference', opt)"
            >
              {{ t(`questionnaire.preferenceOptions.${opt}`) }}
            </button>
          </div>
          
          <div class="feedback-section mt-2">
            <label class="form-label">{{ t('questionnaire.feedback') }}</label>
            <textarea 
              v-model="session.responses.final.feedback"
              class="feedback-input"
              :placeholder="t('questionnaire.feedbackPlaceholder')"
              rows="3"
            ></textarea>
          </div>
        </div>
        
        <!-- Submit button - ALWAYS visible -->
        <button 
          class="btn submit-btn mt-3"
          :class="{
            'btn-primary': !session.isSubmitting && session.submitStatus === null,
            'btn-success': session.submitStatus === 'success',
            'btn-error': session.submitStatus === 'error'
          }"
          :disabled="!session.isComplete || session.isSubmitting"
          @click="handleSubmit"
        >
          <span v-if="session.isSubmitting" class="spinner"></span>
          <span v-else-if="session.submitStatus === 'success'">✓ {{ t('common.submitSuccess') }}</span>
          <span v-else-if="session.submitStatus === 'error'">✗ {{ t('common.submitError') }}</span>
          <span v-else>{{ t('common.submit') }}</span>
        </button>
        
        <!-- Progress indicator -->
        <div class="progress-indicator mt-2">
          <p class="progress-text">
            {{ t('explorer.explorations') || 'Explorations' }}: {{ session.explorationsCount }} / 3
          </p>
          <p class="progress-text" v-if="!showFinalQuestions">
            {{ t('explorer.rateHint') || 'Rate both versions to unlock final questions' }}
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

// API base URL - use empty string so Vite proxy handles /api/* requests
const API_BASE = ''
const MUSIC_API_BASE = 'https://neon.zeabur.app'

// Refs
const plotCanvas = ref(null)
const plotContainer = ref(null)
const audioPlayer = ref(null)

// Data - will be loaded from API
const genres = ref([])
const emotions = ref([])

const questions = [
  { id: 'discoverability' },
  { id: 'serendipity' },
  { id: 'coherence' },
  { id: 'satisfaction' }
]

const preferenceOptions = ['a', 'b', 'same']

// State
const selectedGenre = ref('')
const selectedEmotion = ref('')
const isLoading = ref(false)
const analysisResult = ref(null)
const plotData = ref([])
const clusterReps = ref([])
const rawAxisLabels = ref(null)

// Audio state
const currentSong = ref(null)
const isPlaying = ref(false)
const progress = ref(0)
const currentTime = ref(0)
const duration = ref(30)

// Plot coordinate mapping
const plotBounds = ref({ minX: -6, maxX: 6, minY: -5, maxY: 5 })

// Colors for clusters
const clusterColors = ['#667eea', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#06b6d4']
function getClusterColor(index) {
  return clusterColors[index % clusterColors.length]
}

// Computed axis labels based on current language
const currentAxisLabels = computed(() => {
  if (!rawAxisLabels.value) {
    return {
      x: 'PC1', xR: '0.00', xLow: '', xHigh: '',
      y: 'PC2', yR: '0.00', yLow: '', yHigh: ''
    }
  }
  
  const lang = locale.value
  const xData = rawAxisLabels.value.x
  const yData = rawAxisLabels.value.y
  
  return {
    x: xData.label[lang] || xData.label.en || 'PC1',
    xR: xData.r || '0.00',
    xLow: (xData.polarity[lang]?.low || xData.polarity.en?.low || '').split('\n')[0],
    xHigh: (xData.polarity[lang]?.high || xData.polarity.en?.high || '').split('\n')[0],
    y: yData.label[lang] || yData.label.en || 'PC2',
    yR: yData.r || '0.00',
    yLow: (yData.polarity[lang]?.low || yData.polarity.en?.low || '').split('\n')[0],
    yHigh: (yData.polarity[lang]?.high || yData.polarity.en?.high || '').split('\n')[0]
  }
})

// Show final questions when both versions have been rated
const showFinalQuestions = computed(() => {
  const vA = session.responses.versionA
  const vB = session.responses.versionB
  const requiredQuestions = ['discoverability', 'serendipity', 'coherence', 'satisfaction']
  const vAComplete = requiredQuestions.every(q => vA[q] !== undefined)
  const vBComplete = requiredQuestions.every(q => vB[q] !== undefined)
  return vAComplete && vBComplete
})

// Load available genres and emotions from API
async function loadInfo() {
  try {
    const res = await fetch(`${API_BASE}/api/info`)
    const data = await res.json()
    genres.value = data.genres
    emotions.value = data.emotions
    
    if (genres.value.length > 0) selectedGenre.value = genres.value[0]
    if (emotions.value.length > 0) selectedEmotion.value = emotions.value[0]
  } catch (err) {
    console.error('Failed to load info:', err)
    // Fallback
    genres.value = ['POP', 'Rock/Metal', 'Electronic', 'EDM', 'Jazz']
    emotions.value = ['Happiness', 'Excitement', 'Healing', 'Sadness', 'Nostalgia']
    selectedGenre.value = 'POP'
    selectedEmotion.value = 'Happiness'
  }
}

// Switch version and re-analyze
function switchVersion(version) {
  session.currentVersion = version
  if (selectedGenre.value && selectedEmotion.value) {
    runAnalysis()
  }
}

// Run analysis via backend API
async function runAnalysis() {
  if (!selectedGenre.value || !selectedEmotion.value) return
  
  isLoading.value = true
  session.currentGenre = selectedGenre.value
  session.currentEmotion = selectedEmotion.value
  
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
    
    if (data.error) {
      console.error('Analysis error:', data.error)
      plotData.value = []
      clusterReps.value = []
      analysisResult.value = { count: data.count || 0, k: 0, error: data.error }
      rawAxisLabels.value = null
      drawPlot()
      return
    }
    
    analysisResult.value = data
    plotData.value = data.points
    clusterReps.value = data.cluster_reps.map((rep, i) => ({
      ...rep,
      color: getClusterColor(i)
    }))
    
    // Store raw axis labels
    rawAxisLabels.value = data.axis
    
    // Calculate plot bounds
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
    
    session.trackExploration()
    
    await nextTick()
    drawPlot()
    
  } catch (err) {
    console.error('Analysis failed:', err)
  } finally {
    isLoading.value = false
  }
}

// Watch locale changes to redraw axis labels
watch(locale, () => {
  if (rawAxisLabels.value) {
    nextTick(() => drawPlot())
  }
})

// Draw scatter plot matching gui_cluster_v2.py style
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
  
  // Clear
  ctx.fillStyle = 'rgba(15, 15, 26, 0.9)'
  ctx.fillRect(0, 0, width, height)
  
  // Draw grid
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)'
  ctx.lineWidth = 1
  
  // Vertical grid lines
  for (let i = 0; i <= 10; i++) {
    const x = padding.left + (i / 10) * plotWidth
    ctx.beginPath()
    ctx.moveTo(x, padding.top)
    ctx.lineTo(x, height - padding.bottom)
    ctx.stroke()
  }
  
  // Horizontal grid lines
  for (let i = 0; i <= 10; i++) {
    const y = padding.top + (i / 10) * plotHeight
    ctx.beginPath()
    ctx.moveTo(padding.left, y)
    ctx.lineTo(width - padding.right, y)
    ctx.stroke()
  }
  
  // Draw axes
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
    ctx.fillText(analysisResult.value?.error || 'No data', width / 2, height / 2)
    return
  }
  
  // Map data point to canvas coordinates
  const { minX, maxX, minY, maxY } = plotBounds.value
  
  function toCanvasX(x) {
    return padding.left + ((x - minX) / (maxX - minX)) * plotWidth
  }
  
  function toCanvasY(y) {
    return height - padding.bottom - ((y - minY) / (maxY - minY)) * plotHeight
  }
  
  // Draw points
  for (const point of plotData.value) {
    const px = toCanvasX(point.x)
    const py = toCanvasY(point.y)
    
    ctx.beginPath()
    ctx.arc(px, py, 5, 0, Math.PI * 2)
    ctx.fillStyle = point.color
    ctx.fill()
    
    // Highlight if this is the current song
    if (point.id === currentSong.value) {
      ctx.strokeStyle = 'white'
      ctx.lineWidth = 2
      ctx.stroke()
    }
  }
  
  // Draw cluster representatives (larger, with label)
  for (let i = 0; i < clusterReps.value.length; i++) {
    const rep = clusterReps.value[i]
    const px = toCanvasX(rep.x)
    const py = toCanvasY(rep.y)
    
    // Outer ring
    ctx.beginPath()
    ctx.arc(px, py, 12, 0, Math.PI * 2)
    ctx.fillStyle = rep.color
    ctx.fill()
    ctx.strokeStyle = 'white'
    ctx.lineWidth = 2
    ctx.stroke()
    
    // Label
    ctx.fillStyle = 'white'
    ctx.font = 'bold 10px Inter'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(`C${i + 1}`, px, py)
  }
  
  // Draw axis tick labels
  ctx.fillStyle = 'rgba(255, 255, 255, 0.5)'
  ctx.font = '10px Inter'
  ctx.textAlign = 'center'
  
  // X axis ticks
  const xStep = (maxX - minX) / 5
  for (let i = 0; i <= 5; i++) {
    const val = minX + i * xStep
    const x = toCanvasX(val)
    ctx.fillText(val.toFixed(1), x, height - padding.bottom + 15)
  }
  
  // Y axis ticks
  ctx.textAlign = 'right'
  const yStep = (maxY - minY) / 5
  for (let i = 0; i <= 5; i++) {
    const val = minY + i * yStep
    const y = toCanvasY(val)
    ctx.fillText(val.toFixed(1), padding.left - 5, y + 3)
  }
}

// Handle plot click
function handlePlotClick(event) {
  const canvas = plotCanvas.value
  const rect = canvas.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  
  const padding = { left: 50, right: 20, top: 20, bottom: 40 }
  const plotWidth = rect.width - padding.left - padding.right
  const plotHeight = rect.height - padding.top - padding.bottom
  
  const { minX, maxX, minY, maxY } = plotBounds.value
  
  // Find clicked point
  for (const point of plotData.value) {
    const px = padding.left + ((point.x - minX) / (maxX - minX)) * plotWidth
    const py = rect.height - padding.bottom - ((point.y - minY) / (maxY - minY)) * plotHeight
    
    if (Math.abs(x - px) < 10 && Math.abs(y - py) < 10) {
      playSong(point.id)
      break
    }
  }
}

// Play song using NetEase API
async function playSong(songId) {
  currentSong.value = songId
  session.logExploration('play', songId)
  
  try {
    // Get music URL from API
    const url = `${MUSIC_API_BASE}/song/url?id=${songId}`
    const res = await fetch(url)
    const data = await res.json()
    
    console.log('Music API response:', data)
    
    if (data.data && data.data[0] && data.data[0].url) {
      const audio = audioPlayer.value
      const musicUrl = data.data[0].url
      
      // Create a proxied URL to avoid CORS (use vite proxy or direct)
      audio.src = musicUrl
      audio.load()
      
      audio.play().then(() => {
        isPlaying.value = true
        drawPlot() // Redraw to highlight current song
      }).catch(err => {
        console.error('Audio play error:', err)
        isPlaying.value = false
      })
    } else {
      console.error('No audio URL found for:', songId, data)
    }
  } catch (err) {
    console.error('Failed to get music URL:', err)
  }
}

function togglePlay() {
  const audio = audioPlayer.value
  if (!audio || !currentSong.value) return
  
  if (isPlaying.value) {
    audio.pause()
    isPlaying.value = false
  } else {
    audio.play().then(() => {
      isPlaying.value = true
    }).catch(err => {
      console.error('Play error:', err)
      isPlaying.value = false
    })
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

function onTimeUpdate() {
  const audio = audioPlayer.value
  if (!audio) return
  
  currentTime.value = audio.currentTime
  if (audio.duration > 0) {
    progress.value = (audio.currentTime / audio.duration) * 100
  }
  
  // Stop at 30 seconds
  if (audio.currentTime >= 30) {
    audio.pause()
    isPlaying.value = false
    session.logPlayback(currentSong.value, 30, true)
  }
}

function onAudioLoaded() {
  const audio = audioPlayer.value
  if (audio) {
    duration.value = Math.min(audio.duration, 30)
  }
}

function onAudioEnded() {
  isPlaying.value = false
  session.logPlayback(currentSong.value, duration.value, true)
}

function onAudioError(e) {
  console.error('Audio error:', e, audioPlayer.value?.error)
  isPlaying.value = false
}

function seekAudio(event) {
  const audio = audioPlayer.value
  if (!audio || !currentSong.value) return
  
  const rect = event.target.getBoundingClientRect()
  const x = event.clientX - rect.left
  const percent = x / rect.width
  audio.currentTime = percent * Math.min(audio.duration, 30)
}

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// Handle submit
async function handleSubmit() {
  const success = await session.submitSession()
  if (success) {
    setTimeout(() => {
      router.push('/complete')
    }, 2000)
  }
}

// Initial setup
onMounted(async () => {
  if (!session.userId) {
    router.push('/')
    return
  }
  
  // Load available genres/emotions
  await loadInfo()
  
  // Initial analysis
  if (selectedGenre.value && selectedEmotion.value) {
    await runAnalysis()
  }
  
  // Resize handler
  window.addEventListener('resize', drawPlot)
})

onUnmounted(() => {
  window.removeEventListener('resize', drawPlot)
  stopPlay()
})
</script>

<style scoped>
.explore-page {
  height: calc(100vh - 60px);
  padding: 1rem;
}

.explore-container {
  display: grid;
  grid-template-columns: 260px 1fr 320px;
  gap: 1rem;
  height: 100%;
}

.control-panel, .questionnaire-panel {
  overflow-y: auto;
}

.panel-title {
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
}

.panel-title.highlight {
  color: var(--primary);
  font-weight: 600;
}

.version-toggle {
  display: flex;
  gap: 0.5rem;
}

.version-btn {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text-secondary);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s;
}

.version-btn.active {
  background: var(--primary);
  border-color: var(--primary);
  color: white;
}

.analyze-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.analysis-info {
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
}

.info-text {
  color: var(--text-muted);
  margin: 0.25rem 0;
}

.player-section {
  padding-top: 1rem;
  border-top: 1px solid var(--border);
}

.song-id {
  font-size: 0.85rem;
  color: var(--text-primary);
  word-break: break-all;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.player-controls {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.player-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background: var(--primary);
  color: white;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.2s;
}

.player-btn:hover:not(:disabled) {
  transform: scale(1.05);
}

.player-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.progress-bar {
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  overflow: hidden;
  cursor: pointer;
}

.progress-fill {
  height: 100%;
  background: var(--primary);
  transition: width 0.1s;
}

.time-display {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 0.25rem;
  text-align: center;
}

.cluster-reps {
  padding-top: 1rem;
  border-top: 1px solid var(--border);
}

.cluster-rep-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: background 0.2s;
}

.cluster-rep-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.cluster-rep-item.active {
  background: rgba(102, 126, 234, 0.2);
}

.cluster-label {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
  color: white;
}

.cluster-song {
  font-size: 0.85rem;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plot-area {
  display: flex;
  flex-direction: column;
}

.plot-header {
  text-align: center;
  padding: 0.5rem;
}

.plot-title {
  font-weight: 600;
  color: var(--text-primary);
}

.plot-subtitle {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-left: 0.5rem;
}

.plot-wrapper {
  flex: 1;
  display: flex;
  gap: 0.5rem;
}

.y-axis-container {
  display: flex;
  align-items: center;
  writing-mode: vertical-lr;
  transform: rotate(180deg);
}

.y-axis-label-vertical {
  display: flex;
  align-items: center;
  gap: 1rem;
  font-size: 0.8rem;
}

.y-axis-label-vertical .axis-name {
  color: var(--text-secondary);
  font-weight: 500;
}

.y-axis-label-vertical .axis-pole-label {
  color: var(--text-muted);
  font-size: 0.75rem;
}

.plot-container {
  flex: 1;
  position: relative;
  background: rgba(0, 0, 0, 0.3);
  border-radius: var(--radius);
  overflow: hidden;
}

.plot-container canvas {
  position: absolute;
  inset: 0;
}

.x-axis-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 3rem;
  font-size: 0.8rem;
}

.x-axis-container .axis-name {
  color: var(--text-secondary);
  font-weight: 500;
}

.x-axis-container .axis-pole-label {
  color: var(--text-muted);
  font-size: 0.75rem;
}

.question-item {
  margin-bottom: 1.25rem;
}

.question-text {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
}

.likert-group {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
}

.likert-option {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 2px solid var(--border);
  background: transparent;
  color: var(--text-secondary);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.likert-option:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.likert-option.selected {
  background: var(--primary);
  border-color: var(--primary);
  color: white;
}

.preference-options {
  display: flex;
  gap: 0.5rem;
}

.preference-btn {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text-secondary);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s;
}

.preference-btn.selected {
  background: var(--primary);
  border-color: var(--primary);
  color: white;
}

.feedback-input {
  width: 100%;
  padding: 0.75rem;
  border-radius: var(--radius-sm);
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  color: var(--text-primary);
  font-family: inherit;
  resize: vertical;
}

.submit-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.progress-indicator {
  padding-top: 1rem;
  border-top: 1px solid var(--border);
}

.progress-text {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin: 0.25rem 0;
}
</style>
