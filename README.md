# HandOver — by Shoriu

> Abholen. Unterschreiben. Fertig.

## Projektstruktur

```
handover/
│
├── backend/                    ← Python + FastAPI
│   ├── main.py                 ← App-Einstiegspunkt
│   ├── database.py             ← SQLite Modelle & Setup
│   ├── requirements.txt        ← Python Dependencies
│   ├── routers/
│   │   ├── auth.py             ← Login, JWT, bcrypt
│   │   ├── handover.py         ← Kern-Workflow
│   │   ├── carriers.py         ← Spediteur-Dropdown
│   │   ├── settings.py         ← Setup Wizard & Einstellungen
│   │   └── users.py            ← Benutzerverwaltung
│   ├── services/
│   │   ├── pdf_gen.py          ← WeasyPrint PDF-Generierung
│   │   └── printer.py          ← Auto-Druck (Win/Mac/Linux)
│   └── templates/
│       └── handover.html       ← PDF-Vorlage (HTML + CSS)
│
├── frontend/                   ← Vue 3 + Vite
│   └── src/
│       ├── App.vue             ← Routing: Setup / Login / App
│       ├── api.js              ← Axios Instance
│       ├── stores/
│       │   └── auth.js         ← Pinia Auth Store
│       ├── pages/
│       │   ├── SetupWizard.vue ← Erster Start (TODO)
│       │   ├── Login.vue       ← Login Screen (TODO)
│       │   ├── Dashboard.vue   ← Übersicht (TODO)
│       │   ├── Handover.vue    ← Kern-Workflow (TODO)
│       │   ├── Archive.vue     ← Archiv (TODO)
│       │   └── Settings.vue    ← Einstellungen Admin (TODO)
│       └── components/
│           └── layout/
│               └── AppShell.vue ← Nav + Layout (TODO)
│
└── src-tauri/                  ← Tauri Desktop Shell


## Tech Stack

| Schicht      | Technologie                    |
|--------------|-------------------------------|
| Desktop      | Tauri 2.0                     |
| Frontend     | Vue 3 + Vite + shadcn-vue     |
| Backend      | Python + FastAPI              |
| Datenbank    | SQLite + SQLAlchemy (lokal)   |
| Auth         | bcrypt + JWT (lokal)          |
| PDF          | WeasyPrint + Jinja2           |
| Druck        | CUPS / Win32Print             |
| Unterschrift | signature_pad.js              |

## Lokale Datenspeicherung

Alle Daten liegen beim Kunden:
- Datenbank: `~/.handover/handover.db`
- Archiv:    `~/.handover/archive/*.pdf`

## Berechtigungen

| Rolle    | Übergabe | Archiv | Benutzer | Einstellungen |
|----------|----------|--------|----------|---------------|
| admin    | ✅       | ✅     | ✅       | ✅            |
| operator | ✅       | ✅     | ❌       | ❌            |
| viewer   | ❌       | ✅     | ❌       | ❌            |

## Workflow

1. Referenz eingeben (Tastatur / Barcode / QR)
2. Auftragsdaten werden automatisch geladen
3. Spediteur-Daten eingeben (Dropdown + Felder)
4. Dokumente drucken automatisch
5. Unterschrift auf dem Gerät
6. PDF wird archiviert ✓
```
