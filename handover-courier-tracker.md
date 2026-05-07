# HandOver Courier – Entwicklungs-Tracker

**Letzte Aktualisierung:** 06.05.2026
**Gesamtfortschritt:** 44 / 48 Aufgaben abgeschlossen (92%) — v1.9.0 live, Update-Installer-Fix + kein Auto-Login
**Aktuelle Release-Version:** v1.9.0 (Update-Installer-Shutdown-Wait + Pflichtanmeldung bei App-Start)

---

## 🔵 Aktueller Fokus

> **v1.9.0: Update-Installer-Fix + Pflichtanmeldung (v1.9.0)**
> Zwei App-weite Bugfixes: (1) Update-Installation schlägt nicht mehr fehl, weil Backend-Prozess jetzt per Port-Poll auf vollständiges Herunterfahren wartet, bevor der Installer läuft. (2) Kein Auto-Login mehr — Token wird nicht in localStorage gespeichert, jeder App-Start erfordert neue Anmeldung. Nächster Schritt: Adam testet 7.1–7.3 + 7.5 (E2E, Edge Cases, Mode-Switch, PyInstaller-Build).

---

## ⚠️ Offene Blocker

*(Keine Blocker)*

---

## 📋 Aufgaben nach Phase

Status-Legende: ✅ Fertig · 🔄 In Arbeit · ⏳ Offen · ❌ Blockiert · ⏭️ Übersprungen

---

### Phase 0 – Vorbereitung & DB-Schema
| # | Aufgabe | Status | Notiz |
|---|---|---|---|
| 0.1 | SQLite-Tabellen anlegen: `courier_carriers`, `courier_shipments`, `courier_documents`, `courier_signatures`, `courier_archive` | ✅ | Tabelle umbenannt zu `courier_carriers` (Konflikt mit bestehender LKW-`carriers`-Tabelle, Option A). SQLAlchemy-Modelle in `database.py` |
| 0.2 | Seed-Daten: Default Carrier (FedEx/TNT, DHL, UPS) mit Keywords und Druckset-Regeln | ✅ | Über `_seed_courier_carriers()` in `init_db()`. TNT-Override via `print_set_rules.overrides.tnt = ["label","rechnung","edec"]` |
| 0.3 | Pydantic Models + SQLAlchemy Models für Kurier-Entitäten | ✅ | Pydantic in `backend/models/courier.py` (CarrierOut/Create/Update, ShipmentOut/Create, DocumentOut, SignatureCreate/Out, ArchiveOut, CarrierGroup, ProcessEmailsResponse). SQLAlchemy in `database.py` |
| 0.4 | Settings-Tabelle erweitern: `courier_mailbox`, `courier_archive_path`, `courier_default_mode` | ✅ | Zur SAFE_KEYS-Liste in `routers/settings.py` hinzugefügt |

**Phase-Fortschritt:** 4 / 4 (100%)

---

### Phase 1 – Mode-Switch & Theming
| # | Aufgabe | Status | Notiz |
|---|---|---|---|
| 1.1 | CSS Custom Properties: Kurier-Farbschema (Kühles Blau) als `:root[data-mode="courier"]` | ✅ | Neue Datei `src/styles/theme.css`, in main.js importiert. LKW-Default + `[data-mode="courier"]` Override + Carrier-Akzentfarben |
| 1.2 | `ModeSwitch.vue` Komponente: Toggle-Pill (LKW ↔ Kurier) | ✅ | `components/shared/ModeSwitch.vue` — segmentierter Toggle mit gleitendem Indicator (200ms ease) |
| 1.3 | `courierStore.js`: Mode in Pinia Store + `document.documentElement.dataset.mode` setzen | ✅ | `stores/courier.js` — Mode-Persistenz via localStorage, applyDefaultModeFromSettings() liest courier_default_mode beim App-Start |
| 1.4 | App-Shell anpassen: Bedingtes Rendering von HandoverView vs. CourierDashboard | ✅ | In `AppShell.vue` (statt App.vue, da das Layout dort lebt). Sidebar-Nav passt sich an Modus an. Placeholder `CourierDashboard.vue` angelegt für Phase 3 |
| 1.5 | Settings.vue erweitern: Kurier-Postfach, Archiv-Pfad, Standard-Modus Felder | ✅ | Neue Karte "Kurier-Modul" mit allen drei Feldern + Ordner-Picker |

**Phase-Fortschritt:** 5 / 5 (100%)

**Abweichung von Spec:** Mode-Switch sitzt in der **Sidebar oben** (statt im Header) — die App hat keine Header-Leiste, nur eine Sidebar. Die Position ist immer sichtbar und entspricht dem Geist der Anforderung.

---

### Phase 2 – E-Mail-Abruf & Parsing
| # | Aufgabe | Status | Notiz |
|---|---|---|---|
| 2.1 | `courier_email.py`: IMAP-Abruf vom Kurier-Postfach (bestehende E-Mail-Engine wiederverwenden) | ✅ | OAuth-Token wiederverwendet (`get_outlook_config`/`_refresh_access_token`), Mailbox aus Setting `courier_mailbox` (Fallback `outlook_email`). Cutoff-Fenster Vortag 14:30 → Stichtag 14:30 |
| 2.2 | Betreff-Parser: Lieferscheinnummern aus Betreff extrahieren (Regex, Multi-Nummer Support) | ✅ | `services/courier_parser.py::parse_subject_ls_numbers` — Patterns: `80\d{8}`, `17\d{8}`, `C_\d{2}_\d{4}`. Trenner egal (+ / , Leerzeichen). Duplikat-Eliminierung |
| 2.3 | `carrier_detection.py`: Carrier erkennen aus Betreff + Dateinamen gegen `carriers.detection_keywords` | ✅ | Wort-Grenzen-Matching (`groups` matcht NICHT als ups). Beste-Treffer-Wins. `CarrierMatch.override_key` setzt z.B. "tnt" wenn das Keyword im print_set_rules.overrides existiert |
| 2.4 | `shipment_grouping.py`: Anhänge via Lieferscheinnummer im Dateinamen zuordnen, Multi-LS-Mails splitten | ✅ | Pro LS-Nummer eine ShipmentDraft. Single-LS: ungebundene Anhänge gehören dazu. Multi-LS: ungebundene → separate "unassigned"-Sendung (ls=[]) |
| 2.5 | Dokumenttyp-Erkennung: Label/Rechnung/PKL/EDEC/TO aus Dateinamen ableiten | ✅ | `detect_document_type` mit Token-Grenzen (über `_`/`-`/`.` hinweg). Reihenfolge: edec → pkl → label (Carrier-Marker oder `label`/`awb`) → rechnung (`88\d{8}` oder `rechnung`/`invoice`/`PI`) → lieferschein (`ls_/dn_` oder Schlagwort) → to (Prefix oder `transportauftrag`) → reine LS-Nummer = lieferschein → other. 22/22 Pattern-Tests grün |
| 2.6 | Druckset automatisch setzen: Basierend auf Carrier `print_set_rules` (inkl. TNT-Override) | ✅ | `compute_print_set` setzt `should_print` pro Anhang. Override-Liste *ersetzt* die default-Liste (laut Spec) — TNT bekommt label+rechnung+edec, FedEx ohne TNT-Marker nur label+rechnung |
| 2.7 | FastAPI Router: `/api/courier/fetch-emails`, `/api/courier/process-emails` | ✅ | `routers/courier.py` mit `GET /carriers`, `POST /fetch-emails` (Preview), `POST /process-emails` (idempotent persist + grouped response inkl. `unmatched_shipments`). Anhänge lokal in `~/.handover/courier_attachments/{date}/{email_id}/`. Router unter `/api/courier` in `main.py` registriert |

**Phase-Fortschritt:** 7 / 7 (100%)

---

### Phase 3 – Kurier-Dashboard (Frontend)
| # | Aufgabe | Status | Notiz |
|---|---|---|---|
| 3.1 | `courierStore.ts`: Pinia Store mit State, Actions, Getters | ✅ | `stores/courier.js` erweitert: `carrierGroups`, `unmatchedShipments`, `carriers`, `selectedDate`, `fetchStatus/Error`, `carrierFilter`, `searchQuery`. Getters `totalShipments`, `filteredCarrierGroups`, `filteredUnmatched`. Actions: `loadCarriers`, `loadShipmentsForDate`, `processEmailsForDate`, `toggleDocumentPrint` (optimistic), `setDate/Filter/SearchQuery` |
| 3.2 | `CourierDashboard.vue`: Hauptansicht mit Toolbar (Datum, E-Mails abrufen, Filter, Suche) | ✅ | Toolbar mit `<input type="date">`, "E-Mails abrufen"-Button (mit Spinner), Carrier-Dropdown, Suche. `onMounted` ruft `loadCarriers` + `loadShipmentsForDate` |
| 3.3 | `CarrierGroup.vue`: Aufklappbare Carrier-Karte mit farbigem Rand, Header, Sendungsliste | ✅ | `border-left: 4px solid var(--carrier-color)` über `--carrier-fedex/dhl/ups`. Chevron-Animation, Sendungs-Count, offen/gedruckt/Signatur-Pills im Header. Footer mit "Alle drucken"/"Unterschrift erfassen" als disabled-Placeholder für Phase 4/5 |
| 3.4 | `ShipmentCard.vue`: Sendungszeile mit LS-Nummer (Mono), Dokumenten-Chips, Status-Badge | ✅ | Grid mit LS-Block / Doc-Chips / Status-Block. LS-Nummer in `DM Mono`. Wenn `delivery_note_numbers=[]` (Multi-LS-unassigned): roter "Keine LS-Nummer"-Hinweis |
| 3.5 | Dokumenten-Chips: Klickbar, Druckvorauswahl umschaltbar, Drucker-Icon wenn aktiv | ✅ | `DocumentChip.vue` mit Toggle-Button, Drucker-Icon nur bei `should_print=true`, Optimistic-Update über Store, ✓ wenn `was_printed`. Backend: `PATCH /api/courier/documents/{id}/print` |
| 3.6 | Status-Badges: Offen (Blau) / Gedruckt (Amber) / Unterschrieben (Grün) / Archiviert (Grau) | ✅ | `StatusBadge.vue` mit Status-Dot + farbigem Pill: open=Blau, printed=Amber, signed=Grün, archived=Grau, error=Rot |
| 3.7 | Empty State: Illustration + "E-Mails abrufen" Button | ✅ | Zentrierte Karte mit 📮-Icon, Datum-spezifischem Text, Primary-Button. Zusätzlich Filter-Empty-State (Filter zurücksetzen) |
| 3.8 | Loading State: Skeleton-Loader mit Puls-Animation | ✅ | 3 Skeleton-Gruppen mit Header + 3 Zeilen, `pulse`-Animation 1.4s |

**Phase-Fortschritt:** 8 / 8 (100%)

**Bonus (außerhalb der Phase-Tasks):**
- Backend-Endpunkt `GET /api/courier/shipments?date=…` für initialen Dashboard-Load *ohne* IMAP-Roundtrip (zeigt persistierte Sendungen direkt nach App-Start)
- Backend-Endpunkt `PATCH /api/courier/documents/{id}/print` für die Druckvorauswahl-Toggles aus Phase 3.5

**Frontend-Build:** `vite build` läuft sauber durch (700ms, 119 Module). End-to-End-Test durch Adam steht aus.

---

### Phase 4 – Druck & Sendungsdetail
| # | Aufgabe | Status | Notiz |
|---|---|---|---|
| 4.1 | `PrintSetPreview.vue`: Druckvorschau mit Carrier-basierter Vorauswahl | ✅ | Teleport-Modal mit zwei Spalten: Doc-Liste (Checkboxen über `should_print`) + PDF-Vorschau (axios-Blob → URL.createObjectURL → iframe). 👁-Button aktiviert die Vorschau pro Doc. Toggle synchronisiert via Store mit Backend |
| 4.2 | Einzelsendung drucken: Ausgewählte Dokumente einer Sendung an Print-Service senden | ✅ | `POST /api/courier/shipments/{id}/print` druckt alle Docs mit `should_print=True` und vorhandenem `local_path`. Pro-Doc-Try/Catch (skipped_documents in Response). `services/printer.py::print_document` wiederverwendet (SumatraPDF-Fallback bleibt). Drucken-Button auf jeder ShipmentCard öffnet das Modal, Modal schließt nach Erfolg + Toast |
| 4.3 | Batch-Druck pro Carrier: "Alle drucken" Button → alle Drucksets eines Carriers | ✅ | `POST /api/courier/carriers/{id}/print-all?date=…` läuft über alle Sendungen des Carriers (Status open/printed) und druckt alle Auswahl-Docs. CarrierGroup-Footer zeigt Anzahl bereiter Sendungen, deaktiviert wenn keine Auswahl. Spinner während Druck |
| 4.4 | Status-Update nach Druck: Sendung → "Gedruckt", Badge aktualisieren | ✅ | Backend setzt `was_printed=True` pro Doc und `status="printed"` (sofern vorher "open" + ≥1 Doc gedruckt). Frontend ersetzt die Sendung im State über `_replaceShipment(updated)` — Status-Badge & Doc-Chip-Häkchen updaten reaktiv |

**Phase-Fortschritt:** 4 / 4 (100%)

**Bonus:** `GET /api/courier/documents/{id}/file` als FileResponse für PDF-Vorschau im Modal (axios-Blob im Frontend, kein file:// nötig). Toast-System (success/warning) mit 3.5s Auto-Dismiss.

**Frontend-Build:** vite build OK (121 Module, 698ms).

---

### Phase 5 – Unterschrift & Archivierung
| # | Aufgabe | Status | Notiz |
|---|---|---|---|
| 5.1 | `CarrierSignature.vue`: Modal mit Carrier-Name, LS-Nummern-Liste, Signature-Canvas, Fahrer-Name | ✅ | Eigener Canvas (DPR-skaliert, Maus + Touch). Alle einzigartigen LS-Nummern der Gruppe als Pills, Fahrer-Name optional. Reset bei jedem Open |
| 5.2 | Backend: Unterschrift auf PKL/Lieferschein einbrennen (pro Sendung in der Carrier-Gruppe) | ✅ | `services/pdf_sign.embed_signature_in_pdf` wiederverwendet. Ziel-Doc-Auswahl: PKL > Lieferschein > erstes Doc mit lokalem Pfad. Pro-Sendung Try/Catch (errors-Liste in Response) |
| 5.3 | Backend: Signierte Dokumente im Kurier-Archiv-Ordner ablegen | ✅ | Pfad aus Setting `courier_archive_path` (Fallback `~/.handover/courier_archive`), Struktur `<archive>/<process_date>/<carrier_name>/signed_<ls>_<doc_id>.pdf` |
| 5.4 | SQLite: `courier_signatures` und `courier_archive` Einträge schreiben | ✅ | Eine `CourierSignature` pro (carrier_id, process_date) — 409 bei Doppel-Sign. Pro Sendung ein `CourierArchive`-Eintrag. Wenn alle Burn-Ins fehlschlagen → Rollback der Signatur-Row |
| 5.5 | Status-Update: Alle Sendungen der Carrier-Gruppe → "Archiviert" | ✅ | `shipment.status = "archived"` direkt im Sign-Endpoint. `_build_grouped_response` liest aus `CourierSignature` und setzt `signature_status`/`signed_at` für die Carrier-Gruppe |
| 5.6 | Toast-Notification: "X Sendungen archiviert ✓" | ✅ | Bestehendes Toast-System aus Phase 4 wiederverwendet (`onSigned` im Dashboard). Success-Variante grün, Warning-Variante bei Fehlern |

**Phase-Fortschritt:** 6 / 6 (100%)

---

### Phase 6 – Carrier-Konfiguration & Settings
| # | Aufgabe | Status | Notiz |
|---|---|---|---|
| 6.1 | `CarrierConfig.vue`: Carrier-Liste in Settings mit Edit/Delete, "Neuer Carrier" Button | ✅ | In `pages/Settings.vue` zwischen Kurier-Modul-Karte und Passwort-Karte (nur Admin). Liste mit Status-Dot, Keywords-Vorschau, Druckset-Vorschau (inkl. Overrides). Modal-Form mit Doc-Toggle-Pills, dynamische Override-Zeilen |
| 6.2 | CRUD-Endpunkte: `/api/courier/carriers` (GET, POST, PUT, DELETE) | ✅ | `GET /carriers?include_inactive=…` (User), `POST /carriers` (Admin), `PUT /carriers/{id}` (Admin), `DELETE /carriers/{id}?hard=…` (Admin, Soft-Delete = is_active=false; Hard nur ohne FK-Refs) |
| 6.3 | Validierung: Keywords und Druckset-Regeln beim Speichern prüfen | ✅ | `_validate_carrier_input`: Name nicht leer, ≥1 Keyword, Default-Druckset ≥1 Typ, alle Doc-Types in {label,rechnung,lieferschein,pkl,edec,to,other}, Override-Keys müssen in Keyword-Liste sein. Frontend prüft zusätzlich vor dem Submit (kein Round-Trip für Trivialfehler) |

**Phase-Fortschritt:** 3 / 3 (100%)

---

### Phase 7 – Testing & Polish
| # | Aufgabe | Status | Notiz |
|---|---|---|---|
| 7.1 | E2E Test: Kompletter Workflow — E-Mails abrufen → Drucken → Unterschreiben → Archivieren | ⏳ | Adam-Test mit echtem Postfach |
| 7.2 | Edge Cases: Mail ohne Carrier-Match, Datei ohne LS-Nummer, leerer Tag, 1 Mail mit 3 LS | ⏳ | Adam-Test (Unmatched-Sektion + "Keine LS-Nummer"-Hinweis sind im UI vorhanden) |
| 7.3 | Mode-Switch testen: Wechsel zwischen LKW und Kurier, State bleibt erhalten | ⏳ | Adam-Test |
| 7.4 | Animationen & Übergänge feintunen (Crossfade, Aufklapp-Animation, Toast) | ✅ | Modal-Fade (180ms), Toast-Slide+Fade (250ms), Skeleton-Pulse (1.4s), CarrierGroup-Collapse (250ms), TransitionGroup für Carrier-Liste mit move-Transition (300ms), Doc-Chip-Hover (150ms), **Mode-Crossfade**: `applyMode(mode, animate=true)` triggert beim Toggle eine `body.mode-switching`-Klasse mit 220ms keyframe-Fade (initial-Load animiert nicht — nur User-Toggles) |
| 7.5 | PyInstaller Build mit neuem Kurier-Modul testen | ⏳ | Adam baut |
| 7.6 | UI: Unterschrifts-Canvas verkleinern + horizontal zentrieren | ✅ | `.canvas-frame`: `max-width: 500px; margin: 0 auto`, `.sig-canvas`: `height: 220px → 150px`. Hint-Text `text-align: center`. |
| 7.7 | UI: Signatur-Zeile unter dem Canvas — eingeloggter Mitarbeiter-Name + Datum/Uhrzeit | ✅ | `CarrierSignature.vue`: `useAuthStore` importiert, `sigTimestamp` ref (gesetzt in `reset()`), `.sig-line` Div unter `.canvas-frame` — "Unterzeichnet: [userName] · DD.MM.YYYY HH:MM". |
| 7.8 | Logik: Rechnungs-Dokumente der richtigen Sendung zuordnen statt neue unassigned-Sendung | ✅ | `shipment_grouping.py`: Multi-LS unassigned-Anhänge werden per Round-Robin auf bestehende Sendungen verteilt statt einer separaten "unassigned"-Sendung. Unassigned-ShipmentDraft entsteht jetzt nur noch bei Mails ohne jede LS-Nummer im Betreff. |
| 7.9 | Logik: Dokument-Priorität für Unterschrift — LS immer vor Rechnung | ✅ | `routers/courier.py` `_select_burn_target`: PKL > Lieferschein > Rechnung > docs[0]. Rechnung wird nie gewählt, solange ein LS vorhanden ist. |
| 7.10 | UI: Tablet/Touch-Optimierung Kurier-Modus (v1.7.9) | ✅ | `AppShell`: Sidebar 220→240px, Nav-Items `min-height: 44px`. `ModeSwitch`: 36→44px. `CourierDashboard`: Padding 32/48→24/32, Toolbar-Controls `min-height: 44px`, Font 13→14px. `CarrierGroup`: Footer-Buttons `min-height: 44px`, Pills größer. `ShipmentCard`: Print-Button 32×30→44×44px. `DocumentChip`: Padding 4/10→7/13, Font 11→12px. `StatusBadge`: Font 11→12px. |
| 7.11 | UI: Tablet/Touch-Optimierung LKW-Seiten + globale Lesbarkeit (v1.8.0) | ✅ | Alle Pages: Padding 40/44→24/32px. `Dashboard`: Btn 44px, Tabelle th 11→12px / td 13→14px, Chips 12px, Action-Btn 56px. `Handover`: Vorschau/Sig-Toggle 44px, Btn-Next/Back 48px, Sig-Canvas max-width 500px/160px zentriert (konsistent mit Kurier). `Archive`: Suche+Filter 44px, Tabelle 14px, Paginierung 30→44px, PDF-Btn + Actions 44px. `CourierArchive`: Felder 44px, Font 13→14px, Archiv-Zeilen Padding +2px, Btn-Icon 44×44px. |

**Phase-Fortschritt:** 7 / 11 (64%) — manuelle Tests + Tablet-UI-Optimierung abgeschlossen

---

## 🧠 Entscheidungen & Notizen

| Datum | Thema | Entscheidung | Grund |
|---|---|---|---|
| 01.05.2026 | FedEx/TNT Gruppierung | Eine Carrier-Gruppe mit Druckset-Override für TNT (EDEC) | Fahrer unterschreibt einmal für beide |
| 01.05.2026 | Mode-Switch Platzierung | Header-Leiste als Toggle-Pill | Immer sichtbar, kein Sidebar-Overhead |
| 01.05.2026 | Carrier-Flexibilität | Konfigurierbare Carrier-Tabelle mit JSON-Regeln | Zukunftssicher für neue Carrier |
| 01.05.2026 | Farbschema | Kühles Blau (#5B8DB8) für Kurier-Modus | Klarer Kontrast zu Sakura-Rosa |
| 01.05.2026 | Carrier-Farbe FedEx | Lila (#4D148C) statt Orange | Entspricht der echten FedEx-Markenfarbe |
| 01.05.2026 | Tabellenname Kurier-Carriers | `courier_carriers` (statt `carriers`) | Bestehende `carriers`-Tabelle ist für LKW-Spediteure reserviert. Sauberer Namespace, keine Migration alter Daten |
| 01.05.2026 | Mode-Switch Position | Sidebar (oben unter Brand) statt Header | App hat keine Header-Leiste — nur Sidebar. Immer sichtbar, kein Layout-Bruch nötig |
| 02.05.2026 | LS-Nummer-Format | Drei feste Patterns: `80\d{8}`, `17\d{8}`, `C_\d{2}_\d{4}` | Adam-Aussage. Strikte Patterns reduzieren Fehlerkennungen gegenüber generischer "6+ Ziffern"-Regex |
| 02.05.2026 | TNT-Override-Semantik | Override-Liste *ersetzt* Default-Liste (kein Merge) | Steht so im print_set_rules-Konzept (`overrides.tnt = [label,rechnung,edec]` enthält bereits alles). Vermeidet Konflikte bei künftigen Override-Regeln, die Default-Items entfernen wollen |
| 02.05.2026 | Cutoff-Fenster | Vortag 14:30 — Stichtag 14:30 (lokale Zeit) | Adam-Vorgabe. IMAP `SINCE` arbeitet nur tag-genau → grobes Vor-Fetch + exakter Cutoff im Code |
| 02.05.2026 | Kurier-Postfach | Adresse aus Setting `courier_mailbox`, gleicher OAuth-Token wie Hauptkonto (Shared-Mailbox-Annahme) | Spec sagt "separates Postfach, gleicher Token". Bei nicht-Shared-Mailbox-Setup muss später ein zweiter OAuth-Flow nachgeschoben werden — ist als Risk dokumentiert |
| 02.05.2026 | Unmatched Sendungen | Kommen als `unmatched_shipments`-Liste (separat zu `carrier_groups`) im `/process-emails`-Response | UI bekommt klares Signal für manuelle Carrier-Zuweisung statt einer pseudo-Carrier-Gruppe |
| 02.05.2026 | Anhang-Speicherort | `~/.handover/courier_attachments/{process_date}/{email_id}/{filename}` | Lokale Files für späteren Druck/Burn-In; idempotent (Re-Run überschreibt nicht) |
| 03.05.2026 | Pfad-Trennung Archiv | `handover_*` (App-generiert) IMMER in `~/.handover/archive`, user-konfigurierter `archive_path` und `courier_archive_path` NUR für `signed_*`-PDFs | Adam-Wunsch: der Arbeits-Ordner soll sauber bleiben — nur signierte Dokumente sind für die Arbeit relevant |
| 03.05.2026 | Signed-Filename-Schema | `signed_<originalname>` ohne Referenz/LS/doc_id-Prefix | Adam-Wunsch: kürzer, lesbarer; Kollisionsrisiko gering, weil pro Sendung eindeutig |
| 03.05.2026 | Standard-Modus-Logik | Settings-Wert (`courier_default_mode`) gewinnt IMMER beim App-Start über localStorage | Vorher hatte localStorage Vorrang nach erstem Toggle, sodass der Default nie griff. Jetzt: localStorage ist nur Session-Persistenz |
| 04.05.2026 | IMAP-Fetch-Strategie | Zwei-Phasen-Fetch: erst nur DATE/SUBJECT-Header (`BODY.PEEK[HEADER.FIELDS]`), dann nur passende Mails komplett (`RFC822`) | Vermeidet axios-Timeout/Network-Error bei vollen Postfächern. Vorher wurden alle Mails seit gestern komplett geladen, nur um 99% nach Cutoff zu verwerfen |
| 04.05.2026 | Pro-Mail-Transaktionen | Jede Mail im `process-emails`-Loop hat eigene DB-Transaktion mit `try/except + commit/rollback` | Eine kaputte Mail rollt nicht mehr alle bisherigen zurück; Failed-List wandert ins Logfile |
| 04.05.2026 | File-Logger | `~/.handover/handover.log` (RotatingFileHandler, 2MB×3) für `courier.email`, `courier.router`, `uvicorn.error` | Stacktraces im Tauri-Sidecar-Modus sonst unsichtbar; Adam kann Logfile bei Bugs senden |
| 04.05.2026 | CI latest.json-Upload | tauri-action mit `continue-on-error: true` + nachgeschalteter Fallback-Step generiert `latest.json` aus `*.sig`-Dateien und uploaded sie via `softprops/action-gh-release@v2` | tauri-action 0.5.x crasht manchmal beim 5. Asset-Upload (Race-Condition). v1.7.3-Release hatte deshalb keine `latest.json` → Auto-Updater blieb stumm |
| 06.05.2026 | Touch-Target-Minimum | Universell 44px `min-height` auf allen interaktiven Elementen (kein Media-Query-Ansatz) | Apple/Google HIG: 44pt Minimum. Universelle Änderung wirkt auf Tablet und Desktop gleichwertig — Desktop fühlt sich spaciger an, kein Layoutbruch. Kein responsives System nötig. |
| 06.05.2026 | Tablet-Padding | Alle Pages von `40px 44px` → `24px 32px` reduziert | 11"-Tablet (~1024px nach Sidebar) hatte mit 88px horizontalem Gesamt-Padding zu wenig Nutzfläche. `24/32px` ist ausreichend für den Weißraum-Look ohne zu viel Platz zu verschwenden. |
| 06.05.2026 | Sig-Canvas LKW-Modus | LKW-Handover-Canvas (in `Handover.vue`) auf `max-width: 500px / height: 160px` vereinheitlicht | Konsistenz mit Kurier-Modus (`CarrierSignature.vue`). Beide Unterschriftsfelder sehen jetzt gleich aus — ein Canvas-Standard für die ganze App. |
| 06.05.2026 | Update-Installer-Wait | `install_update` in `main.rs` wartet nach `child.kill()` via `wait_for_backend_shutdown(8)` (Port-Poll) bis Port 8000 geschlossen ist, bevor `download_and_install` läuft | Race-Condition: kill() schickt nur das Signal, der Prozess braucht Zeit zum Beenden. Installer schlug fehl, weil Backend noch lief. |
| 06.05.2026 | Kein Auto-Login | `token = ref(null)` in `auth.js` — Token wird nicht mehr in localStorage geschrieben/gelesen; nur `handover_user`/`role`/`uid` bleiben im localStorage | Adam-Wunsch: bei jedem App-Start neu einloggen. Token existiert nur in-memory für die aktuelle Session. |

---

## 📎 Verknüpfte Dokumente

- Konzept: `handover-courier-concept.md`
- Architektur: `handover-courier-architecture.md`
- UI/Design: `handover-courier-ui-design.md`

---

## 🔁 Session-Log

| Session | Datum | Was wurde gemacht | Nächster Schritt |
|---|---|---|---|
| 1 | 01.05.2026 | Konzept, Architektur, UI-Design und Tracker erstellt. Alle offenen Fragen geklärt. | Phase 0 starten: DB-Schema & Seed-Daten |
| 2 | 01.05.2026 | Phase 0 komplett: 5 SQLAlchemy-Tabellen in `database.py` (`courier_carriers`/`_shipments`/`_documents`/`_signatures`/`_archive`), Seed-Funktion `_seed_courier_carriers()` mit FedEx/TNT-Override für EDEC, Pydantic-Schemas in `backend/models/courier.py`, Settings-SAFE_KEYS um `courier_mailbox`/`courier_archive_path`/`courier_default_mode` erweitert. DB-Init + Seed lokal verifiziert. | Phase 1 starten: CSS-Variablen, ModeSwitch.vue, ThemeProvider.vue, App.vue Erweiterung, Settings-UI |
| 3 | 01.05.2026 | Phase 1 komplett: `src/styles/theme.css` mit data-mode-Switch (Sakura-Rosa ↔ Kühles Blau) + Carrier-Akzentfarben, `stores/courier.js` mit Mode-Persistenz (localStorage) und `applyDefaultModeFromSettings()`, `components/shared/ModeSwitch.vue` als Segment-Toggle mit gleitendem Indicator, `AppShell.vue` mit ModeSwitch in Sidebar + bedingtes Rendering pro Modus, `components/courier/CourierDashboard.vue` als Phase-3-Placeholder, `pages/Settings.vue` um Kurier-Karte erweitert. Frontend baut sauber (vite build OK). | Phase 2 starten: IMAP-Postfach-Abruf, Betreff-Parser, Carrier-Erkennung, Sendungs-Gruppierung |
| 4 | 02.05.2026 | Phase 2 komplett: 4 neue Backend-Module (`services/courier_parser.py`, `services/carrier_detection.py`, `services/shipment_grouping.py`, `services/courier_email.py`) + Router `routers/courier.py` mit `/carriers`, `/fetch-emails`, `/process-emails`. LS-Patterns nach Adam (`80\d{8}`/`17\d{8}`/`C_\d{2}_\d{4}`), Doc-Type-Patterns mit Token-Grenzen (über `_`/`-`/`.` hinweg, kein Fehl-Match auf `groups`/`support`), TNT-Override greift als Replace, Cutoff-Fenster Vortag-14:30 → Stichtag-14:30, idempotente Persistierung, Anhänge lokal unter `~/.handover/courier_attachments/`. 22/22 Doc-Type-Tests grün, alle Module compilieren. ProcessEmailsResponse um `unmatched_shipments` erweitert. | Phase 3: Frontend-Pinia-Store (`courierStore.ts`), CourierDashboard mit Toolbar/Filter/Suche, CarrierGroup-Karten, ShipmentCard mit Doc-Chips & Status-Badges, Empty/Loading-States |
| 5 | 02.05.2026 | Phase 3 komplett (8/8): `stores/courier.js` um Dashboard-State + 7 Actions/3 Getters erweitert (Filter, Suche, Optimistic-Updates), 5 neue Vue-Komponenten (`StatusBadge`, `DocumentChip`, `ShipmentCard`, `CarrierGroup`, `CourierDashboard`-Rewrite). Toolbar mit Datum/Refresh/Carrier-Filter/Suche, Carrier-Gruppen mit farbigem Rand (FedEx Lila / DHL Gelb / UPS Braun) und Aufklapp-Animation, Doc-Chips mit Drucker-Icon und PATCH-Sync, Status-Badges (Offen/Gedruckt/Unterschrieben/Archiviert/Fehler), Skeleton-Loader, Empty-State, separate "Unzugeordnete Sendungen"-Sektion mit roter gestrichelter Border. Backend-Bonus: `GET /api/courier/shipments?date=…` (Dashboard-Load ohne IMAP) + `PATCH /api/courier/documents/{id}/print` (Druckvorauswahl). vite build OK (119 Module, 700ms). | Adam testet End-to-End, danach gezielte Bug-Fixes vor Phase 4 |
| 6 | 02.05.2026 | Phase 4 komplett (4/4): 3 neue Backend-Endpoints (`POST /shipments/{id}/print`, `POST /carriers/{id}/print-all`, `GET /documents/{id}/file`) + Druck-Helper `_print_one_shipment` mit Pro-Doc-Try/Catch. Store-Actions `printShipment`/`printAllForCarrier`/`fetchDocumentBlobUrl` mit `printingShipments`/`printingCarriers`-Sets für UI-Spinner, `_replaceShipment` für reaktiven Status-Update. Neue Komponente `PrintSetPreview.vue` (Teleport-Modal, 2-Spalten-Layout, axios-Blob-PDF-Vorschau im iframe). ShipmentCard bekommt 🖨-Aktions-Button, CarrierGroup "Alle drucken" mit Spinner und Bereit-Counter, Dashboard mit Toast-System (success/warning, 3.5s Auto-Dismiss). vite build OK (121 Module, 698ms). | Adam testet End-to-End (LKW-Drucker zum Testen!), dann gezielte Bug-Fixes oder direkt Phase 5 |
| 7 | 03.05.2026 | Phasen 5+6+7.4 komplett: **Phase 5 (6/6)** — Backend `POST /carriers/{id}/sign` mit Burn-In via `pdf_sign.embed_signature_in_pdf`, Ziel-Doc-Auswahl PKL>LS>erstes, Archive-Pfad aus Setting (Fallback `~/.handover/courier_archive/{date}/{carrier}/`), `CourierSignature` (idempotent über carrier+date, 409 bei Doppel-Sign) + `CourierArchive` pro Sendung, Status→archived, `_build_grouped_response` liest Signatur-Status aus DB. Frontend: `CarrierSignature.vue` (DPR-skalierter Canvas, Maus+Touch, alle LS-Pills, Fahrer-Name optional), Store-Action `signCarrier` mit `signingCarriers`-Set, CarrierGroup-Footer-Button verdrahtet (✓ Unterschrieben wenn signed), Dashboard-Wiring + Toast. **Phase 6 (3/3)** — Backend POST/PUT/DELETE/`carriers` (Admin-only, Soft-Delete via is_active=false, Hard nur ohne FK-Refs), `_validate_carrier_input` für Name/Keywords/Doc-Types/Override-Keys. Frontend `CarrierConfig.vue` in Settings (Admin-only) mit Liste + Modal-Form (Doc-Toggle-Pills, dynamische Overrides). **Phase 7.4** — TransitionGroup auf Carrier-Liste mit move-Transition. vite build OK (125 Module, 691ms). | Adam testet End-to-End: 7.1 (Workflow), 7.2 (Edge Cases), 7.3 (Mode-Switch), 7.5 (PyInstaller-Build) |
| 8 | 03.05.2026 | **Initial-Release v1.7.0** gepusht (commit ca2fc48, Tag v1.7.0). 36 Files, +6702/−314 Zeilen — kompletter Kurier-Modul-Snapshot. CI lief grün, Setup-Files heißen aber `HandOver_1.6.9_*` weil ich vor dem Tag die Versionen in `tauri.conf.json`/`package.json`/`Cargo.toml` nicht angehoben hatte → `latest.json` meldete weiterhin Version 1.6.9, Auto-Updater sprang nicht an. **Hotfix v1.7.1** (commit e98166a): nur Versions-Bump auf 1.7.1 in den 4 Build-Configs. CI grün, Updater zog Update sauber. | Adam testet im echten Postfach |
| 9 | 03.05.2026 | **Bugfix-Release v1.7.2** (commit 99bf5ba, Tag v1.7.2): a) Eigene Kurier-Archiv-Seite (`pages/CourierArchive.vue` mit Datum-/Carrier-Filter, Suche, PDF-Vorschau in neuem Tab via Blob-URL) ersetzt im Kurier-Modus die LKW-Archive-Page; Backend `GET /api/courier/archive` mit Joined-Carrier/Sendung/Signatur und `GET /api/courier/archive/{id}/file`. b) Pfad-Trennung: `pdf_gen.generate_pdf` schreibt `handover_*` ab jetzt IMMER nach `~/.handover/archive`, der user-konfigurierte Pfad ist nur noch für `signed_*`. c) Filename-Vereinfachung: `signed_<originalname>` statt mit Referenz/LS/doc_id-Prefix bei LKW (`outlook_router`) und Kurier (`_archive_signed_pdf`). d) Bessere Fehler-Texte beim IMAP-Abruf (Connection/Token/Login-spezifisch, 502 statt 500). | Adam testet, meldet weitere Bugs |
| 10 | 03.05.2026 | **Bugfix-Release v1.7.3** (commit 094593e, Tag v1.7.3): Adam meldet "Network Error" beim Mail-Abruf an Tagen mit Mails (leere Tage funktionieren). Root-Cause-Analyse: alter Code lädt ALLE Mails seit gestern komplett (RFC822 inkl. Anhänge), filtert erst danach im Code → axios-Timeout bei vollen Postfächern. **IMAP-Fetch-Refactoring** in `services/courier_email.py`: zwei-Phasen-Fetch — erst nur `BODY.PEEK[HEADER.FIELDS (DATE SUBJECT)]` pro Mail, nur passende Mails bekommen den vollen Body. **Pro-Mail-Transactions** im Loop (eine kaputte Mail rollt nicht alles zurück, Failed-List ins Logfile). **Frontend-Timeout** 60s→180s. **File-Logger** (`~/.handover/handover.log`, RotatingFileHandler 2MB×3) für `courier.email`/`courier.router`/`uvicorn.error`. **Default-Modus-Fix**: localStorage-Check entfernt, Settings-Wert gewinnt IMMER beim App-Start. CI-Build der v1.7.3 ist erfolgreich, aber `tauri-action` failt beim Upload des `latest.json` als 5. Asset (Race-Condition-Bug in tauri-action 0.5.x) → Auto-Updater bekommt kein Update-Signal. | Workflow-Fix nötig |
| 11 | 04.05.2026 | **CI-Fix v1.7.4** (commit a1c927f, Tag v1.7.4): Workflow `release.yml` erweitert — `tauri-action` läuft mit `continue-on-error: true`, danach zwei neue Steps: `Generate latest.json (fallback)` baut die Datei aus den vorhandenen `*.sig`-Files (msi + setup.exe) als UTF-8 ohne BOM zusammen, `Upload latest.json` schiebt sie idempotent via `softprops/action-gh-release@v2` zum Tag-Release nach. Plus: `unused_mut`-Warnings in `src-tauri/src/main.rs` weg. Damit greift der Auto-Updater jetzt zuverlässig, auch wenn tauri-action beim primären Upload stolpert. | Adam testet v1.7.4 (IMAP-Fix, Default-Modus, Archiv) und meldet UI-Polish-Wünsche |
| 12 | 05.05.2026 | **CI-Workflow-Fix v1.7.5** + **Pydantic-Fix v1.7.6**: v1.7.5 — Fallback-Step `if: always()` → `if: steps.tauri.outcome != 'success'`, `shell: powershell` → `shell: pwsh` (PS 5.1 las UTF-8 mit Windows-1252-Codepage, Byte 0x94 des em-Dash wurde als String-Terminator `"` interpretiert). v1.7.6 — `ShipmentOut` ValidationError bei `delivery_note_numbers=[]`: Validator aus `ShipmentBase` in `ShipmentCreate` verschoben, damit unmatched Sendungen (Multi-LS-Mails) geladen werden können. Adam testet v1.7.6 erfolgreich: Kurier-Mails gefunden + Unterschrift funktioniert. Neue Polish-Tasks 7.6–7.9 aus dem Echttest aufgenommen. | Tasks 7.6–7.9 umsetzen (Canvas, Signatur-Zeile, Multi-LS-Gruppierung, Dok-Priorität) |
| 13 | 06.05.2026 | **Tasks 7.6–7.9**: 7.6 Canvas-Verkleinerung (`max-width: 500px`, `height: 150px`, zentriert). 7.7 Signatur-Zeile unter Canvas ("Unterzeichnet: [userName] · DD.MM.YYYY HH:MM", `useAuthStore`, `sigTimestamp` in `reset()`). 7.8 Rechnungs-Zuordnung bei Multi-LS: Round-Robin statt separater unassigned-Sendung (`shipment_grouping.py`). 7.9 Burn-Target-Priorität: PKL > LS > Rechnung > docs[0] (`_select_burn_target` in `courier.py`). vite build OK (127 Module). Push v1.7.8. | Tablet-UI optimieren |
| 14 | 06.05.2026 | **Task 7.10 — Tablet/Touch Kurier-Modus (v1.7.9)**: `AppShell` Sidebar 240px, Nav-Items 44px. `ModeSwitch` 44px. `CourierDashboard` Padding 24/32, Toolbar-Controls 44px. `CarrierGroup` Footer-Buttons 44px + font 14px. `ShipmentCard` Print-Button 44×44px. `DocumentChip` 32px, font 12px. `StatusBadge` font 12px. Alle Touch-Targets auf 44px-Minimum gebracht. | LKW-Seiten optimieren |
| 15 | 06.05.2026 | **Task 7.11 — Tablet/Touch LKW + Lesbarkeit (v1.8.0)**: Alle Pages Padding 24/32px. `Dashboard` Btn 44px, Tabelle 14px, Chips 12px. `Handover` Buttons 44–48px, Sig-Canvas max-width 500px/160px zentriert. `Archive` Suche+Filter 44px, Tabelle 14px, Paginierung 44px. `CourierArchive` Felder 44px, Btn-Icon 44×44px, Meta-Zeile 12.5px. Globale Lesbarkeit: min. 12px Schriftgröße überall. vite build OK. Push v1.8.0. | Adam testet 7.1–7.3 + 7.5 |
| 16 | 06.05.2026 | **Bugfix v1.9.0 — Update-Installer + kein Auto-Login**: (1) `main.rs`: neue `wait_for_backend_shutdown(8)`-Hilfsfunktion pollt Port 8000 bis er geschlossen ist; `install_update` ruft sie nach `child.kill()` auf (`tokio::task::spawn_blocking`) — Installer startet erst wenn Backend wirklich weg ist. (2) `auth.js`: `token = ref(null)` auf Startup, kein `localStorage.setItem('handover_token')` mehr beim Login — Token existiert nur in-memory. `logout()` bereinigt weiterhin den alten Key. vite build OK. Push v1.9.0. | Adam testet Update-Flow + Login-Verhalten |

---

*Tracker wird nach jeder Session aktualisiert · app-dev-tracker Skill*
