<template>
  <div class="shipment-card" :class="{ unmatched: isUnmatched }">
    <div class="ls-block">
      <div class="ls-numbers">
        <span
          v-for="ls in displayedLs"
          :key="ls"
          class="ls-number"
        >{{ ls }}</span>
        <span v-if="displayedLs.length === 0" class="ls-missing">Keine LS-Nummer</span>
      </div>
      <div v-if="shipment.email_subject" class="email-subject" :title="shipment.email_subject">
        {{ shipment.email_subject }}
      </div>
    </div>

    <div class="docs-block">
      <DocumentChip
        v-for="doc in shipment.documents"
        :key="doc.id"
        :shipment-id="shipment.id"
        :doc="doc"
      />
      <span v-if="!shipment.documents || shipment.documents.length === 0" class="docs-empty">
        Keine Dokumente
      </span>
    </div>

    <div class="status-block">
      <StatusBadge :status="shipment.status" />
      <button
        type="button"
        class="btn-print"
        :disabled="!canPrint || isPrinting"
        :title="printTooltip"
        @click.stop="$emit('print-request', shipment)"
      >
        <span v-if="isPrinting" class="btn-spinner" />
        <span v-else>🖨</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import DocumentChip from './DocumentChip.vue'
import StatusBadge  from './StatusBadge.vue'
import { useCourierStore } from '../../stores/courier'

const props = defineProps({
  shipment:    { type: Object, required: true },
  isUnmatched: { type: Boolean, default: false },
})
defineEmits(['print-request'])

const courier = useCourierStore()

const displayedLs = computed(() => props.shipment.delivery_note_numbers || [])

const selectedCount = computed(() =>
  (props.shipment.documents || []).filter(d => d.should_print).length,
)
const canPrint   = computed(() => selectedCount.value > 0)
const isPrinting = computed(() => courier.isShipmentPrinting(props.shipment.id))

const printTooltip = computed(() => {
  if (isPrinting.value) return 'Druckt …'
  if (!canPrint.value)  return 'Kein Dokument zum Drucken ausgewählt'
  return `Drucken (${selectedCount.value} Dokument${selectedCount.value === 1 ? '' : 'e'})`
})
</script>

<style scoped>
.shipment-card {
  display: grid;
  grid-template-columns: minmax(180px, 220px) 1fr auto;
  gap: 16px;
  align-items: center;
  padding: 14px 18px;
  border-bottom: 1px solid var(--color-border);
  transition: background 150ms ease;
}
.shipment-card:last-child { border-bottom: none; }
.shipment-card:hover      { background: var(--accent-bg); }

.shipment-card.unmatched {
  background: rgba(239,68,68,0.04);
}
.shipment-card.unmatched:hover {
  background: rgba(239,68,68,0.07);
}

.ls-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}
.ls-numbers {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.ls-number {
  font-family: 'DM Mono', 'JetBrains Mono', monospace;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text);
  letter-spacing: 0.2px;
}
.ls-missing {
  font-size: 12px;
  color: var(--color-danger);
  font-style: italic;
}
.email-subject {
  font-size: 11px;
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.docs-block {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  min-width: 0;
}
.docs-empty {
  font-size: 11px;
  color: var(--color-text-muted);
  font-style: italic;
}

.status-block {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.btn-print {
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  width: 32px; height: 30px;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 13px;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all 150ms ease;
}
.btn-print:hover:not(:disabled) {
  background: var(--accent-primary);
  border-color: var(--accent-primary);
  color: white;
}
.btn-print:disabled { opacity: 0.4; cursor: not-allowed; }

.btn-spinner {
  width: 12px; height: 12px;
  border: 2px solid var(--color-border);
  border-top-color: var(--accent-primary);
  border-radius: 50%;
  animation: spin 700ms linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
