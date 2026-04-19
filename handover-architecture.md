# HandOver – Technische Architektur

> Basierend auf: handover-concept.md

---

## 1. Tech Stack

| Schicht | Technologie | Version | Begründung |
|---|---|---|---|
| Desktop-Framework | Tauri 2.0 | 2.x | Nativer Windows-Build, kleiner Bundle, Rust-basiert |
| Frontend | Vue 3 + Vite | Vue 3.x | Reaktiv, leichtgewichtig, gleicher Stack wie Werkli |
| Backend | Python FastAPI | 0.115.x | Schnell, async, ideal für lokalen API-Server |
| Datenbank | SQLite + SQLAlchemy | 2.x | Lokal, kein Server, für 1–20 User ausreichend |
| Auth | JWT (PyJWT + bcrypt) | - | Einfach, lokal, kein externer Dienst |
| PDF-Verarbeitung | pypdf + reportlab | 4.x | Unterschrift einbetten, Overlay erstellen |
| E-Mail | MSAL + IMAP (imaplib) | 1.28.x | OAuth2 für Outlook.com, IMAP für Abruf |
| Build/Packaging | PyInstaller + NSIS | 6.x | Backend als .exe, currentUser Install |
| CI/CD | GitHub Actions | - | Automatischer Build + Release bei git tag |
| Updates | Tauri Updater Plugin | 2.x | Signierte Updates via GitHub Releases |

---

## 2. Projektstruktur

```
handover/
├── .github/
│   └── workflows/
│       └── release.yml          ← Build, PyInstaller, Tauri Bundle, Portable ZIP
├── backend/
│   ├── main.py                  ← FastAPI App + Uvicorn Entry Point
│   ├── database.py              ← SQLAlchemy Models + init_db()
│   ├── requirements.txt
│   ├── handover.spec            ← PyInstaller Spec (hidden imports)
│   ├── generate_license.py      ← Lizenzschlüssel-Generator (intern)
│   ├── routers/
│   │   ├── auth.py              ← Login, JWT, get_current_user, require_admin
│   │   ├── handover.py          ← /handover/create, /sign, /list
│   │   ├── carriers.py          ← /carriers/search, CRUD
│   │   ├── settings.py          ← /settings/all, /setup, PUT /{key}
│   │   ├── users.py             ← /users/ CRUD
│   │   ├── outlook_router.py    ← /outlook/login/start, /complete, /search, /test
│   │   └── license_router.py   ← /license/status, /activate, /check
│   └── services/
│       ├── outlook_service.py   ← IMAP OAuth2, Exchange EWS, Graph API
│       ├── pdf_sign.py          ← Unterschrift in PDF einbetten
│       ├── pdf_gen.py           ← PDF aus Template generieren (WeasyPrint)
│       ├── printer.py           ← Druckauftrag senden
│       └── license_service.py   ← HMAC-SHA256 Lizenzvalidierung
├── frontend/
│   ├── package.json             ← version muss mit tauri.conf.json + Cargo.toml sync sein
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.js
│       ├── App.vue              ← UpdateChecker eingebunden
│       ├── api.js               ← Axios, baseURL: http://localhost:8000
│       ├── stores/
│       │   ├── auth.js          ← Pinia: JWT, login/logout, restore
│       │   └── settings.js      ← Pinia: globale Settings
│       ├── components/
│       │   ├── layout/
│       │   │   └── AppShell.vue ← Sidebar + Router-View
│       │   └── UpdateChecker.vue ← Tauri invoke check_for_updates
│       └── pages/
│           ├── Login.vue
│           ├── Dashboard.vue
│           ├── Handover.vue     ← 5–6 Schritte Workflow (dynamisch je nach Datenquelle)
│           ├── Archive.vue
│           ├── Users.vue
│           ├── Settings.vue     ← Firma, Drucker, Datenquelle, Outlook, Lizenz
│           └── SetupWizard.vue  ← Ersteinrichtung, 5 Schritte
└── src-tauri/
    ├── tauri.conf.json          ← version, bundle.resources, updater pubkey
    ├── Cargo.toml               ← version muss sync sein
    ├── build.rs
    ├── icons/                   ← Sakura-branded Icons
    └── src/
        └── main.rs              ← Backend autostart, check_for_updates, install_update
```

---

## 3. Routing & Seiten

| Route | Seite | Zugriffsschutz | Beschreibung |
|---|---|---|---|
| `/setup` | SetupWizard | Public (nur wenn DB leer) | Ersteinrichtung: Firma, Drucker, Datenquelle, Admin |
| `/login` | Login | Public | JWT-Login mit E-Mail + Passwort |
| `/` | Dashboard | Auth | Statistiken, letzte Übergaben, Schnellzugriff |
| `/handover` | Neue Übergabe | Auth | 5–6 Schritte Workflow |
| `/archive` | Archiv | Auth | Alle abgeschlossenen Übergaben, Suche/Filter |
| `/users` | Benutzer | Admin only | Benutzer anlegen, bearbeiten, deaktivieren |
| `/settings` | Einstellungen | Admin only | Firma, Drucker, Datenquelle, Outlook OAuth2, Lizenz |

---

## 4. State Management

- **Lokaler State** (Vue ref/reactive): Formular-Inputs, Stepper-Schritt, Dropdown-Sichtbarkeit
- **Pinia Stores**:
  - `auth.js` — JWT-Token, Benutzername, Rolle, login/logout/restore
  - `settings.js` — globale App-Settings (Firmenname, Druckername etc.)
- **Server State**: direkt via Axios (`api.js`), kein React Query equivalent — einfache fetch-on-mount Pattern

---

## 5. Datenbankschema

### `users`

| Spalte | Typ | Constraint | Beschreibung |
|---|---|---|---|
| `id` | INTEGER | PK, autoincrement | |
| `created_at` | DATETIME | default now() | |
| `name` | VARCHAR | NOT NULL | Anzeigename |
| `email` | VARCHAR | UNIQUE, NOT NULL | Login-E-Mail |
| `password_hash` | VARCHAR | NOT NULL | bcrypt Hash |
| `role` | VARCHAR | NOT NULL, default 'viewer' | 'admin' oder 'viewer' |
| `is_active` | BOOLEAN | default true | Deaktivierte User können sich nicht einloggen |

### `handovers`

| Spalte | Typ | Constraint | Beschreibung |
|---|---|---|---|
| `id` | INTEGER | PK, autoincrement | |
| `created_at` | DATETIME | default now() | |
| `referenz` | VARCHAR | NOT NULL | Ladereferenz / Auftragsnummer |
| `carrier_id` | INTEGER | FK → carriers.id | Spediteur |
| `truck_plate` | VARCHAR | nullable | LKW-Kennzeichen |
| `driver_name` | VARCHAR | nullable | Name des Fahrers |
| `status` | VARCHAR | default 'open' | 'open', 'printed', 'signed', 'archived' |
| `signed_pdf_path` | VARCHAR | nullable | Lokaler Pfad zum archivierten PDF |
| `signed_at` | DATETIME | nullable | Zeitpunkt der Unterschrift |
| `user_id` | INTEGER | FK → users.id | Wer die Übergabe durchgeführt hat |

### `carriers`

| Spalte | Typ | Constraint | Beschreibung |
|---|---|---|---|
| `id` | INTEGER | PK, autoincrement | |
| `created_at` | DATETIME | default now() | |
| `company_name` | VARCHAR | UNIQUE, NOT NULL | Firmenname des Spediteurs |
| `last_used` | DATETIME | nullable | Für Sortierung im Dropdown |

### `settings`

| Spalte | Typ | Constraint | Beschreibung |
|---|---|---|---|
| `id` | INTEGER | PK, autoincrement | |
| `key` | VARCHAR | UNIQUE, NOT NULL | Einstellungs-Key |
| `value` | TEXT | nullable | Einstellungs-Wert |

**Wichtige Settings-Keys:**
- `company_name`, `company_address`, `company_logo_b64`
- `printer_name`
- `data_source_type` — `manual`, `csv`, `api`, `outlook`
- `outlook_type` — `imap`, `graph`, `exchange`
- `outlook_email`, `outlook_password`, `outlook_tenant_id`, `outlook_client_id`
- `outlook_server`, `outlook_imap_server`
- `outlook_access_token`, `outlook_refresh_token`
- `license_key`

### Relationen

```
users 1 ──── N handovers   (über user_id)
carriers 1 ── N handovers  (über carrier_id)
```

---

## 6. Authentifizierung & Rollen

| Rolle | Beschreibung | Berechtigungen |
|---|---|---|
| `admin` | Teamleiter / einrichtender Benutzer | Alles: Users, Settings, Handover, Archive |
| `viewer` | Lagerist | Nur Handover-Workflow und eigenes Archiv |

**Auth-Flow:**
1. App startet → `auth.restore()` prüft localStorage auf gespeicherten JWT-Token
2. Kein Token → Weiterleitung zu `/login`
3. POST `/auth/login` mit `username` + `password` (URLSearchParams)
4. Backend prüft bcrypt Hash, gibt JWT zurück (8h Gültigkeitsdauer)
5. Token in localStorage + Axios default header gesetzt
6. Alle geschützten Endpoints prüfen `get_current_user()` Dependency
7. Admin-Endpoints prüfen zusätzlich `require_admin()` Dependency

---

## 7. API-Endpunkte

### Auth
| Method | Endpoint | Beschreibung |
|---|---|---|
| POST | `/auth/login` | Login, gibt JWT zurück |

### Handover
| Method | Endpoint | Beschreibung |
|---|---|---|
| POST | `/handover/create` | Neue Übergabe anlegen |
| POST | `/handover/sign` | Unterschrift einbetten + archivieren |
| GET | `/handover/list` | Alle Übergaben (gefiltert) |
| GET | `/handover/today` | Heutige Übergaben für Dashboard |

### Outlook
| Method | Endpoint | Beschreibung |
|---|---|---|
| POST | `/outlook/login/start` | OAuth2 Device Flow starten |
| POST | `/outlook/login/complete` | OAuth2 Token abholen + speichern |
| GET | `/outlook/search/{referenz}` | E-Mails nach Referenz suchen |
| GET | `/outlook/attachment/{ref}/{id}` | PDF-Inhalt als Base64 |
| POST | `/outlook/process` | PDFs unterschreiben + drucken |
| POST | `/outlook/test` | Verbindung testen |

### Settings
| Method | Endpoint | Beschreibung |
|---|---|---|
| GET | `/settings/all` | Alle Settings als Dict |
| PUT | `/settings/{key}` | Einzelnen Wert speichern |
| POST | `/settings/setup` | SetupWizard abschliessen |
| POST | `/settings/test-print` | Testdruck senden |

### License
| Method | Endpoint | Beschreibung |
|---|---|---|
| GET | `/license/status` | Lizenzstatus mit Details |
| POST | `/license/activate` | Lizenzschlüssel aktivieren |
| GET | `/license/check` | Schnellprüfung (kein Auth) |

---

## 8. Umgebungsvariablen / Konfiguration

```
# Keine .env nötig — alles wird in SQLite Settings gespeichert
# Ausnahme: Backend-interne Konstante in license_service.py
LICENSE_SECRET = "SHORIU_HANDOVER_2026_SECRET_KEY_PRODUCTION"  # in Code hardcoded

# Azure OAuth2 (werden in DB gespeichert, nicht als Env Vars)
AZURE_CLIENT_ID = "030d437c-961a-49a4-b088-f2f493d9b71d"
AZURE_AUTHORITY = "https://login.microsoftonline.com/consumers"
IMAP_SCOPE = "https://outlook.office.com/IMAP.AccessAsUser.All"
```

---

## 9. Build & Deployment

### Versionierung
Alle drei Dateien müssen immer synchron sein:
- `frontend/package.json` → `"version": "X.Y.Z"`
- `frontend/src-tauri/tauri.conf.json` → `"version": "X.Y.Z"`
- `frontend/src-tauri/Cargo.toml` → `version = "X.Y.Z"`

### Release-Prozess
```bash
# 1. Versionen in allen 3 Dateien erhöhen
# 2. Commit + Push
git add .
git commit -m "v1.X.Y — Beschreibung"
git tag vX.Y.Z
git push origin main --tags
# → GitHub Actions baut automatisch:
#   - handover-backend.exe (PyInstaller)
#   - HandOver_x64-setup.exe (NSIS Installer)
#   - HandOver_x64_en-US.msi (MSI Installer)
#   - HandOver_portable.zip (kein Installer)
#   - latest.json (Auto-Updater Manifest)
```

### Installationsordner (nach NSIS currentUser)
```
C:\Users\{USER}\AppData\Local\Programs\HandOver\
├── handover.exe
├── handover-backend.exe   ← aus bundle.resources
└── ...

C:\Users\{USER}\.handover\
├── handover.db            ← SQLite Datenbank
├── archive\               ← Archivierte PDFs
└── licenses.json          ← Lizenzschlüssel
```

---

## 10. Bekannte Risiken & Entscheidungen

| Thema | Entscheidung | Risiko |
|---|---|---|
| Outlook Auth | OAuth2 Device Flow (consumers) | Microsoft-Richtlinien können sich ändern |
| Lokale DB | SQLite (kein Server) | Kein Mehrbenutzerzugriff von mehreren Rechnern |
| Backend als .exe | PyInstaller onefile | Startup-Zeit ~2–3s, Antivirus könnte flaggen |
| currentUser Install | AppData\Local | Kein Admin nötig, aber kein systemweiter Zugriff |
| License offline | HMAC + lokale JSON | licenses.json muss beim Kunden deployt werden |
| Auto-Updater | Tauri Updater + GitHub Releases | Bei Signing-Key-Verlust keine Updates mehr möglich |

---

## 11. Nächste Schritte

- [ ] E-Mail-Suche OAuth2 Token-Übergabe debuggen
- [ ] Settings loadSettings() Outlook-Felder Fix deployen
- [ ] Auto-Updater vollständig testen
- [ ] UI/Design festlegen → *handover-ui-design.md*
- [ ] Entwicklung tracken → *handover-tracker.md*

---

*Erstellt mit dem app-architecture Skill · April 2026*
