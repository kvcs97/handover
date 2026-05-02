<template>
  <div class="mode-switch" role="tablist" aria-label="Modus wechseln">
    <button
      type="button"
      role="tab"
      class="seg"
      :class="{ active: courier.mode === 'lkw' }"
      :aria-selected="courier.mode === 'lkw'"
      @click="courier.setMode('lkw')"
    >
      <span class="seg-icon" aria-hidden="true">🚚</span>
      <span class="seg-label">LKW</span>
    </button>
    <button
      type="button"
      role="tab"
      class="seg"
      :class="{ active: courier.mode === 'courier' }"
      :aria-selected="courier.mode === 'courier'"
      @click="courier.setMode('courier')"
    >
      <span class="seg-icon" aria-hidden="true">📦</span>
      <span class="seg-label">Kurier</span>
    </button>
    <span class="indicator" :class="courier.mode" aria-hidden="true"></span>
  </div>
</template>

<script setup>
import { useCourierStore } from '../../stores/courier'
const courier = useCourierStore()
</script>

<style scoped>
.mode-switch {
  position: relative;
  display: grid;
  grid-template-columns: 1fr 1fr;
  align-items: stretch;
  height: 36px;
  min-width: 160px;
  padding: 3px;
  background: rgba(0, 0, 0, 0.04);
  border-radius: 999px;
  border: 1px solid rgba(0, 0, 0, 0.05);
  font-family: 'DM Sans', sans-serif;
  user-select: none;
}

.seg {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-muted);
  border-radius: 999px;
  transition: color 200ms ease;
  padding: 0 10px;
  white-space: nowrap;
}
.seg:hover { color: var(--color-text); }
.seg.active { color: #fff; }

.seg-icon { font-size: 13px; line-height: 1; }
.seg-label { letter-spacing: 0.02em; }

.indicator {
  position: absolute;
  top: 3px;
  bottom: 3px;
  left: 3px;
  width: calc(50% - 3px);
  border-radius: 999px;
  background: var(--accent-primary);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.12);
  transition: transform 200ms ease, background-color 200ms ease;
  z-index: 0;
}
.indicator.courier { transform: translateX(100%); }
</style>
