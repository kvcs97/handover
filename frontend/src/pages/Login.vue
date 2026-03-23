<template>
  <div class="login-wrap">

    <!-- Left Panel -->
    <div class="left-panel">
      <div class="left-content">
        <div class="brand">
          <div class="brand-logo">
            <svg viewBox="0 0 20 20" fill="none">
              <path d="M4 4v12M16 4v12M4 10h12" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
            </svg>
          </div>
          <div>
            <div class="brand-name">HandOver</div>
            <div class="brand-by">by Shoriu</div>
          </div>
        </div>
        <div class="left-body">
          <h1 class="left-title">Abholen.<br>Unterschreiben.<br><em>Fertig.</em></h1>
          <p class="left-sub">Der komplette Übergabe-Workflow in unter 60 Sekunden.</p>
        </div>
        <div class="left-footer">© 2026 Shoriu · 書流</div>
      </div>
    </div>

    <!-- Right Panel -->
    <div class="right-panel">
      <div class="login-card">
        <h2 class="login-title">Willkommen zurück</h2>
        <p class="login-sub">Melde dich mit deinem Account an</p>

        <div class="fields">
          <div class="field">
            <label>E-Mail</label>
            <input
              v-model="email"
              type="email"
              class="input"
              placeholder="name@firma.ch"
              @keyup.enter="login"
              :disabled="loading"
            />
          </div>
          <div class="field">
            <label>Passwort</label>
            <div class="pw-wrap">
              <input
                v-model="password"
                :type="showPw ? 'text' : 'password'"
                class="input"
                placeholder="••••••••"
                @keyup.enter="login"
                :disabled="loading"
              />
              <button type="button" class="pw-toggle" @click="showPw = !showPw">
                {{ showPw ? '🙈' : '👁️' }}
              </button>
            </div>
          </div>
        </div>

        <div class="error-box" v-if="error">{{ error }}</div>

        <button class="btn-login" @click="login" :disabled="loading || !email || !password">
          <span v-if="!loading">Anmelden</span>
          <span v-else class="spinner"></span>
        </button>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const email    = ref('')
const password = ref('')
const loading  = ref(false)
const error    = ref('')
const showPw   = ref(false)

async function login() {
  if (!email.value || !password.value) return
  loading.value = true; error.value = ''
  try {
    await authStore.login(email.value, password.value)
  } catch (e) {
    error.value = e.response?.data?.detail || 'Anmeldung fehlgeschlagen'
  } finally { loading.value = false }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

.login-wrap { display: flex; height: 100vh; font-family: 'DM Sans', sans-serif; }

/* Left */
.left-panel {
  width: 420px; flex-shrink: 0;
  background: linear-gradient(145deg, #1c1c1e 0%, #2c1a1f 100%);
  display: flex; align-items: center; justify-content: center;
  position: relative; overflow: hidden;
}
.left-panel::before {
  content: '書';
  position: absolute; bottom: -40px; right: -40px;
  font-size: 280px; color: rgba(255,255,255,0.03);
  font-family: serif; pointer-events: none;
}
.left-content { padding: 48px; display: flex; flex-direction: column; height: 100%; width: 100%; }

.brand { display: flex; align-items: center; gap: 12px; margin-bottom: auto; }
.brand-logo {
  width: 36px; height: 36px; border-radius: 10px;
  background: linear-gradient(135deg, #f2a7b8, #c0546a);
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 12px rgba(192,84,106,0.4);
}
.brand-logo svg { width: 18px; height: 18px; }
.brand-name { font-family: 'Instrument Serif', serif; font-size: 18px; color: white; letter-spacing: -0.3px; }
.brand-by   { font-size: 11px; color: rgba(255,255,255,0.3); margin-top: 1px; }

.left-body { margin: auto 0; }
.left-title {
  font-family: 'Instrument Serif', serif;
  font-size: 44px; font-weight: 400; color: white;
  letter-spacing: -1.5px; line-height: 1.1; margin-bottom: 16px;
}
.left-title em { font-style: italic; color: #f2a7b8; }
.left-sub { font-size: 15px; color: rgba(255,255,255,0.45); font-weight: 300; line-height: 1.6; }
.left-footer { font-size: 12px; color: rgba(255,255,255,0.2); margin-top: auto; }

/* Right */
.right-panel {
  flex: 1; background: #f2f2f7;
  display: flex; align-items: center; justify-content: center; padding: 48px;
}
.login-card {
  background: white; border-radius: 20px; padding: 40px;
  width: 100%; max-width: 400px;
  box-shadow: 0 2px 20px rgba(0,0,0,0.07), 0 0 0 1px rgba(0,0,0,0.05);
}
.login-title { font-family: 'Instrument Serif', serif; font-size: 28px; font-weight: 400; color: #1c1c1e; letter-spacing: -0.5px; margin-bottom: 4px; }
.login-sub   { font-size: 14px; color: #98989f; font-weight: 300; margin-bottom: 28px; }

.fields { display: flex; flex-direction: column; gap: 16px; margin-bottom: 20px; }
.field  { display: flex; flex-direction: column; gap: 6px; }
.field label { font-size: 12px; font-weight: 600; color: #1c1c1e; text-transform: uppercase; letter-spacing: 0.05em; }
.input {
  padding: 12px 16px; border: 1.5px solid #e8e8ed; border-radius: 11px;
  font-family: 'DM Sans', sans-serif; font-size: 15px; color: #1c1c1e;
  outline: none; background: white; transition: border-color 0.2s, box-shadow 0.2s; width: 100%;
}
.input:focus { border-color: #c0546a; box-shadow: 0 0 0 3px rgba(192,84,106,0.1); }
.input:disabled { background: #f5f5f7; }
.pw-wrap { position: relative; }
.pw-wrap .input { padding-right: 44px; }
.pw-toggle { position: absolute; right: 12px; top: 50%; transform: translateY(-50%); background: none; border: none; cursor: pointer; font-size: 16px; }

.error-box { background: rgba(255,59,48,0.07); border: 1px solid rgba(255,59,48,0.2); border-radius: 10px; padding: 10px 14px; font-size: 13px; color: #c0392b; margin-bottom: 16px; }

.btn-login {
  width: 100%; padding: 13px;
  background: linear-gradient(135deg, #e8849a, #c0546a);
  color: white; border: none; border-radius: 12px;
  font-family: 'DM Sans', sans-serif; font-size: 15px; font-weight: 500;
  cursor: pointer; transition: opacity 0.2s;
  box-shadow: 0 2px 12px rgba(192,84,106,0.3);
  display: flex; align-items: center; justify-content: center; min-height: 48px;
}
.btn-login:hover:not(:disabled) { opacity: 0.9; }
.btn-login:disabled { opacity: 0.45; cursor: not-allowed; }
.spinner { width: 18px; height: 18px; border: 2px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: spin 0.7s linear infinite; }

@keyframes spin { to { transform: rotate(360deg); } }
</style>
