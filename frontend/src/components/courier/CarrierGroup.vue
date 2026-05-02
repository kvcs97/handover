<template>
  <section
    class="carrier-group"
    :style="{ '--carrier-color': carrierColor }"
    :class="{ collapsed }"
  >
    <header class="group-header" @click="collapsed = !collapsed">
      <div class="group-title">
        <span class="chevron" :class="{ open: !collapsed }">▾</span>
        <span class="carrier-name">{{ group.carrier.display_name }}</span>
        <span class="shipment-count">
          {{ group.shipments.length }}
          {{ group.shipments.length === 1 ? 'Sendung' : 'Sendungen' }}
        </span>
      </div>
      <div class="group-meta">
        <span v-if="openCount > 0" class="meta-pill open-count">{{ openCount }} offen</span>
        <span v-if="printedCount > 0" class="meta-pill printed-count">{{ printedCount }} gedruckt</span>
        <span
          class="signature-pill"
          :class="`sig-${group.signature_status}`"
          :title="signatureTooltip"
        >
          {{ signatureLabel }}
        </span>
      </div>
    </header>

    <transition name="collapse">
      <div v-show="!collapsed" class="group-body">
        <div class="shipment-list">
          <ShipmentCard
            v-for="s in group.shipments"
            :key="s.id"
            :shipment="s"
            @print-request="$emit('print-request', $event)"
          />
        </div>

        <footer class="group-footer">
          <span v-if="batchSummary" class="batch-summary">{{ batchSummary }}</span>
          <button
            class="btn-ghost"
            :disabled="!canBatchPrint || isBatchPrinting || isSigned"
            :title="batchTooltip"
            @click="onPrintAll"
          >
            <span v-if="isBatchPrinting" class="btn-spinner" />
            <span v-else>🖨</span>
            {{ isBatchPrinting ? 'Drucke …' : 'Alle drucken' }}
          </button>
          <button
            class="btn-primary"
            :disabled="isSigned || isSigning || !canSign"
            :title="signTooltip"
            @click="$emit('sign-request', group)"
          >
            <span v-if="isSigning" class="btn-spinner light" />
            <span v-else>✍</span>
            {{ signButtonLabel }}
          </button>
        </footer>
      </div>
    </transition>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'
import ShipmentCard from './ShipmentCard.vue'
import { useCourierStore } from '../../stores/courier'

const props = defineProps({
  group: { type: Object, required: true },
})
defineEmits(['print-request', 'sign-request'])

const courier   = useCourierStore()
const collapsed = ref(false)

const isSigned    = computed(() => props.group.signature_status === 'signed')
const isSigning   = computed(() => courier.isCarrierSigning(props.group.carrier.id))
const canSign     = computed(() => (props.group.shipments || []).some(s => s.status !== 'archived'))

const signButtonLabel = computed(() => {
  if (isSigning.value) return 'Wird archiviert…'
  if (isSigned.value)  return '✓ Unterschrieben'
  return 'Unterschrift erfassen'
})
const signTooltip = computed(() => {
  if (isSigned.value)  return `Unterschrieben am ${props.group.signed_at || ''}`
  if (!canSign.value)  return 'Alle Sendungen bereits archiviert'
  return 'Sammel-Unterschrift für diesen Carrier erfassen'
})

const printableShipments = computed(() =>
  props.group.shipments.filter(s =>
    (s.status === 'open' || s.status === 'printed')
    && (s.documents || []).some(d => d.should_print),
  ),
)
const canBatchPrint   = computed(() => printableShipments.value.length > 0)
const isBatchPrinting = computed(() => courier.isCarrierPrinting(props.group.carrier.id))

const batchSummary = computed(() => {
  if (!canBatchPrint.value) return ''
  const n = printableShipments.value.length
  return `${n} ${n === 1 ? 'Sendung bereit' : 'Sendungen bereit'}`
})
const batchTooltip = computed(() => {
  if (isBatchPrinting.value) return 'Druckt …'
  if (!canBatchPrint.value)  return 'Keine offenen Sendungen mit Druckauswahl'
  return `Druckt alle ${printableShipments.value.length} Sendungen dieses Carriers`
})

async function onPrintAll() {
  if (!canBatchPrint.value || isBatchPrinting.value) return
  try {
    await courier.printAllForCarrier(props.group.carrier.id)
  } catch { /* fetchError ist im Store */ }
}

const CARRIER_COLORS = {
  fedex_tnt: 'var(--carrier-fedex)',
  dhl:       'var(--carrier-dhl)',
  ups:       'var(--carrier-ups)',
}

const carrierColor = computed(() =>
  CARRIER_COLORS[props.group.carrier.name] || 'var(--accent-primary)',
)

const openCount    = computed(() => props.group.shipments.filter(s => s.status === 'open').length)
const printedCount = computed(() => props.group.shipments.filter(s => s.status === 'printed').length)

const signatureLabel = computed(() =>
  props.group.signature_status === 'signed' ? '✓ Unterschrieben' : 'Offen',
)
const signatureTooltip = computed(() =>
  props.group.signature_status === 'signed'
    ? `Unterschrieben am ${props.group.signed_at || ''}`
    : 'Noch keine Unterschrift erfasst',
)
</script>

<style scoped>
.carrier-group {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-left: 4px solid var(--carrier-color);
  border-radius: 12px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  transition: box-shadow 200ms ease;
  overflow: hidden;
}
.carrier-group:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  cursor: pointer;
  gap: 16px;
  user-select: none;
}
.group-header:hover { background: var(--accent-bg); }

.group-title {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.chevron {
  display: inline-block;
  font-size: 12px;
  color: var(--color-text-muted);
  transition: transform 200ms ease;
}
.chevron.open { transform: rotate(0deg); }
.collapsed .chevron { transform: rotate(-90deg); }

.carrier-name {
  font-family: 'Instrument Serif', serif;
  font-size: 20px;
  font-weight: 400;
  color: var(--color-text);
  letter-spacing: -0.3px;
}
.shipment-count {
  font-size: 12px;
  color: var(--color-text-muted);
  background: var(--accent-bg);
  padding: 3px 9px;
  border-radius: 9999px;
}

.group-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.meta-pill {
  font-size: 11px;
  padding: 3px 9px;
  border-radius: 9999px;
  font-weight: 500;
}
.meta-pill.open-count    { background: rgba(91,141,184,0.10); color: var(--accent-primary); }
.meta-pill.printed-count { background: rgba(245,158,11,0.12); color: #B45309; }

.signature-pill {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 9999px;
  font-weight: 500;
}
.signature-pill.sig-pending { background: #F1F1F1;            color: var(--color-text-muted); }
.signature-pill.sig-signed  { background: rgba(34,197,94,0.12); color: #15803D; }

.group-body {
  border-top: 1px solid var(--color-border);
}

.shipment-list {
  background: var(--color-surface);
}

.group-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
  padding: 12px 18px;
  background: #FAFAFA;
  border-top: 1px solid var(--color-border);
}
.batch-summary {
  margin-right: auto;
  font-size: 12px;
  color: var(--color-text-muted);
}
.btn-spinner {
  display: inline-block;
  width: 12px; height: 12px;
  border: 2px solid var(--color-border);
  border-top-color: var(--accent-primary);
  border-radius: 50%;
  animation: spin 700ms linear infinite;
}
.btn-spinner.light {
  border-color: rgba(255,255,255,0.4);
  border-top-color: white;
}
@keyframes spin { to { transform: rotate(360deg); } }

.btn-primary, .btn-ghost {
  font-family: 'DM Sans', sans-serif;
  font-size: 13px;
  font-weight: 500;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 150ms ease, opacity 150ms ease;
}
.btn-primary {
  background: var(--accent-primary);
  color: white;
  border: none;
}
.btn-primary:hover:not(:disabled) { background: var(--accent-secondary); }
.btn-ghost {
  background: transparent;
  border: 1px solid var(--color-border);
  color: var(--color-text);
}
.btn-ghost:hover:not(:disabled) { background: var(--accent-bg); }
.btn-primary:disabled, .btn-ghost:disabled { opacity: 0.5; cursor: not-allowed; }

/* Collapse-Transition */
.collapse-enter-active, .collapse-leave-active {
  transition: max-height 250ms ease, opacity 200ms ease;
  overflow: hidden;
}
.collapse-enter-from, .collapse-leave-to { max-height: 0; opacity: 0; }
.collapse-enter-to, .collapse-leave-from { max-height: 2000px; opacity: 1; }
</style>
