<template>
  <span class="status-badge" :class="`status-${status}`">
    <span class="status-dot" />
    {{ label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: { type: String, default: 'open' },   // open | printed | signed | archived | error
})

const LABELS = {
  open:      'Offen',
  printed:   'Gedruckt',
  signed:    'Unterschrieben',
  archived:  'Archiviert',
  error:     'Zuordnung prüfen',
}

const label = computed(() => LABELS[props.status] || props.status)
</script>

<style scoped>
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  border-radius: 9999px;
  font-size: 11px;
  font-weight: 500;
  font-family: 'DM Sans', sans-serif;
  white-space: nowrap;
  line-height: 1.4;
}
.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.status-open      { background: rgba(91,141,184,0.10); color: var(--accent-primary); }
.status-printed   { background: rgba(245,158,11,0.12); color: #B45309; }
.status-signed    { background: rgba(34,197,94,0.12);  color: #15803D; }
.status-archived  { background: #F1F1F1;               color: var(--color-text-muted); }
.status-error     { background: rgba(239,68,68,0.10);  color: var(--color-danger); }
</style>
