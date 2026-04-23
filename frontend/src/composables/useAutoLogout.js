import { onMounted, onBeforeUnmount, ref } from 'vue'

/**
 * Meldet den Benutzer nach `timeoutMs` Inaktivitaet automatisch ab.
 * Aktivitaet wird ueber Maus, Tastatur, Touch und Scroll erkannt.
 *
 * @param {() => void} onTimeout      Callback bei Inaktivitaet (z.B. auth.logout)
 * @param {object}     opts
 * @param {number}     opts.timeoutMs Inaktivitaetsdauer in ms, Default 30 Min
 * @param {number}     opts.warnBeforeMs Warnung anzeigen X ms vor Logout, Default 60s
 */
export function useAutoLogout(onTimeout, opts = {}) {
  const timeoutMs    = opts.timeoutMs    ?? 30 * 60 * 1000
  const warnBeforeMs = opts.warnBeforeMs ?? 60 * 1000

  const warning    = ref(false)
  const msRemaining = ref(0)

  let idleTimer    = null
  let warnTimer    = null
  let countdownTimer = null

  function fireLogout() {
    warning.value = false
    onTimeout?.()
  }

  function reset() {
    clearTimeout(idleTimer)
    clearTimeout(warnTimer)
    clearInterval(countdownTimer)
    warning.value = false

    // Warnung kurz vor Logout
    warnTimer = setTimeout(() => {
      warning.value = true
      msRemaining.value = warnBeforeMs
      countdownTimer = setInterval(() => {
        msRemaining.value = Math.max(0, msRemaining.value - 1000)
      }, 1000)
    }, Math.max(0, timeoutMs - warnBeforeMs))

    // Finales Timeout
    idleTimer = setTimeout(fireLogout, timeoutMs)
  }

  // Events die als "aktiv" zaehlen
  const events = ['mousemove', 'mousedown', 'keydown', 'touchstart', 'scroll', 'wheel']

  function onActivity() {
    // Wenn Warnung aktiv ist, setzt Aktivitaet den Timer zurueck
    reset()
  }

  function onVisibility() {
    if (document.visibilityState === 'visible') reset()
  }

  onMounted(() => {
    events.forEach(e => window.addEventListener(e, onActivity, { passive: true }))
    document.addEventListener('visibilitychange', onVisibility)
    reset()
  })

  onBeforeUnmount(() => {
    events.forEach(e => window.removeEventListener(e, onActivity))
    document.removeEventListener('visibilitychange', onVisibility)
    clearTimeout(idleTimer)
    clearTimeout(warnTimer)
    clearInterval(countdownTimer)
  })

  return { warning, msRemaining, reset }
}
