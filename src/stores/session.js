import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useSessionStore = defineStore('session', () => {
    // Session data
    const userId = ref(null)
    const language = ref('zh')
    const startTime = ref(null)
    const versionMapping = ref({ A: null, B: null }) // Will be randomized

    // Exploration logs
    const explorationLogs = ref([])
    const playbackHistory = ref([])

    // Responses
    const responses = ref({
        versionA: {},
        versionB: {},
        final: { preference: null, feedback: '' }
    })

    // Current state
    const currentVersion = ref('A')
    const currentGenre = ref(null)
    const currentEmotion = ref(null)
    const explorationsCount = ref(0)

    // Submission state
    const isSubmitting = ref(false)
    const submitStatus = ref(null) // 'success' | 'error' | null

    // Initialize session
    function initSession() {
        userId.value = crypto.randomUUID()
        startTime.value = Date.now()

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

    // Log exploration action
    function logExploration(action, songId = null) {
        explorationLogs.value.push({
            timestamp: Date.now(),
            genre: currentGenre.value,
            emotion: currentEmotion.value,
            version: currentVersion.value,
            action,
            songId
        })
    }

    // Log playback
    function logPlayback(songId, duration, completed) {
        playbackHistory.value.push({
            songId,
            duration,
            completed,
            timestamp: Date.now()
        })
    }

    // Increment exploration count when genre+emotion changes
    function trackExploration() {
        explorationsCount.value++
        logExploration('analyze')
    }

    // Set response for current version
    function setResponse(questionId, value) {
        const key = `version${currentVersion.value}`
        responses.value[key][questionId] = value
    }

    // Set final response
    function setFinalResponse(questionId, value) {
        responses.value.final[questionId] = value
    }

    // Check if all required fields are filled
    const isComplete = computed(() => {
        const vA = responses.value.versionA
        const vB = responses.value.versionB
        const final = responses.value.final

        const requiredQuestions = ['discoverability', 'serendipity', 'coherence', 'satisfaction']
        const vAComplete = requiredQuestions.every(q => vA[q] !== undefined)
        const vBComplete = requiredQuestions.every(q => vB[q] !== undefined)
        const finalComplete = final.preference !== null

        return vAComplete && vBComplete && finalComplete && explorationsCount.value >= 3
    })

    // Get session data for submission
    function getSessionData() {
        return {
            userId: userId.value,
            language: language.value,
            startTime: startTime.value,
            submittedAt: Date.now(),
            versionMapping: versionMapping.value,
            explorationLogs: explorationLogs.value,
            playbackHistory: playbackHistory.value,
            responses: responses.value,
            explorationsCount: explorationsCount.value
        }
    }

    // Submit session
    async function submitSession() {
        isSubmitting.value = true
        submitStatus.value = null

        try {
            const data = getSessionData()

            // For testing: save to localStorage
            const submissions = JSON.parse(localStorage.getItem('submissions') || '[]')
            submissions.push(data)
            localStorage.setItem('submissions', JSON.stringify(submissions))

            // TODO: In production, send to backend
            // await fetch('/api/submit', {
            //   method: 'POST',
            //   headers: { 'Content-Type': 'application/json' },
            //   body: JSON.stringify(data)
            // })

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

    return {
        // State
        userId,
        language,
        startTime,
        versionMapping,
        explorationLogs,
        playbackHistory,
        responses,
        currentVersion,
        currentGenre,
        currentEmotion,
        explorationsCount,
        isSubmitting,
        submitStatus,

        // Computed
        isComplete,

        // Actions
        initSession,
        logExploration,
        logPlayback,
        trackExploration,
        setResponse,
        setFinalResponse,
        getSessionData,
        submitSession
    }
})
