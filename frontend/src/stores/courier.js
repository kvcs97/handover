import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import api from '../api'

const STORAGE_KEY = 'handover.mode'
const VALID_MODES = ['lkw', 'courier']

function readInitialMode() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved && VALID_MODES.includes(saved)) return saved
  } catch {}
  return 'lkw'
}

function applyMode(mode, animate = false) {
  if (typeof document === 'undefined') return
  document.documentElement.dataset.mode = mode
  if (animate && document.body) {
    document.body.classList.remove('mode-switching')
    // Force reflow, damit die Animation auch bei aufeinanderfolgenden Toggles neu startet
    void document.body.offsetWidth
    document.body.classList.add('mode-switching')
    setTimeout(() => document.body.classList.remove('mode-switching'), 260)
  }
}

function todayIso() {
  return new Date().toISOString().slice(0, 10)
}

export const useCourierStore = defineStore('courier', () => {
  // ── Mode-Switch (Phase 1) ───────────────────────────
  const mode = ref(readInitialMode())
  applyMode(mode.value, false)   // initial: kein Fade
  watch(mode, (next) => {
    applyMode(next, true)         // Wechsel: Fade-Animation triggern
    try { localStorage.setItem(STORAGE_KEY, next) } catch {}
  })

  function setMode(next) {
    if (!VALID_MODES.includes(next)) return
    mode.value = next
  }
  function toggleMode() {
    mode.value = mode.value === 'lkw' ? 'courier' : 'lkw'
  }
  /**
   * Standard-Modus aus den Settings beim App-Start anwenden.
   *
   * Wenn `courier_default_mode` konfiguriert ist, gewinnt er IMMER über den
   * localStorage-Wert. localStorage hält nur die Session-Persistenz für
   * manuelle Toggles WÄHREND der laufenden App.
   */
  async function applyDefaultModeFromSettings() {
    try {
      const res = await api.get('/settings/global')
      const def = res.data?.courier_default_mode
      if (def && VALID_MODES.includes(def) && def !== mode.value) {
        mode.value = def
      }
    } catch { /* Settings nicht erreichbar — bleibe beim Initial-Mode */ }
  }

  // ── Dashboard-State (Phase 3) ───────────────────────
  const carrierGroups       = ref([])   // [{ carrier, shipments, signature_status, signed_at }]
  const unmatchedShipments  = ref([])
  const carriers            = ref([])   // alle aktiven Carrier (für Filter-Dropdown)
  const selectedDate        = ref(todayIso())
  const fetchStatus         = ref('idle')   // idle | loading | done | error
  const fetchError          = ref(null)
  const lastProcessSummary  = ref(null)     // {total_emails, total_shipments}
  const carrierFilter       = ref(null)     // null | carrier.id
  const searchQuery         = ref('')

  const totalShipments = computed(() => {
    const groupCount = carrierGroups.value.reduce((sum, g) => sum + g.shipments.length, 0)
    return groupCount + unmatchedShipments.value.length
  })

  const filteredCarrierGroups = computed(() => {
    const q = searchQuery.value.trim().toLowerCase()
    return carrierGroups.value
      .filter(g => carrierFilter.value == null || g.carrier.id === carrierFilter.value)
      .map(g => ({
        ...g,
        shipments: q ? g.shipments.filter(s => _matchesQuery(s, q)) : g.shipments,
      }))
      .filter(g => g.shipments.length > 0)
  })

  const filteredUnmatched = computed(() => {
    const q = searchQuery.value.trim().toLowerCase()
    if (carrierFilter.value != null) return []   // bei aktivem Filter keine unmatched
    if (!q) return unmatchedShipments.value
    return unmatchedShipments.value.filter(s => _matchesQuery(s, q))
  })

  function _matchesQuery(s, q) {
    if ((s.delivery_note_numbers || []).some(ls => ls.toLowerCase().includes(q))) return true
    if (s.email_subject && s.email_subject.toLowerCase().includes(q)) return true
    return false
  }

  function _applyResponse(data) {
    carrierGroups.value      = data?.carrier_groups       || []
    unmatchedShipments.value = data?.unmatched_shipments  || []
    lastProcessSummary.value = {
      total_emails:    data?.total_emails    ?? 0,
      total_shipments: data?.total_shipments ?? totalShipments.value,
      process_date:    data?.process_date    ?? selectedDate.value,
    }
  }

  // ── API-Calls ──────────────────────────────────────
  async function loadCarriers() {
    try {
      const res = await api.get('/api/courier/carriers')
      carriers.value = res.data || []
    } catch (e) {
      // Carrier-Liste ist nice-to-have für den Filter; Fehler nicht blocken
      carriers.value = []
    }
  }

  async function loadShipmentsForDate(date) {
    fetchStatus.value = 'loading'
    fetchError.value  = null
    try {
      const res = await api.get('/api/courier/shipments', { params: { date } })
      _applyResponse(res.data)
      fetchStatus.value = 'done'
    } catch (e) {
      fetchError.value  = _errorMessage(e)
      fetchStatus.value = 'error'
    }
  }

  async function processEmailsForDate(date) {
    fetchStatus.value = 'loading'
    fetchError.value  = null
    try {
      // 3 Min Timeout: bei vollen Postfächern kann der initiale Pull mehrere
      // Dutzend MB an PDF-Anhängen umfassen.
      const res = await api.post('/api/courier/process-emails', { date }, { timeout: 180000 })
      _applyResponse(res.data)
      fetchStatus.value = 'done'
    } catch (e) {
      fetchError.value  = _errorMessage(e)
      fetchStatus.value = 'error'
    }
  }

  async function toggleDocumentPrint(shipmentId, docId, nextValue) {
    // Optimistic Update
    const doc = _findDocument(shipmentId, docId)
    if (!doc) return
    const previous = doc.should_print
    doc.should_print = nextValue
    try {
      await api.patch(`/api/courier/documents/${docId}/print`, { should_print: nextValue })
    } catch (e) {
      doc.should_print = previous
      fetchError.value = _errorMessage(e)
    }
  }

  function _findDocument(shipmentId, docId) {
    const groups = [
      ...carrierGroups.value,
      { shipments: unmatchedShipments.value },
    ]
    for (const g of groups) {
      for (const s of g.shipments) {
        if (s.id !== shipmentId) continue
        return (s.documents || []).find(d => d.id === docId)
      }
    }
    return null
  }

  function _replaceShipment(updated) {
    if (!updated) return
    for (const g of carrierGroups.value) {
      const idx = g.shipments.findIndex(s => s.id === updated.id)
      if (idx !== -1) {
        g.shipments[idx] = updated
        return
      }
    }
    const uIdx = unmatchedShipments.value.findIndex(s => s.id === updated.id)
    if (uIdx !== -1) unmatchedShipments.value[uIdx] = updated
  }

  // ── Drucken (Phase 4) ──────────────────────────────
  const printingShipments = ref(new Set())
  const printingCarriers  = ref(new Set())

  function isShipmentPrinting(id) { return printingShipments.value.has(id) }
  function isCarrierPrinting(id)  { return printingCarriers.value.has(id) }

  async function printShipment(shipmentId) {
    if (printingShipments.value.has(shipmentId)) return null
    printingShipments.value = new Set(printingShipments.value).add(shipmentId)
    try {
      const res = await api.post(`/api/courier/shipments/${shipmentId}/print`, null, { timeout: 60000 })
      if (res.data?.shipment) _replaceShipment(res.data.shipment)
      return res.data
    } catch (e) {
      fetchError.value = _errorMessage(e)
      throw e
    } finally {
      const next = new Set(printingShipments.value)
      next.delete(shipmentId)
      printingShipments.value = next
    }
  }

  async function printAllForCarrier(carrierId) {
    if (printingCarriers.value.has(carrierId)) return null
    printingCarriers.value = new Set(printingCarriers.value).add(carrierId)
    try {
      const res = await api.post(
        `/api/courier/carriers/${carrierId}/print-all`,
        null,
        { params: { date: selectedDate.value }, timeout: 120000 },
      )
      const results = res.data?.results || []
      for (const r of results) {
        if (r.shipment) _replaceShipment(r.shipment)
      }
      return res.data
    } catch (e) {
      fetchError.value = _errorMessage(e)
      throw e
    } finally {
      const next = new Set(printingCarriers.value)
      next.delete(carrierId)
      printingCarriers.value = next
    }
  }

  async function fetchDocumentBlobUrl(docId) {
    const res = await api.get(`/api/courier/documents/${docId}/file`, { responseType: 'blob' })
    return URL.createObjectURL(res.data)
  }

  // ── Unterschrift & Archivierung (Phase 5) ──────────
  const signingCarriers = ref(new Set())
  function isCarrierSigning(id) { return signingCarriers.value.has(id) }

  async function signCarrier(carrierId, payload) {
    if (signingCarriers.value.has(carrierId)) return null
    signingCarriers.value = new Set(signingCarriers.value).add(carrierId)
    try {
      const res = await api.post(
        `/api/courier/carriers/${carrierId}/sign`,
        {
          signature_data: payload.signature_data,
          signer_name:    payload.signer_name || null,
          process_date:   payload.process_date || selectedDate.value,
        },
        { timeout: 60000 },
      )
      const updatedShipments = res.data?.shipments || []
      for (const s of updatedShipments) _replaceShipment(s)

      // Signatur-Status der Carrier-Gruppe lokal aktualisieren
      const group = carrierGroups.value.find(g => g.carrier.id === carrierId)
      if (group && res.data?.archived_count > 0) {
        group.signature_status = 'signed'
        group.signed_at = new Date().toISOString()
      }
      return res.data
    } catch (e) {
      fetchError.value = _errorMessage(e)
      throw e
    } finally {
      const next = new Set(signingCarriers.value)
      next.delete(carrierId)
      signingCarriers.value = next
    }
  }

  function _errorMessage(e) {
    // 1) Backend-Detail mit konkretem Text → Priorität
    if (e?.response?.data?.detail) return e.response.data.detail
    // 2) Timeout (axios setzt code='ECONNABORTED' bei timeout)
    if (e?.code === 'ECONNABORTED' || /timeout/i.test(e?.message || '')) {
      return 'Zeitüberschreitung — der Mail-Abruf hat zu lange gedauert. ' +
             'Versuch es erneut, oder prüfe das Backend-Log.'
    }
    // 3) "Network Error" generisch — meistens Backend abgestürzt oder Connection reset
    if (/network error/i.test(e?.message || '')) {
      return 'Netzwerkfehler — Backend antwortet nicht. ' +
             'Bitte App neu starten und Backend-Log prüfen (Status, Speicher, Stacktrace).'
    }
    return e?.message || 'Unbekannter Fehler'
  }

  function setDate(iso) {
    if (!iso || iso === selectedDate.value) return
    selectedDate.value = iso
    loadShipmentsForDate(iso)
  }
  function setCarrierFilter(id) { carrierFilter.value = id }
  function setSearchQuery(q)    { searchQuery.value = q ?? '' }

  return {
    // Mode-Switch
    mode, setMode, toggleMode, applyDefaultModeFromSettings,
    // Dashboard-State
    carrierGroups, unmatchedShipments, carriers,
    selectedDate, fetchStatus, fetchError, lastProcessSummary,
    carrierFilter, searchQuery,
    // Drucken
    printingShipments, printingCarriers, isShipmentPrinting, isCarrierPrinting,
    // Unterschrift
    signingCarriers, isCarrierSigning,
    // Getters
    totalShipments, filteredCarrierGroups, filteredUnmatched,
    // Actions
    loadCarriers, loadShipmentsForDate, processEmailsForDate,
    toggleDocumentPrint, setDate, setCarrierFilter, setSearchQuery,
    printShipment, printAllForCarrier, fetchDocumentBlobUrl,
    signCarrier,
  }
})
