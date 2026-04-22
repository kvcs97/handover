# HandOver – Entwicklungs-Tracker

**Letzte Aktualisierung:** 22. April 2026
**Gesamtfortschritt:** 52 / 63 Aufgaben abgeschlossen (83%)

---

## 🔵 Aktueller Fokus

> **✅ v1.6.4 gepusht — 5 Bugfixes implementiert**
> Globale Admin-Einstellungen, PDF-Icon klickbar, alle Drucker sichtbar, Unterschrift mit Mitarbeitername/Datum, doppelte Referenzen mit Suffix. GitHub Actions Release-Build läuft. **Live-Test bei medmix ausstehend.**

---

## ⚠️ Offene Blocker

- [ ] **🔴 Backend Sidecar — Live-Test ausstehend** — v1.5.7 enthält den Sidecar-Fix. Muss bei medmix getestet werden ob AppLocker den Sidecar akzeptiert.
- [ ] **PDF-Signatur Position** — Auf 355pt von oben gesetzt (~125mm), live auf Lieferschein prüfen.
- [ ] **IMAP E-Mail-Suche live** — XOAUTH2-Fix implementiert, aber noch kein Live-Test.

---

## 📋 Aufgaben nach Phase

Status-Legende: ✅ Fertig · 🔄 In Arbeit · ⏳ Offen · ❌ Blockiert · ⏭️ Übersprungen

---

### Phase 0 – Setup & Infrastruktur
| # | Aufgabe | Status | Notiz |
|---|---|---|---|
| 0.1 | GitHub Repo erstellen | ✅ | kvcs97/handover |
| 0.2 | Tauri 2.0 + Vue 3 + FastAPI Stack | ✅ | |
| 0.3 | SQLite + SQLAlchemy | ✅ | ~/.handover/handover.db |
| 0.4 | GitHub Actions CI/CD | ✅ | release.yml |
| 0.5 | PyInstaller + Tauri Bundle | ✅ | handover-backend.exe in resources |
| 0.6 | NSIS currentUser Install | ✅ | AppData\Local, kein Admin |
| 0.7 | Signing Keys + GitHub Secrets | ✅ | |
| 0.8 | Auto-Updater + latest.json | ✅ | UpdateChecker.vue, Sakura Banner |
| 0.9 | Portable ZIP Build | ✅ | HandOver_portable.zip via release.yml |
| 0.10 | **Backend als Tauri Sidecar** | ✅ | v1.5.7: externalBin, tauri-plugin-shell, capabilities/main.json, release.yml angepasst. Live-Test bei medmix ausstehend. |

**Phase-Fortschritt:** 9 / 10 (90%)

---

## 🔴 Tauri Sidecar — Implementierungsplan (für Claude Code)

### Was zu ändern ist:

**1. `tauri.conf.json`** — resources durch sidecar ersetzen:
```json
"bundle": {
  "externalBin": ["binaries/handover-backend"],
  ...
}
```
→ `resources: ["handover-backend.exe"]` entfernen

**2. `Cargo.toml`** — shell plugin hinzufügen:
```toml
tauri-plugin-shell = "2"
```

**3. `main.rs`** — Sidecar statt Command::new:
```rust
use tauri_plugin_shell::ShellExt;
// app.shell().sidecar("handover-backend").unwrap().spawn()
```

**4. `release.yml`** — Backend nach `src-tauri/binaries/` kopieren:
```yaml
- name: Copy backend as sidecar
  run: |
    mkdir -p frontend/src-tauri/binaries
    copy backend\dist\handover-backend.exe frontend\src-tauri\binaries\handover-backend-x86_64-pc-windows-msvc.exe
```
→ Tauri erwartet das Format: `{name}-{target-triple}.exe`

**5. Capabilities** — Shell-Permission in `src-tauri/capabilities/main.json`:
```json
"tauri:allow-shell-execute",
"shell:allow-execute",
"shell:allow-open"
```

### Warum das das Problem löst:
Tauri signiert den Sidecar als Teil des App-Bundles. Windows/AppLocker sieht es als integrierten Bestandteil der installierten App — nicht als fremde `.exe`.

---

### Phase 1 – Auth & Benutzerverwaltung
| # | Aufgabe | Status | Notiz |
|---|---|---|---|
| 1.1 | JWT Login/Logout | ✅ | |
| 1.2 | SetupWizard (Ersteinrichtung) | ✅ | 5 Schritte inkl. Outlook |
| 1.3 | Admin / Viewer Rollen | ✅ | |
| 1.4 | Benutzer verwalten (Users.vue) | ✅ | |
| 1.5 | Passwort ändern | ✅ | |

**Phase-Fortschritt:** 5 / 5 (100%)

---

### Phase 2 – Kernworkflow (Handover)
| # | Aufgabe | Status | Notiz |
|---|---|---|---|
| 2.1 | Referenz eingeben (Step 0) | ✅ | Scanner-kompatibel |
| 2.2 | Spediteur-Daten (Step 1) | ✅ | Combobox + Autocomplete |
| 2.3 | Spediteur-Datenbank | ✅ | Auto-Create |
| 2.4 | Druckschritt (Step 2) | ✅ | |
| 2.5 | Unterschrift Canvas (Step 3) | ✅ | Touch + Maus; zeigt Mitarbeitername + Datum unter Canvas (v1.6.4) |
| 2.6 | PDF Signatur einbetten | 🔄 | Position 355pt von oben — live testen; employee_name ins PDF gebrannt (v1.6.4) |
| 2.7 | Archivieren + Fertig (Step 4) | ✅ | |
| 2.8 | Outlook PDF-Auswahl Step | ✅ | Dynamisch wenn Outlook aktiv |
| 2.9 | PDF Vorschau Modal | ✅ | |
| 2.10 | Unterschrift An/Aus pro PDF | ✅ | |
| 2.11 | PDF-Auswahl: standardmässig alle abgewählt | ⏳ | Aktuell sind alle PDFs vorausgewählt — User soll manuell auswählen welche unterschrieben werden. Fix: `signIndices.value = []` statt `.map((_, i) => i)` in `Handover.vue` |
| 2.12 | PDF-Icon im Archiv klickbar | ✅ | v1.6.4: öffnet lokale Datei mit System-PDF-Viewer via tauri-plugin-shell |
| 2.13 | Doppelte Referenznummer abfangen | ✅ | v1.6.4: `get_unique_reference()` vergibt automatisch `_2`, `_3` … Suffix |

**Phase-Fortschritt:** 11 / 13 (85%)

---

### Phase 3 – Outlook / E-Mail Integration
| # | Aufgabe | Status | Notiz |
|---|---|---|---|
| 3.1 | IMAP Service (outlook_service.py) | ✅ | |
| 3.2 | Exchange EWS Support | ✅ | exchangelib |
| 3.3 | Microsoft Graph API Support | ✅ | msal |
| 3.4 | OAuth2 Device Flow Backend | ✅ | /outlook/login/start + /complete |
| 3.5 | OAuth2 Device Flow Frontend | ✅ | "Mit Microsoft anmelden" Button |
| 3.6 | consumers Endpoint Fix | ✅ | AADSTS9002346 gefixt |
| 3.7 | Azure App Registration | ✅ | Client ID 030d437c... |
| 3.8 | Settings-Felder persistent nach Reload | ✅ | outlook_logged_in Flag in /settings/all |
| 3.9 | E-Mail-Suche nach Referenznummer | ✅ | XOAUTH2 Fix + live getestet ✓ |
| 3.10 | OAuth2 Token-Persistenz | ✅ | _refresh_access_token() via Refresh-Token |
| 3.11 | PDF Anhänge herunterladen + verarbeiten | ⏳ | Abhängig von 3.9 |

**Phase-Fortschritt:** 9 / 11 (82%)

---

### Phase 4 – Einstellungen & Konfiguration
| # | Aufgabe | Status | Notiz |
|---|---|---|---|
| 4.1 | Firmendaten (Name, Adresse, Logo) | ✅ | |
| 4.2 | Drucker konfigurieren | ✅ | v1.6.4: Datalist zeigt alle lokalen + Netzwerkdrucker via `GET /settings/printers` (win32print) |
| 4.3 | Datenquelle (Manual/CSV/API/Outlook) | ✅ | |
| 4.4 | Outlook Konfigurationskarte | ✅ | IMAP/M365/Exchange |
| 4.5 | Testdruck | ⏳ | Echter Netzwerkdrucker nötig |
| 4.6 | Outlook Verbindung testen | 🔄 | XOAUTH2-Bug auch im /test-Endpoint gefixt |
| 4.7 | Archiv-Pfad konfigurierbar | ⏳ | Neues Settings-Feld `archive_path` — User kann Zielordner für archivierte PDFs wählen. Default: `%USERPROFILE%\.handover\archive\`. Backend: `outlook_router.py` + `handover.py` müssen `ARCHIVE_DIR` aus Settings lesen statt hardcoded. Frontend: neues Feld in Settings.vue Firmendaten-Karte mit Ordner-Auswahl Button. |
| 4.8 | Admin-Einstellungen global für alle User | ✅ | v1.6.4: `GET /settings/global` für alle Auth-User; Nicht-Admins sehen Settings read-only |

**Phase-Fortschritt:** 5 / 8 (63%)

---

### Phase 5 – Lizenzschlüssel System
| # | Aufgabe | Status | Notiz |
|---|---|---|---|
| 5.1 | license_service.py (HMAC-SHA256) | ✅ | ~/.handover/licenses.json |
| 5.2 | generate_license.py Script | ✅ | Interaktiv, Shoriu-intern |
| 5.3 | License Router | ✅ | /license/status, /activate, /check |
| 5.4 | Lizenz-Karte in Settings.vue | ✅ | Status, Ablaufdatum, Aktivierung |
| 5.5 | Lizenzschlüssel für medmix | ✅ | XL6V7-VPYM7-C5MXC-RXFAC-7XZV5 |

**Phase-Fortschritt:** 5 / 5 (100%)

---

### Phase 6 – UI / Design (Sakura)
| # | Aufgabe | Status | Notiz |
|---|---|---|---|
| 6.1 | Design System (#c0546a, Fonts) | ✅ | Instrument Serif + DM Sans |
| 6.2 | Login.vue | ✅ | |
| 6.3 | Dashboard.vue | ✅ | |
| 6.4 | Handover.vue | ✅ | Sakura + dynamische Steps |
| 6.5 | Archive.vue | ✅ | |
| 6.6 | Users.vue | ✅ | |
| 6.7 | Settings.vue | ✅ | |
| 6.8 | SetupWizard.vue | ✅ | |
| 6.9 | AppShell + Sidebar | ✅ | |
| 6.10 | UpdateChecker Banner | ✅ | |

**Phase-Fortschritt:** 10 / 10 (100%)

---

### Phase 7 – Testing & Deployment
| # | Aufgabe | Status | Notiz |
|---|---|---|---|
| 7.1 | Interner Pilot bei medmix | 🔄 | v1.5.7 Sidecar-Fix bereit → Installation + Test ausstehend |
| 7.2 | Auto-Updater Test | ✅ | Funktioniert — Repo public gestellt |
| 7.3 | Netzwerkdrucker Test | ⏳ | Bei medmix vor Ort |
| 7.4 | Lizenzschlüssel für medmix | ✅ | XL6V7-VPYM7-C5MXC-RXFAC-7XZV5 |
| 7.5 | IT-Dokumentation an medmix IT | ✅ | HandOver_IT-Dokumentation_medmix.docx |
| 7.6 | Portable ZIP für Firmeneinsatz | ✅ | HandOver_portable.zip |
| 7.7 | medmix als bezahlter Kunde | ⏳ | Ziel für FlexKapG Gründung |

**Phase-Fortschritt:** 4 / 7 (57%)

---

## 🧠 Entscheidungen & Notizen

| Datum | Thema | Entscheidung | Grund |
|---|---|---|---|
| März 2026 | IMAP Auth | OAuth2 Device Flow | Microsoft hat BasicAuth gesperrt |
| März 2026 | Azure Authority | /consumers Endpoint | Persönliche MS-Konten brauchen /consumers |
| März 2026 | Install-Modus | currentUser (AppData) | Kein Admin-Recht nötig |
| März 2026 | Lizenz | HMAC + lokale JSON | Einfach, sicher, offline-fähig |
| März 2026 | PyInstaller | .spec mit hidden imports | Uvicorn + msal müssen explizit deklariert werden |
| April 2026 | Portable ZIP | Extra Build-Step in release.yml | Firmen-IT blockiert .exe Installer |
| April 2026 | Claude Code | Wechsel von Claude.ai zu Claude Code | Direkter Datei-Zugriff, effizienter für Code |
| April 2026 | Token-Refresh | _refresh_access_token() mit MSAL | MS Access Token läuft nach 1h ab |
| April 2026 | PDF-Signatur | Feste Koordinaten (x=51, y=448) | Exakte Platzierung laut medmix Layout |
| April 2026 | Tauri Sidecar | Backend als Sidecar statt resources | AppLocker in Firmen blockiert standalone .exe |
| April 2026 | Settings global | `GET /settings/global` statt `/settings/all` für alle User | Nicht-Admins sollen Einstellungen lesen aber nicht schreiben können |
| April 2026 | PDF öffnen | `shellOpen()` statt `window.open()` für Archiv-PDFs | Nativer PDF-Viewer statt Tauri-WebView-Tab |

---

## 📎 Verknüpfte Dokumente

- **Briefing:** `handover-claude-code-briefing.md` ← Hier anfangen!
- Konzept: `handover-concept.md`
- Architektur: `handover-architecture.md`
- UI/Design: `handover-ui-design.md`
- IT-Doku: `HandOver_IT-Dokumentation_medmix.docx`

---

## 🔁 Session-Log

| Session | Datum | Was wurde gemacht | Nächster Schritt |
|---|---|---|---|
| 1–5 | Feb 2026 | Grundgerüst, Auth, Workflow, PDF Signatur | UI Redesign |
| 6–8 | März 2026 | Sakura UI, GitHub Actions, Auto-Updater | Outlook Integration |
| 9–11 | März 2026 | Outlook OAuth2, Azure App Registration | E-Mail-Suche fixen |
| 12 | März 2026 | consumers Endpoint, Azure Platform-Fix | Settings Reload + Suche |
| 13 | April 2026 | Portable ZIP, IT-Doku, Claude Code Briefing | E-Mail-Suche + Settings debuggen |
| 14 | April 2026 | IMAP XOAUTH2 Fix, Settings Reload Fix, medmix Lizenz | IMAP live testen + Netzwerkdrucker |
| 15 | April 2026 | Token-Persistenz, PDF-Signatur neu | Auto-Updater debuggen, IMAP live testen |
| 16 | April 2026 | Auto-Updater gefixt, PDF-Position angepasst | PDF bestätigen, IMAP live testen |
| 17 | April 2026 | Tauri Sidecar als Prio-Task erfasst (AppLocker-Problem) | Sidecar in Claude Code umbauen |
| 18 | April 2026 | Tauri Sidecar umgebaut (v1.5.7) — externalBin, plugin-shell, capabilities, release.yml | Live-Test bei medmix: AppLocker-Fix bestätigen |
| 19 | 22. April 2026 | v1.6.4: 5 Bugfixes aus handover-fixes-v1.md — globale Settings, PDF-Icon, Drucker-Auswahl, Unterschrift mit Name/Datum, doppelte Referenz mit Suffix. Tag v1.6.4 gepusht, GitHub Actions Build gestartet. | Live-Test bei medmix |

---

*Tracker wird nach jeder Session aktualisiert · app-dev-tracker Skill*
