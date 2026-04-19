# HandOver – Entwicklungs-Tracker

**Letzte Aktualisierung:** April 2026
**Gesamtfortschritt:** 45 / 55 Aufgaben abgeschlossen (82%)

---

## 🔵 Aktueller Fokus

> **v1.5.6 morgen testen bei medmix** — Auto-Updater funktioniert (war privates Repo), PDF-Signatur-Position angepasst. Nächster Schritt: PDF-Position bestätigen, IMAP live testen, Netzwerkdrucker.

---

## ⚠️ Offene Blocker

- [ ] **PDF-Signatur Position** — Auf 355pt von oben gesetzt (~125mm), morgen live auf Lieferschein prüfen ob Position passt.
- [ ] **IMAP E-Mail-Suche live** — XOAUTH2-Fix + Token-Refresh implementiert, aber noch kein Live-Test mit echtem Postfach.

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

**Phase-Fortschritt:** 9 / 9 (100%)

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
| 2.5 | Unterschrift Canvas (Step 3) | ✅ | Touch + Maus |
| 2.6 | PDF Signatur einbetten | 🔄 | Position auf 355pt von oben (~125mm) — morgen live testen ob es passt |
| 2.7 | Archivieren + Fertig (Step 4) | ✅ | |
| 2.8 | Outlook PDF-Auswahl Step | ✅ | Dynamisch wenn Outlook aktiv |
| 2.9 | PDF Vorschau Modal | ✅ | |
| 2.10 | Unterschrift An/Aus pro PDF | ✅ | |

**Phase-Fortschritt:** 10 / 10 (100%)

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
| 3.8 | Settings-Felder persistent nach Reload | ✅ | /settings/all gibt alle Outlook-Keys + outlook_logged_in Flag zurück |
| 3.9 | E-Mail-Suche nach Referenznummer | 🔄 | XOAUTH2 double-encoding gefixt + Token-Refresh — live Test ausstehend |
| 3.10 | OAuth2 Token-Persistenz (kein Re-Login nach Neustart) | ✅ | _refresh_access_token() via Refresh-Token, automatischer Retry bei IMAP-Fehler |
| 3.11 | PDF Anhänge herunterladen + verarbeiten | ⏳ | Abhängig von 3.9 |

**Phase-Fortschritt:** 8 / 11 (73%)

---

### Phase 4 – Einstellungen & Konfiguration
| # | Aufgabe | Status | Notiz |
|---|---|---|---|
| 4.1 | Firmendaten (Name, Adresse, Logo) | ✅ | |
| 4.2 | Drucker konfigurieren | ✅ | |
| 4.3 | Datenquelle (Manual/CSV/API/Outlook) | ✅ | |
| 4.4 | Outlook Konfigurationskarte | ✅ | IMAP/M365/Exchange |
| 4.5 | Testdruck | ⏳ | Echter Netzwerkdrucker nötig |
| 4.6 | Outlook Verbindung testen | 🔄 | XOAUTH2-Bug auch im /test-Endpoint gefixt |

**Phase-Fortschritt:** 4 / 6 (67%)

---

### Phase 5 – Lizenzschlüssel System
| # | Aufgabe | Status | Notiz |
|---|---|---|---|
| 5.1 | license_service.py (HMAC-SHA256) | ✅ | ~/.handover/licenses.json |
| 5.2 | generate_license.py Script | ✅ | Interaktiv, Shoriu-intern |
| 5.3 | License Router | ✅ | /license/status, /activate, /check |
| 5.4 | Lizenz-Karte in Settings.vue | ✅ | Status, Ablaufdatum, Aktivierung |
| 5.5 | Lizenzschlüssel für medmix generieren | ✅ | XL6V7-VPYM7-C5MXC-RXFAC-7XZV5 (Complete, 365T, 15 User, läuft ab 2027-04-19) |

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
| 7.1 | Interner Pilot bei medmix | 🔄 | v1.5.3 installiert, Outlook-Test ausstehend |
| 7.2 | Auto-Updater Test | ✅ | Funktioniert — Ursache war privates Repo (assets nicht öffentlich). Repo public gestellt, v1.5.5 Fix: Backend wird vor Install gestoppt |
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
| April 2026 | Token-Refresh | _refresh_access_token() mit MSAL | MS Access Token läuft nach 1h ab — Refresh-Token für automatische Erneuerung |
| April 2026 | PDF-Signatur Position | Feste Koordinaten (x=51, y=448, 283×136pt) | Exakte Platzierung laut medmix Dokument-Layout |

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
| 14 | April 2026 | IMAP XOAUTH2 Fix, Settings Reload Fix, v1.5.3, medmix Lizenz | IMAP live testen + Netzwerkdrucker |
| 15 | April 2026 | Token-Persistenz (Refresh-Token), XOAUTH2 Fix /test-Endpoint, PDF-Signatur neu (Position + Layout + Spediteur-Daten) | Auto-Updater debuggen (v1.5.4), IMAP live testen |
| 16 | April 2026 | Auto-Updater gefixt (Repo public, Backend-Kill vor Install), PDF-Position angepasst (355pt), v1.5.5+v1.5.6 | PDF-Position morgen bestätigen, IMAP live testen |

---

*Tracker wird nach jeder Session aktualisiert · app-dev-tracker Skill*
