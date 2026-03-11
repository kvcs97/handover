# HandOver — Tauri Desktop App Setup

## Voraussetzungen installieren

```bash
# 1. Rust installieren (einmalig)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# 2. Node.js (v18+) — falls noch nicht vorhanden
# https://nodejs.org

# 3. Python 3.11+ — falls noch nicht vorhanden
# https://python.org

# Windows: zusätzlich benötigt
# - Microsoft C++ Build Tools
# - WebView2 (meist schon vorhanden)
```

---

## Projekt initialisieren

```bash
# Im handover/ Verzeichnis:

# 1. Frontend Dependencies
cd frontend
npm install
npm install vue@3 vue-router@4 pinia@2 axios

# 2. Tauri CLI installieren
npm install --save-dev @tauri-apps/cli@2
npm install @tauri-apps/api@2

# 3. Tauri initialisieren (einmalig)
npx tauri init
# → App name: HandOver
# → Window title: HandOver
# → Web assets: ../dist
# → Dev server: http://localhost:5173
# → Dev command: npm run dev
# → Build command: npm run build

# 4. Python Backend Dependencies
cd ../backend
pip install -r requirements.txt
```

---

## Dateistruktur nach Tauri Init

```
handover/
├── src-tauri/
│   ├── src/
│   │   └── main.rs          ← Tauri Entry (ersetzt durch unten)
│   ├── icons/               ← App Icons
│   ├── Cargo.toml           ← Rust Dependencies
│   └── tauri.conf.json      ← Tauri Konfiguration (ersetzt durch unten)
├── frontend/
│   ├── src/
│   ├── vite.config.js
│   └── package.json
└── backend/
    └── main.py
```

---

## Entwicklungsmodus starten

```bash
# Terminal 1: Python Backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2: Tauri App
cd frontend
npx tauri dev
```

---

## Produktions-Build erstellen

```bash
# 1. Python Backend zu .exe packen
cd backend
pyinstaller --onefile --name handover-backend main.py
# Erstellt: backend/dist/handover-backend.exe (Win) oder handover-backend (Mac/Linux)

# 2. Tauri App bauen
cd frontend
npx tauri build
# Erstellt Installer in: src-tauri/target/release/bundle/
```
