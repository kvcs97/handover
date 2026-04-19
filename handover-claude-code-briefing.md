# HandOver — Claude Code Briefing

> Dieses Dokument ist das vollständige Briefing für Claude Code.
> Lies es komplett bevor du irgendwelchen Code anfasst.

---

## 🎯 Was ist HandOver?

HandOver ist eine **Windows Desktop-App** für die Lagerlogistik, entwickelt von Adam Kovacs (Shoriu, Österreich). Sie digitalisiert den Warenausgabeprozess:

1. Laderreferenz einlesen (Tastatur / Barcode-Scanner)
2. Versanddokumente automatisch per Outlook/E-Mail finden
3. PDFs anzeigen, auswählen, drucken
4. Digitale Unterschrift des Fahrers erfassen
5. Unterschriebenes PDF lokal archivieren

**Aktueller Stand:** v1.5.1 — in internem Pilot bei medmix Switzerland AG

---

## 📁 Repo & Struktur

**GitHub:** `github.com/kvcs97/handover`
**Lokaler Pfad:** `C:\Users\faceb\Desktop\Projekt\handover\`

```
handover/
├── .github/workflows/release.yml   ← CI/CD: PyInstaller + Tauri Build + Portable ZIP
├── backend/                         ← Python FastAPI
│   ├── main.py                      ← FastAPI App + uvicorn entry point
│   ├── database.py                  ← SQLAlchemy Models (users, handovers, carriers, settings)
│   ├── requirements.txt
│   ├── handover.spec                ← PyInstaller Spec (hidden imports!)
│   ├── generate_license.py          ← Lizenzschlüssel-Generator (intern)
│   ├── routers/
│   │   ├── auth.py                  ← JWT Login, get_current_user, require_admin
│   │   ├── handover.py              ← /handover/create, /sign, /list
│   │   ├── carriers.py              ← /carriers/search, CRUD
│   │   ├── settings.py              ← /settings/all, /setup, PUT /{key}
│   │   ├── users.py                 ← /users/ CRUD
│   │   ├── outlook_router.py        ← OAuth2 Device Flow, IMAP search, /test
│   │   └── license_router.py        ← /license/status, /activate, /check
│   └── services/
│       ├── outlook_service.py       ← IMAP OAuth2, Exchange EWS, Graph API
│       ├── pdf_sign.py              ← Unterschrift in PDF einbetten
│       ├── pdf_gen.py               ← PDF aus Template (WeasyPrint)
│       ├── printer.py               ← Druckauftrag
│       └── license_service.py       ← HMAC-SHA256 Lizenzvalidierung
├── frontend/
│   ├── package.json                 ← version: 1.5.1 (muss sync sein!)
│   ├── vite.config.js
│   └── src/
│       ├── api.js                   ← Axios, baseURL: http://localhost:8000
│       ├── stores/auth.js           ← Pinia: JWT, login/logout/restore
│       ├── stores/settings.js       ← Pinia: globale Settings
│       ├── components/
│       │   ├── layout/AppShell.vue  ← Sidebar + Router-View
│       │   └── UpdateChecker.vue    ← Tauri Auto-Updater Banner
│       └── pages/
│           ├── Login.vue
│           ├── Dashboard.vue
│           ├── Handover.vue         ← Kern-Workflow, 5–6 Steps dynamisch
│           ├── Archive.vue
│           ├── Users.vue
│           ├── Settings.vue         ← Firma, Drucker, Outlook OAuth2, Lizenz
│           └── SetupWizard.vue
└── src-tauri/
    ├── tauri.conf.json              ← version: 1.5.1 (muss sync sein!)
    ├── Cargo.toml                   ← version = "1.5.1" (muss sync sein!)
    └── src/main.rs                  ← Backend autostart, check_for_updates
```

---

## 🛠 Tech Stack

| Schicht | Technologie | Version |
|---|---|---|
| Desktop | Tauri 2.0 | 2.x |
| Frontend | Vue 3 + Vite | 3.x |
| Backend | Python FastAPI | 0.115.x |
| Datenbank | SQLite + SQLAlchemy | 2.x |
| Auth | JWT + bcrypt | - |
| E-Mail | MSAL + imaplib (OAuth2) | 1.28.x |
| PDF | pypdf + reportlab | 4.x |
| Build | PyInstaller + NSIS | 6.x |
| CI/CD | GitHub Actions | - |

---

## ⚙️ Lokale Entwicklung starten

```powershell
# Terminal 1 — Backend
cd C:\Users\faceb\Desktop\Projekt\handover\backend
python -m uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd C:\Users\faceb\Desktop\Projekt\handover\frontend
npm run dev

# Oder alles mit einem Klick:
C:\Users\faceb\Desktop\Projekt\handover\start.bat
```

**Backend API Docs:** http://localhost:8000/docs
**Frontend Dev:** http://localhost:5173

---

## 🗄 Datenbank

**Pfad:** `C:\Users\faceb\.handover\handover.db`

Tabellen:
- `users` — id, name, email, password_hash, role (admin/viewer), is_active
- `handovers` — id, referenz, carrier_id, truck_plate, driver_name, status, signed_pdf_path, user_id
- `carriers` — id, company_name, last_used
- `settings` — key, value (alle App-Einstellungen als Key-Value)

**Wichtige Settings-Keys:**
```
company_name, company_address, company_logo_b64
printer_name
data_source_type          → manual / csv / api / outlook
outlook_type              → imap / graph / exchange
outlook_email
outlook_password
outlook_tenant_id
outlook_client_id
outlook_server
outlook_imap_server
outlook_access_token      ← OAuth2 Token (wird nach Login gesetzt)
outlook_refresh_token
license_key
```

---

## 🔐 Auth-System

**Login:** POST `/auth/login` mit URLSearchParams (`username`, `password`)
**Token:** JWT, 8h Gültigkeitsdauer, in localStorage gespeichert
**Rollen:** `admin` (alles), `viewer` (nur Handover-Workflow)
**Dependencies:** `get_current_user()`, `require_admin()` in FastAPI

```python
# Beispiel: geschützter Endpoint
@router.get("/beispiel")
def beispiel(user=Depends(get_current_user)):
    ...

# Admin-only Endpoint
@router.post("/admin-only")
def admin(user=Depends(require_admin)):
    ...
```

---

## 📧 Outlook OAuth2 Integration

**Status:** Login funktioniert, E-Mail-Suche noch geblockt ❌

**Azure App Registration:**
- Client ID: `030d437c-961a-49a4-b088-f2f493d9b71d`
- Authority: `https://login.microsoftonline.com/consumers` (persönliche Konten!)
- Scopes: `["https://outlook.office.com/IMAP.AccessAsUser.All"]`
- Platform: Mobile and desktop applications ✅
- Allow public client flows: Yes ✅

**Flow:**
1. Frontend POST `/outlook/login/start` → bekommt `user_code` + `verification_url`
2. User öffnet URL, gibt Code ein, loggt sich bei Microsoft ein
3. Frontend POST `/outlook/login/complete` → Token wird in `settings.outlook_access_token` gespeichert
4. IMAP-Verbindung via XOAUTH2: `user={email}\x01auth=Bearer {token}\x01\x01`
5. IMAP Server: `outlook.office365.com:993`

**Bekannter Bug:** E-Mail-Suche nach OAuth2-Login findet keine Mails.
Verdacht: Token wird korrekt gespeichert, aber `_search_imap_oauth()` in `outlook_service.py`
hat möglicherweise einen Fehler in der XOAUTH2-Auth-String Konstruktion oder
der IMAP-Suchbefehl ist falsch formatiert.

---

## 🎨 Design System

**Farben:**
```css
--primary:        #c0546a   /* Sakura Rosa */
--primary-light:  #e8849a   /* Gradient Start */
--bg:             #f2f2f7   /* Seitenhintergrund */
--surface:        #ffffff   /* Karten */
--border:         #e8e8ed
--text:           #1c1c1e
--text-muted:     #6e6e73
--text-subtle:    #98989f

/* Gradient Buttons */
background: linear-gradient(135deg, #e8849a, #c0546a);
box-shadow: 0 2px 12px rgba(192,84,106,0.3);
```

**Fonts:**
```css
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&family=DM+Mono&display=swap');

/* Instrument Serif → Seitentitel, Überschriften (kursiv für Akzent) */
/* DM Sans → alles andere */
/* DM Mono → Lizenzschlüssel, technische Werte */
```

**Seitenstruktur:**
```css
.page { padding: 40px 44px; max-width: 900px; }
.page-eyebrow { font-size: 12px; text-transform: uppercase; color: #98989f; }
.page-title { font-family: 'Instrument Serif'; font-size: 38px; color: #1c1c1e; }
.page-title em { font-style: italic; color: #c0546a; }
```

---

## 🚀 Release-Prozess

**Versionen immer in allen 3 Dateien synchron halten:**
- `frontend/package.json` → `"version": "X.Y.Z"`
- `frontend/src-tauri/tauri.conf.json` → `"version": "X.Y.Z"`
- `frontend/src-tauri/Cargo.toml` → `version = "X.Y.Z"`

```bash
git add .
git commit -m "vX.Y.Z — Beschreibung"
git tag vX.Y.Z
git push origin main --tags
```

→ GitHub Actions baut automatisch: `.exe`, `.msi`, `_portable.zip`, `latest.json`

**GitHub Secrets:** `TAURI_SIGNING_PRIVATE_KEY`, `TAURI_SIGNING_PRIVATE_KEY_PASSWORD`

---

## ⚠️ Bekannte Bugs & offene Punkte

### 🔴 Priorität 1 — E-Mail-Suche funktioniert nicht
**Datei:** `backend/services/outlook_service.py`, Funktion `_search_imap_oauth()`
**Problem:** OAuth2 Token ist vorhanden, aber IMAP-Suche findet keine E-Mails
**Was zu prüfen ist:**
- Auth-String korrekt? `f"user={email}\x01auth=Bearer {token}\x01\x01"` → Base64
- IMAP `authenticate("XOAUTH2", ...)` — Callback-Format stimmt?
- Suchbefehl: `mail.search(None, f'SUBJECT "{referenz}"')` — korrekt für IMAP?
- Token abgelaufen? Refresh-Token vorhanden?

### 🔴 Priorität 2 — Settings-Felder leer nach Reload
**Datei:** `frontend/src/pages/Settings.vue`, Funktion `loadSettings()`
**Problem:** Outlook-Felder (email, client_id, tenant_id etc.) erscheinen leer nach Seitenwechsel
**Fix vorbereitet:** `loadSettings()` prüft bereits `outlook_access_token` und setzt `outlookLoggedIn.value = true`, aber Felder werden trotzdem nicht befüllt
**Was zu prüfen:** `/settings/all` Endpoint — gibt er alle Outlook-Keys zurück? `Object.keys(form.value)` — sind alle Outlook-Keys im form-Objekt?

### 🟡 Priorität 3 — Auto-Updater testen
**Ablauf:** v1.5.0 installieren → v1.5.1 pushen → prüfen ob Update-Banner erscheint
**UpdateChecker.vue** ruft `invoke('check_for_updates')` auf → `main.rs` prüft `latest.json`

### 🟡 Priorität 4 — Testdruck mit echtem Netzwerkdrucker
**Datei:** `backend/services/printer.py`
**"Microsoft Print to PDF"** funktioniert nicht (virtueller Drucker)
Echter Netzwerkdrucker bei medmix nötig für echten Test

---

## 🔑 Lizenz-System

**Schlüssel generieren:**
```bash
cd backend
python generate_license.py
# → interaktiv: Kundenname, E-Mail, Plan, Laufzeit, User-Anzahl
# → gibt XXXXX-XXXXX-XXXXX-XXXXX-XXXXX zurück
# → speichert in ~/.handover/licenses.json
```

**Wichtig:** `licenses.json` muss beim Kunden unter `%USERPROFILE%\.handover\` vorhanden sein.

---

## 📦 Wichtige Konfigurationswerte

| Key | Wert |
|---|---|
| Azure Client ID | `030d437c-961a-49a4-b088-f2f493d9b71d` |
| Azure Tenant | `consumers` |
| IMAP Server Outlook | `outlook.office365.com:993` |
| Backend Port | `8000` |
| Installationspfad | `C:\Users\faceb\AppData\Local\Programs\HandOver\` |
| Datenbank | `C:\Users\faceb\.handover\handover.db` |
| Archiv | `C:\Users\faceb\.handover\archive\` |
| GitHub Repo | `github.com/kvcs97/handover` |

---

## 💡 Wichtige Patterns & Fallstricke

1. **Versionen immer synchron** — package.json + tauri.conf.json + Cargo.toml müssen gleich sein
2. **PyInstaller hidden imports** — neue Python-Pakete müssen in `handover.spec` unter `hiddenimports` eingetragen werden
3. **Tauri resources** — Array-Syntax: `"resources": ["handover-backend.exe"]` (nicht Objekt-Syntax)
4. **CORS** — Backend nutzt `allow_origins=["*"]` weil die installierte App nicht auf localhost:5173 läuft
5. **Microsoft OAuth2** — muss `/consumers` Authority nutzen, nicht Tenant-ID für persönliche Konten
6. **Settings speichern** — jedes einzelne Setting wird als Key-Value in der `settings` Tabelle gespeichert, nicht als JSON
7. **Minimal diffs** — Adam bevorzugt kleine, gezielte Änderungen statt komplette Datei-Rewrites
8. **Deutsche UI** — alle User-facing Texte auf Deutsch

---

*Briefing erstellt: April 2026 · HandOver v1.5.1*
