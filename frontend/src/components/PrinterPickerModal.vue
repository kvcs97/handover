<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-card">
      <div class="modal-header">
        <h3>Drucker auswählen</h3>
        <button class="btn-close" @click="$emit('close')">✕</button>
      </div>

      <input
        v-model="search"
        class="search-input"
        placeholder="Drucker suchen…"
        autofocus
      />

      <div class="printer-list" v-if="!loading && filtered.length">
        <button
          v-for="p in filtered"
          :key="p.name"
          class="printer-item"
          @click="select(p)"
        >
          <span class="printer-icon">🖨️</span>
          <div class="printer-info">
            <strong>{{ p.name }}</strong>
            <span class="printer-port" v-if="p.port">{{ p.port }}</span>
          </div>
          <span class="badge" :class="p.type">
            {{ p.type === 'local' ? 'Lokal' : 'Netzwerk' }}
          </span>
        </button>
      </div>

      <div class="empty" v-else-if="!loading">
        <span>🔍</span>
        <p v-if="search">Kein Drucker passt zu «{{ search }}»</p>
        <p v-else>Keine Drucker gefunden</p>
      </div>

      <div class="loading" v-else>
        <div class="spinner"></div>
        <span>Drucker werden geladen…</span>
      </div>

      <div class="modal-footer">
        <button class="btn-ghost" @click="$emit('close')">Abbrechen</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api'

const emit = defineEmits(['select', 'close'])

const printers = ref([])
const search   = ref('')
const loading  = ref(true)

onMounted(async () => {
  try {
    const res = await api.get('/settings/printers')
    printers.value = res.data || []
  } catch (e) {
    console.error('Drucker konnten nicht geladen werden:', e)
    printers.value = []
  } finally {
    loading.value = false
  }
})

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return printers.value
  return printers.value.filter(p => p.name.toLowerCase().includes(q))
})

function select(printer) {
  emit('select', printer.name)
  emit('close')
}
</script>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(4px);
  z-index: 400;
  display: flex; align-items: center; justify-content: center;
  padding: 24px;
  animation: fadeIn 0.15s ease both;
}

.modal-card {
  background: white;
  border-radius: 18px;
  width: 100%; max-width: 480px;
  max-height: 80vh;
  display: flex; flex-direction: column;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.25);
  overflow: hidden;
  animation: popIn 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275) both;
  font-family: 'DM Sans', sans-serif;
}

.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 20px 24px 12px;
}
.modal-header h3 {
  font-family: 'Instrument Serif', serif;
  font-size: 22px; font-weight: 400;
  color: #1c1c1e; letter-spacing: -0.5px;
}
.btn-close {
  width: 28px; height: 28px;
  background: #f5f5f7; border: none; border-radius: 50%;
  cursor: pointer; font-size: 12px; color: #6e6e73;
}
.btn-close:hover { background: #ebebf0; }

.search-input {
  margin: 0 24px 12px;
  padding: 11px 16px;
  border: 1.5px solid #e8e8ed;
  border-radius: 11px;
  font-family: 'DM Sans', sans-serif;
  font-size: 14px; color: #1c1c1e;
  outline: none;
  transition: all 0.2s;
}
.search-input:focus {
  border-color: #c0546a;
  box-shadow: 0 0 0 3px rgba(192, 84, 106, 0.1);
}

.printer-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 12px 8px;
  display: flex; flex-direction: column; gap: 4px;
}

.printer-item {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 14px;
  background: white;
  border: 1.5px solid transparent;
  border-radius: 11px;
  cursor: pointer;
  transition: all 0.12s;
  width: 100%;
  text-align: left;
  font-family: 'DM Sans', sans-serif;
}
.printer-item:hover {
  background: #fafafa;
  border-color: rgba(192, 84, 106, 0.25);
}
.printer-icon { font-size: 20px; flex-shrink: 0; }
.printer-info { flex: 1; min-width: 0; }
.printer-info strong {
  display: block; font-size: 14px; font-weight: 500;
  color: #1c1c1e;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.printer-port {
  display: block; font-size: 11px; color: #98989f;
  margin-top: 2px;
}

.badge {
  font-size: 10px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.04em;
  padding: 3px 8px; border-radius: 6px;
  flex-shrink: 0;
}
.badge.local    { background: rgba(40, 200, 64, 0.1);   color: #1a7a2e; }
.badge.network  { background: rgba(0, 113, 227, 0.1);   color: #0056b3; }

.empty, .loading {
  display: flex; flex-direction: column; align-items: center;
  gap: 8px; padding: 40px 24px;
  color: #98989f; font-size: 13px;
}
.empty span { font-size: 28px; }

.spinner {
  width: 24px; height: 24px;
  border: 3px solid #f0f0f0; border-top-color: #c0546a;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

.modal-footer {
  display: flex; justify-content: flex-end;
  padding: 12px 24px 20px;
  border-top: 1px solid #f5f5f7;
}
.btn-ghost {
  padding: 9px 18px;
  background: white;
  border: 1.5px solid #e8e8ed;
  border-radius: 10px;
  font-family: 'DM Sans', sans-serif;
  font-size: 13px; font-weight: 500;
  color: #6e6e73;
  cursor: pointer;
  transition: all 0.15s;
}
.btn-ghost:hover { background: #f5f5f7; color: #1c1c1e; }

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes popIn  { from { transform: scale(0.92); opacity: 0; } to { transform: scale(1); opacity: 1; } }
@keyframes spin   { to { transform: rotate(360deg); } }
</style>
