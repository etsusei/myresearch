import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useSessionStore = defineStore('session', () => {
    // Session data
    const userId = ref(null)
    const language = ref('zh')
    const startTime = ref(null)
    const endTime = ref(null)
    const versionMapping = ref({ A: null, B: null }) // Will be randomized

    // Current state
    const currentVersion = ref('A')
    const currentGenre = ref(null)
    const currentEmotion = ref(null)
    const currentTaskType = ref('guided') // 'guided' | 'free'
    const explorationsCount = ref(0)

    // State for Experiment Wizard
    const taskStep = ref('welcome') // 'welcome', 'guided_A', 'guided_B', 'transition', 'free_A', 'free_B', 'final', 'complete'

    // Submission state
    const isSubmitting = ref(false)
    const submitStatus = ref(null)

    // Unified Data Storage keyed by ContextID
    // Format: "Genre_Emotion_Version_TaskType" (e.g., "Pop_Happy_A_free")
    const sessionData = ref({})

    // Listened songs tracking (Global helper for "listened to" visualization)
    const listenedSongs = ref({}) // { songId: { duration: number, timestamp: number } }

    // Current playback state
    const currentPlayback = ref({
        songId: null,
        startTime: null,
        contextId: null
    })

    // ═══════════════════════════════════════════════════════════
    // Initialize session
    // ═══════════════════════════════════════════════════════════
    function initSession() {
        userId.value = crypto.randomUUID()
        startTime.value = new Date().toISOString()

        // Randomize version mapping (A/B -> GT/Model)
        const isAGT = Math.random() < 0.5
        versionMapping.value = {
            A: isAGT ? 'GT' : 'Model',
            B: isAGT ? 'Model' : 'GT'
        }

        console.log('Session initialized:', {
            userId: userId.value,
            versionMapping: versionMapping.value
        })
    }

    // Helper to generate Context ID
    function getContextId() {
        if (taskStep.value === 'final') return 'final'
        const g = currentGenre.value || 'Unknown'
        const e = currentEmotion.value || 'Unknown'
        const v = currentVersion.value
        const t = currentTaskType.value
        return `${g}_${e}_${v}_${t}`
    }

    // Initialize data bucket for current context if not exists
    function ensureContext() {
        const key = getContextId()
        if (!sessionData.value[key]) {
            sessionData.value[key] = {
                genre: currentGenre.value,
                emotion: currentEmotion.value,
                version: currentVersion.value,
                taskType: currentTaskType.value,
                events: [],
                path: [],     // Only for free task
                likedSongs: [], // Only for free task
                responses: {}
            }
        }
    }

    // ═══════════════════════════════════════════════════════════
    // Event Recording
    // ═══════════════════════════════════════════════════════════
    function recordEvent(type, data = {}) {
        ensureContext()
        const key = getContextId()
        const event = {
            type,
            timestamp: Date.now(),
            ...data
        }
        sessionData.value[key].events.push(event)
        // console.log('Event recorded:', key, event)
    }

    // Record click on a song point
    function recordClick(songId, x, y) {
        recordEvent('click', { songId, x, y })

        // Only record path in FREE exploration
        if (currentTaskType.value === 'free') {
            ensureContext()
            const key = getContextId()
            sessionData.value[key].path.push({
                songId,
                x,
                y,
                timestamp: Date.now()
            })
        }
    }

    // Record play start
    function recordPlayStart(songId) {
        if (currentPlayback.value.songId) {
            recordPlayEnd()
        }

        currentPlayback.value = {
            songId,
            startTime: Date.now(),
            contextId: getContextId() // Store context when playback started
        }
        recordEvent('play_start', { songId })
    }

    // Record play end
    function recordPlayEnd() {
        if (!currentPlayback.value.songId) return

        const duration = (Date.now() - currentPlayback.value.startTime) / 1000
        const songId = currentPlayback.value.songId
        const contextId = currentPlayback.value.contextId

        const event = {
            type: 'play_end',
            timestamp: Date.now(),
            songId,
            duration
        }

        // Store in the correct context (even if user switched context while playing)
        if (sessionData.value[contextId]) {
            sessionData.value[contextId].events.push(event)
        }

        // Update listened songs (global tracking for "Have listened to...")
        if (!listenedSongs.value[songId]) {
            listenedSongs.value[songId] = { duration: 0, timestamp: Date.now() }
        }
        listenedSongs.value[songId].duration += duration

        // Update path duration if in free exploration AND context matches
        if (contextId.includes('_free')) {
            const bucket = sessionData.value[contextId]
            if (bucket && bucket.path) {
                const pathEntry = bucket.path.find(p => p.songId === songId && !p.duration)
                if (pathEntry) {
                    pathEntry.duration = duration
                }
            }
        }

        currentPlayback.value = { songId: null, startTime: null }
    }

    // ═══════════════════════════════════════════════════════════
    // Like/Unlike
    // ═══════════════════════════════════════════════════════════
    function toggleLike(songId) {
        ensureContext()
        const key = getContextId()
        // Only allow likes in free mode (or stored in current context)
        const bucket = sessionData.value[key]
        if (!bucket.likedSongs) bucket.likedSongs = []

        const index = bucket.likedSongs.indexOf(songId)
        if (index === -1) {
            bucket.likedSongs.push(songId)
            recordEvent('like', { songId })
        } else {
            bucket.likedSongs.splice(index, 1)
            recordEvent('unlike', { songId })
        }
    }

    function isLiked(songId) {
        const key = getContextId()
        const bucket = sessionData.value[key]
        return bucket && bucket.likedSongs ? bucket.likedSongs.includes(songId) : false
    }

    function getLikedCount() {
        const key = getContextId()
        const bucket = sessionData.value[key]
        return bucket && bucket.likedSongs ? bucket.likedSongs.length : 0
    }

    // ═══════════════════════════════════════════════════════════
    // Listened state - NEW
    // ═══════════════════════════════════════════════════════════
    function getListenedState(songId) {
        const info = listenedSongs.value[songId]
        if (!info) return 'unheard'
        if (info.duration < 5) return 'skipped'
        return 'listened'
    }

    function getListenedCount() {
        // Count songs listened for ≥5 seconds
        return Object.values(listenedSongs.value).filter(s => s.duration >= 5).length
    }

    // ═══════════════════════════════════════════════════════════
    // Responses
    // ═══════════════════════════════════════════════════════════
    // ═══════════════════════════════════════════════════════════
    // Responses
    // ═══════════════════════════════════════════════════════════
    // ═══════════════════════════════════════════════════════════
    // Responses
    // ═══════════════════════════════════════════════════════════

    // Get the key for storing/retrieving responses
    // For Guided: bound to specific context (Genre_Emotion)
    // For Free: bound to Version only (Global for A or B)
    function getQuestionnaireKey() {
        if (taskStep.value === 'final') return 'final'

        if (currentTaskType.value === 'free') {
            // Summary bucket for Free Task (e.g. "Summary_A_free")
            return `Summary_${currentVersion.value}_free`
        }

        return getContextId()
    }

    function setResponse(questionId, value) {
        const key = getQuestionnaireKey()

        // Ensure bucket exists for this key (might be a Summary bucket)
        if (!sessionData.value[key]) {
            sessionData.value[key] = {
                genre: 'Mixed',
                emotion: 'Mixed',
                version: currentVersion.value,
                taskType: currentTaskType.value,
                events: [],
                path: [],
                likedSongs: [],
                responses: {}
            }
        }

        sessionData.value[key].responses[questionId] = value
    }

    // Helper to get current response for UI binding
    function getResponse(questionId) {
        const key = getQuestionnaireKey()
        if (sessionData.value[key] && sessionData.value[key].responses) {
            return sessionData.value[key].responses[questionId]
        }
        return undefined
    }

    function setFinalResponse(questionId, value) {
        // Special case for final
        if (!sessionData.value['final']) sessionData.value['final'] = { responses: {} }
        sessionData.value['final'].responses[questionId] = value
    }

    function getFinalResponse(questionId) {
        if (sessionData.value['final'] && sessionData.value['final'].responses) {
            return sessionData.value['final'].responses[questionId]
        }
        return undefined
    }

    // ═══════════════════════════════════════════════════════════
    // Validation
    // ═══════════════════════════════════════════════════════════
    function canProceedFromGuided() {
        // Just need ANY listening activity really, but let's enforce 1 song > 5s
        // Or user design requirement
        // return getListenedCount() >= 1
        return true // DEBUG: Allow skipping for testing
    }

    function canProceedFromFree() {
        // Need at least 3 songs listened and 1 liked
        // return getListenedCount() >= 3 && getLikedCount() >= 1
        return true // DEBUG: Allow skipping for testing
    }

    // ═══════════════════════════════════════════════════════════
    // Session Data & Submit
    // ═══════════════════════════════════════════════════════════
    function getSessionData() {
        endTime.value = new Date().toISOString()
        return {
            sessionId: crypto.randomUUID(),
            userId: userId.value,
            language: language.value,
            startTime: startTime.value,
            endTime: endTime.value,
            versionMapping: versionMapping.value,
            // Dump all accumulated data
            data: sessionData.value
        }
    }

    // Download session data as JSON
    function downloadSessionData() {
        const data = getSessionData()
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `session_${new Date().toISOString().slice(0, 19).replace(/[:-]/g, '')}_${userId.value.slice(0, 8)}.json`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
    }

    async function submitSession() {
        isSubmitting.value = true
        submitStatus.value = null

        try {
            const data = getSessionData()

            // Save to localStorage as backup
            const submissions = JSON.parse(localStorage.getItem('submissions') || '[]')
            submissions.push(data)
            localStorage.setItem('submissions', JSON.stringify(submissions))

            // Try to save to backend
            try {
                await fetch('/api/submit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_data: data })
                })
            } catch (e) {
                console.warn('Backend submit failed, data saved locally:', e)
            }

            submitStatus.value = 'success'
            return true
        } catch (error) {
            console.error('Submit error:', error)
            submitStatus.value = 'error'
            return false
        } finally {
            isSubmitting.value = false
        }
    }

    // Reset listened songs when switching versions/tasks
    function resetListenedForTask() {
        listenedSongs.value = {}
    }

    return {
        // State
        // State
        userId,
        language,
        startTime,
        endTime,
        versionMapping,
        currentVersion,
        currentGenre,
        currentEmotion,
        currentTaskType,
        explorationsCount,
        taskStep,        // NEW
        sessionData,     // NEW
        listenedSongs,
        currentPlayback,
        isSubmitting,
        submitStatus,

        // Computed
        // isComplete, // Deprecated, handled by step flow

        // Actions
        initSession,
        recordClick,
        recordPlayStart,
        recordPlayEnd,
        toggleLike,
        isLiked,
        getLikedCount,
        getListenedState,
        getListenedCount,
        setResponse,
        getResponse,     // NEW
        setFinalResponse,
        getFinalResponse,// NEW
        canProceedFromGuided,
        canProceedFromFree,
        getSessionData,
        downloadSessionData,
        submitSession,
        resetListenedForTask
    }
})
