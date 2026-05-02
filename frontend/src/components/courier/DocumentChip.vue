<template>
  <button
    type="button"
    class="doc-chip"
    :class="{ active: doc.should_print, printed: doc.was_printed }"
    :disabled="busy"
    :title="tooltip"
    @click="onToggle"
  >
    <span v-if="doc.should_print" class="chip-icon">🖨</span>
    <span class="chip-label">{{ label }}</span>
  </button>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useCourierStore } from '../../stores/courier'

const props = defineProps({
  shipmentId: { type: Number, required: true },
  doc:        { type: Object, required: true },
})

const courier = useCourierStore()
const busy    = ref(false)

const TYPE_LABELS = {
  label:        'Label',
  rechnung:     'Rechnung',
  lieferschein: 'LS',
  pkl:          'PKL',
  edec:         'EDEC',
  to:           'TO',
  other:        'Sonstige',
}

const label = computed(() => TYPE_LABELS[props.doc.document_type] || props.doc.document_type)

const tooltip = computed(() => {
  const parts = [props.doc.filename]
  if (props.doc.was_printed) parts.push('bereits gedruckt')
  parts.push(props.doc.should_print ? 'Klicken um nicht zu drucken' : 'Klicken um zu drucken')
  return parts.join(' — ')
})

async function onToggle() {
  if (busy.value) return
  busy.value = true
  try {
    await courier.toggleDocumentPrint(props.shipmentId, props.doc.id, !props.doc.should_print)
  } finally {
    busy.value = false
  }
}
</script>

<style scoped>
.doc-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  border-radius: 9999px;
  font-family: 'DM Sans', sans-serif;
  font-size: 11px;
  font-weight: 500;
  border: 1px solid transparent;
  background: var(--color-border);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: background 150ms ease, color 150ms ease, border-color 150ms ease;
  line-height: 1.4;
  white-space: nowrap;
}
.doc-chip:hover:not(:disabled) {
  background: rgba(91,141,184,0.06);
  border-color: rgba(91,141,184,0.20);
}
.doc-chip:disabled { opacity: 0.5; cursor: progress; }

.doc-chip.active {
  background: rgba(91,141,184,0.10);
  color: var(--accent-primary);
  border-color: rgba(91,141,184,0.25);
}
.doc-chip.active:hover { background: rgba(91,141,184,0.18); }

.doc-chip.printed::after {
  content: '✓';
  margin-left: 4px;
  color: var(--color-success);
  font-weight: 600;
}

.chip-icon  { font-size: 11px; line-height: 1; }
.chip-label { font-family: 'DM Mono', 'JetBrains Mono', monospace; }
</style>
