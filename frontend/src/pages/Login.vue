<template>
  <div class="login-root">

    <!-- Left: Branding Panel -->
    <div class="brand-panel">
      <div class="brand-inner">
        <div class="brand-logo">
          <span class="logo-mark">H</span>
        </div>
        <div class="brand-text">
          <h1 class="brand-name">HandOver</h1>
          <p class="brand-by">by Shoriu</p>
        </div>
        <div class="brand-tagline">
          <p>Abholen.</p>
          <p>Unterschreiben.</p>
          <p class="tagline-em">Fertig.</p>
        </div>
        <div class="brand-steps">
          <div class="step" v-for="(s, i) in steps" :key="i" :style="`animation-delay:${0.6 + i*0.12}s`">
            <span class="step-icon">{{ s.icon }}</span>
            <span class="step-label">{{ s.label }}</span>
          </div>
        </div>
      </div>
      <div class="brand-footer">shoriu.com/handover</div>
    </div>

    <!-- Right: Login Form -->
    <div class="form-panel">
      <div class="form-inner">

        <div class="form-header">
          <h2 class="form-title">Anmelden</h2>
          <p class="form-subtitle">Willkommen zurück</p>
        </div>

        <form class="form" @submit.prevent="handleLogin">

          <div class="field" :class="{ error: errors.email }">
            <label>E-Mail</label>
            <input
              v-model="email"
              type="email"
              placeholder="name@firma.ch"
              autocomplete="email"
              @input="errors.email = ''"
            />
            <span class="field-error" v-if="errors.email">{{ errors.email }}</span>
          </div>

          <div class="field" :class="{ error: errors.password }">
            <label>Passwort</label>
            <div class="password-wrap">
              <input
                v-model="password"
                :type="showPw ? 'text' : 'password'"
                placeholder="••••••••"
                autocomplete="current-password"
                @input="errors.password = ''"
              />
              <button type="button" class="pw-toggle" @click="showPw = !showPw">
                {{ showPw ? '🙈' : '👁️' }}
              </button>
            </div>
            <span class="field-error" v-if="errors.password">{{ errors.password }}</span>
          </div>

          <div class="form-error" v-if="loginError">
            {{ loginError }}
          </div>

          <button class="btn-login" :class="{ loading }" :disabled="loading" type="submit">
            <span v-if="!loading">Anmelden</span>
            <span v-else class="spinner"></span>
          </button>

        </form>

        <div class="form-hint">
          <span>Kein Zugang?</span>
          <span>Administrator kontaktieren.</span>
        </div>

      </div>
    </div>

  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

const email      = ref('')
const password   = ref('')
const showPw     = ref(false)
const loading    = ref(false)
const loginError = ref('')
const errors     = ref({ email: '', password: '' })

const steps = [
  { icon: '⌨️', label: 'Referenz eingeben' },
  { icon: '⚡', label: 'Daten geladen' },
  { icon: '🖨️', label: 'Auto-Druck' },
  { icon: '✍️', label: 'Unterschrift' },
  { icon: '📁', label: 'Archiviert' },
]

async function handleLogin() {
  errors.value = { email: '', password: '' }
  loginError.value = ''

  if (!email.value)    { errors.value.email    = 'E-Mail ist erforderlich'; return }
  if (!password.value) { errors.value.password = 'Passwort ist erforderlich'; return }

  loading.value = true
  try {
    await authStore.login(email.value, password.value)
  } catch (e) {
    loginError.value = e.response?.data?.detail || 'Anmeldung fehlgeschlagen'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500&display=swap');

.login-root {
  display: flex;
  height: 100vh;
  font-family: 'DM Sans', sans-serif;
}

/* ── Brand Panel ─────────────────────────────── */
.brand-panel {
  width: 420px;
  flex-shrink: 0;
  background: #1d1d1f;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 56px 48px;
  position: relative;
  overflow: hidden;
}

.brand-panel::before {
  content: '';
  position: absolute;
  top: -120px; right: -120px;
  width: 400px; height: 400px;
  background: radial-gradient(circle, rgba(0,113,227,0.15) 0%, transparent 70%);
  pointer-events: none;
}

.brand-inner {
  display: flex;
  flex-direction: column;
  gap: 40px;
}

.brand-logo {
  width: 52px; height: 52px;
  background: #0071e3;
  border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  animation: fadeUp 0.6s ease forwards;
}
.logo-mark {
  font-family: 'Instrument Serif', serif;
  font-size: 28px;
  color: white;
  line-height: 1;
}

.brand-text {
  animation: fadeUp 0.6s ease 0.1s both;
}
.brand-name {
  font-family: 'Instrument Serif', serif;
  font-size: 36px;
  font-weight: 400;
  color: white;
  letter-spacing: -1px;
  line-height: 1;
}
.brand-by {
  font-size: 13px;
  color: #6e6e73;
  margin-top: 4px;
  letter-spacing: 0.02em;
}

.brand-tagline {
  animation: fadeUp 0.6s ease 0.2s both;
}
.brand-tagline p {
  font-family: 'Instrument Serif', serif;
  font-size: 28px;
  font-weight: 400;
  color: rgba(255,255,255,0.5);
  line-height: 1.3;
  letter-spacing: -0.5px;
}
.tagline-em {
  color: white !important;
  font-style: italic;
}

.brand-steps {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.step {
  display: flex;
  align-items: center;
  gap: 12px;
  animation: fadeUp 0.5s ease both;
  opacity: 0;
}
.step-icon {
  font-size: 16px;
  width: 32px; height: 32px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
}
.step-label {
  font-size: 13px;
  color: rgba(255,255,255,0.55);
  font-weight: 300;
}

.brand-footer {
  font-size: 11px;
  color: #3a3a3c;
  letter-spacing: 0.04em;
}

/* ── Form Panel ──────────────────────────────── */
.form-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f7;
}

.form-inner {
  width: 100%;
  max-width: 380px;
  padding: 0 24px;
  animation: fadeUp 0.7s ease 0.3s both;
}

.form-header {
  margin-bottom: 40px;
}
.form-title {
  font-family: 'Instrument Serif', serif;
  font-size: 36px;
  font-weight: 400;
  color: #1d1d1f;
  letter-spacing: -1px;
  line-height: 1;
}
.form-subtitle {
  font-size: 15px;
  color: #6e6e73;
  margin-top: 6px;
  font-weight: 300;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.field label {
  font-size: 12px;
  font-weight: 500;
  color: #1d1d1f;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}
.field input {
  width: 100%;
  padding: 13px 16px;
  border: 1.5px solid #e8e8ed;
  border-radius: 12px;
  font-family: 'DM Sans', sans-serif;
  font-size: 15px;
  color: #1d1d1f;
  background: white;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.field input:focus {
  border-color: #0071e3;
  box-shadow: 0 0 0 3px rgba(0,113,227,0.12);
}
.field.error input {
  border-color: #ff3b30;
}
.field-error {
  font-size: 12px;
  color: #ff3b30;
}

.password-wrap {
  position: relative;
}
.password-wrap input {
  padding-right: 44px;
}
.pw-toggle {
  position: absolute;
  right: 12px; top: 50%;
  transform: translateY(-50%);
  background: none; border: none;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  padding: 4px;
}

.form-error {
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 10px;
  padding: 10px 14px;
  font-size: 13px;
  color: #ff3b30;
}

.btn-login {
  width: 100%;
  padding: 14px;
  background: #1d1d1f;
  color: white;
  border: none;
  border-radius: 12px;
  font-family: 'DM Sans', sans-serif;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s, transform 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 50px;
  margin-top: 4px;
}
.btn-login:hover:not(:disabled) {
  background: #000;
  transform: translateY(-1px);
}
.btn-login:disabled { opacity: 0.6; cursor: not-allowed; }

.spinner {
  width: 18px; height: 18px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

.form-hint {
  margin-top: 28px;
  display: flex;
  gap: 4px;
  font-size: 13px;
  color: #98989f;
  justify-content: center;
}

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
