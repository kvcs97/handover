# HandOver Courier – Technische Architektur

> Basierend auf: handover-courier-concept.md — Erweiterungsmodul für HandOver

---

## 1. Tech Stack

Da HandOver Courier ein Modul innerhalb der bestehenden HandOver-App ist, wird der identische Stack verwendet. Kein neues Projekt, sondern Erweiterung des bestehenden Codebases.

| Schicht | Technologie | Begründung |
|---|---|---|
| Shell | Tauri 2.0 | Bereits in HandOver, Desktop-nativ, Dateisystem-Zugriff, Druckdialog |
| Frontend | Vue 3 (Composition API) | Identisch mit HandOver, Wiederverwendung bestehender Komponenten |
| Backend | FastAPI (gebundelt via PyInstaller) | Identisch, E-Mail-Engine und PDF-Handling bereits implementiert |
| Datenbank | SQLite | Identisch, lokale Datenhaltung, kein Server nötig |
| Auth | MSAL Device Flow (OAuth) | Bereits implementiert für Outlook-Zugriff |
| PDF | Bestehende HandOver PDF-Engine | Download, Anzeige, Druck, Signatur, Archivierung |

---

## 2. Projektstruktur (Erweiterung)

Neue Dateien/Ordner innerhalb der bestehenden HandOver-Struktur:

```
handover/
├── src/
│   ├── components/
│   │   ├── courier/                    # NEU: Kurier-spezifische Komponenten
│   │   │   ├── CourierDashboard.vue     # Tagesübersicht aller Sendungen
│   │   │   ├── CarrierGroup.vue        # Carrier-Gruppierung (FedEx/TNT, DHL, UPS)
│   │   │   ├── ShipmentCard.vue        # Einzelne Sendung mit Dokumentenliste
│   │   │   ├── CarrierSignature.vue    # Gesammelte Unterschrift pro Carrier
│   │   │   ├── PrintSetPreview.vue     # Druckvorschau mit Carrier-basierter Vorauswahl
│   │   │   └── CarrierConfig.vue       # Carrier-Verwaltung (Settings)
│   │   ├── shared/                     # NEU: Geteilte Komponenten
│   │   │   ├── ModeSwitch.vue          # Header-Mode-Switch LKW ↔ Kurier
│   │   │   └── ThemeProvider.vue       # Farbschema-Steuerung pro Modus
│   │   └── [bestehende HandOver-Komponenten]
│   ├── composables/
│   │   ├── useCourierEmails.ts         # NEU: E-Mail-Abruf & Parsing für Kurier
│   │   ├── useCarrierDetection.ts      # NEU: Carrier-Erkennung Logik
│   │   ├── useShipmentGrouping.ts      # NEU: Sendungs-Gruppierung
│   │   └── [bestehende Composables]
│   ├── stores/
│   │   ├── courierStore.ts             # NEU: Pinia Store für Kurier-State
│   │   └── [bestehende Stores]
│   ├── types/
│   │   ├── courier.ts                  # NEU: TypeScript-Typen für Kurier
│   │   └── [bestehende Types]
│   └── App.vue                         # ERWEITERT: Mode-Switch Integration
├── backend/
│   ├── routers/
│   │   ├── courier.py                  # NEU: Kurier-spezifische API-Routen
│   │   └── [bestehende Router]
│   ├── services/
│   │   ├── courier_email.py            # NEU: Kurier-E-Mail-Parsing
│   │   ├── carrier_detection.py        # NEU: Carrier-Erkennung
│   │   ├── shipment_grouping.py        # NEU: Sendungsgruppierung & Splitting
│   │   └── [bestehende Services]
│   └── models/
│       ├── courier.py                  # NEU: SQLAlchemy/Pydantic Models
│       └── [bestehende Models]
└── ...
```

---

## 3. Routing & Views

Kein klassisches Routing (Single-Page Desktop App). Stattdessen Mode-basierter View-Switch:

| Modus | View | Beschreibung |
|---|---|---|
| LKW-Verladung | `HandoverView` | Bestehender HandOver-Workflow (Sakura-Rosa Farbschema) |
| Kurier | `CourierDashboard` | Kurier-Workflow (Kühles Blau Farbschema) |

Der Mode-Switch in der Header-Leiste steuert:
1. Welche View gerendert wird
2. Welches CSS-Farbschema aktiv ist (CSS Custom Properties)
3. Welcher Pinia Store primär genutzt wird

---

## 4. State Management

### Pinia Store: `courierStore.ts`

```typescript
interface CourierState {
  mode: 'lkw' | 'courier'                    // Aktiver Modus
  shipments: Shipment[]                       // Alle Sendungen des Tages
  carrierGroups: CarrierGroup[]               // Gruppiert nach Carrier
  selectedDate: string                        // Stichtag (default: heute)
  fetchStatus: 'idle' | 'loading' | 'done' | 'error'
}

interface Shipment {
  id: string
  deliveryNoteNumbers: string[]               // Lieferscheinnummern (1–3)
  carrier: CarrierType
  documents: ShipmentDocument[]               // Alle Anhänge
  printSet: ShipmentDocument[]                // Automatisch vorausgewählt
  status: 'open' | 'printed' | 'signed' | 'archived'
  emailId: string                             // Referenz zur Quell-E-Mail
  emailSubject: string
}

interface ShipmentDocument {
  filename: string
  deliveryNoteNumber: string                  // Zuordnung via Dateiname
  documentType: DocumentType                  // Label, Rechnung, Lieferschein, EDEC, TO, PKL
  localPath: string                           // Lokaler Dateipfad nach Download
  shouldPrint: boolean                        // Druckvorauswahl
}

interface CarrierGroup {
  carrier: CarrierType
  shipments: Shipment[]
  signatureStatus: 'pending' | 'signed'
  signatureData?: string                      // Base64 Signatur
  signedAt?: string
}

type CarrierType = 'fedex_tnt' | 'dhl' | 'ups' | string  // string für zukünftige Carrier
type DocumentType = 'label' | 'rechnung' | 'lieferschein' | 'pkl' | 'edec' | 'to' | 'other'
```

- **Lokaler State** (ref/reactive): UI-Interaktionen wie PDF-Vorschau, Druckdialog, Unterschrift-Canvas
- **Globaler State** (Pinia `courierStore`): Sendungen, Carrier-Gruppen, Status, Modus
- **Persistierter State** (SQLite): Archivierte Sendungen, Carrier-Konfiguration, Unterschriften

---

## 5. Datenbankschema

Erweiterung der bestehenden HandOver SQLite-Datenbank um Kurier-Tabellen.

### Tabellen

#### `carriers`

Flexibel konfigurierbare Carrier-Liste mit Druckset-Regeln.

| Spalte | Typ | Constraint | Beschreibung |
|---|---|---|---|
| `id` | `INTEGER` | PK, AUTOINCREMENT | Primärschlüssel |
| `name` | `TEXT` | NOT NULL, UNIQUE | Carrier-Name (z.B. "FedEx/TNT", "DHL", "UPS") |
| `display_name` | `TEXT` | NOT NULL | Anzeigename in der UI |
| `detection_keywords` | `TEXT` | NOT NULL | JSON-Array mit Erkennungswörtern (z.B. `["fedex","tnt","federal express"]`) |
| `print_set_rules` | `TEXT` | NOT NULL | JSON-Array mit Dokumenttypen die gedruckt werden (z.B. `["label","rechnung"]`) |
| `is_active` | `INTEGER` | DEFAULT 1 | Carrier aktiv/inaktiv |
| `created_at` | `TEXT` | DEFAULT CURRENT_TIMESTAMP | Erstellungszeitpunkt |

#### `courier_shipments`

| Spalte | Typ | Constraint | Beschreibung |
|---|---|---|---|
| `id` | `INTEGER` | PK, AUTOINCREMENT | Primärschlüssel |
| `delivery_note_numbers` | `TEXT` | NOT NULL | JSON-Array der Lieferscheinnummern |
| `carrier_id` | `INTEGER` | FK → carriers.id | Zugeordneter Carrier |
| `email_id` | `TEXT` | NOT NULL | E-Mail Message-ID |
| `email_subject` | `TEXT` | | Betreff der Quell-E-Mail |
| `email_date` | `TEXT` | NOT NULL | Datum der E-Mail |
| `status` | `TEXT` | DEFAULT 'open' | open / printed / signed / archived |
| `process_date` | `TEXT` | NOT NULL | Verarbeitungstag |
| `created_at` | `TEXT` | DEFAULT CURRENT_TIMESTAMP | Erstellungszeitpunkt |

#### `courier_documents`

| Spalte | Typ | Constraint | Beschreibung |
|---|---|---|---|
| `id` | `INTEGER` | PK, AUTOINCREMENT | Primärschlüssel |
| `shipment_id` | `INTEGER` | FK → courier_shipments.id, ON DELETE CASCADE | Zugehörige Sendung |
| `filename` | `TEXT` | NOT NULL | Originaler Dateiname |
| `delivery_note_number` | `TEXT` | | Zugeordnete Lieferscheinnummer (aus Dateiname) |
| `document_type` | `TEXT` | NOT NULL | label / rechnung / lieferschein / pkl / edec / to / other |
| `local_path` | `TEXT` | | Lokaler Dateipfad nach Download |
| `should_print` | `INTEGER` | DEFAULT 0 | Druckvorauswahl (basierend auf Carrier-Regel) |
| `was_printed` | `INTEGER` | DEFAULT 0 | Wurde tatsächlich gedruckt |
| `created_at` | `TEXT` | DEFAULT CURRENT_TIMESTAMP | Erstellungszeitpunkt |

#### `courier_signatures`

| Spalte | Typ | Constraint | Beschreibung |
|---|---|---|---|
| `id` | `INTEGER` | PK, AUTOINCREMENT | Primärschlüssel |
| `carrier_id` | `INTEGER` | FK → carriers.id | Carrier-Gruppe |
| `process_date` | `TEXT` | NOT NULL | Verarbeitungstag |
| `signature_data` | `TEXT` | NOT NULL | Base64-kodierte Unterschrift |
| `signer_name` | `TEXT` | | Name des Fahrers (optional) |
| `signed_at` | `TEXT` | NOT NULL | Unterschriftszeitpunkt |
| `created_at` | `TEXT` | DEFAULT CURRENT_TIMESTAMP | Erstellungszeitpunkt |

#### `courier_archive`

| Spalte | Typ | Constraint | Beschreibung |
|---|---|---|---|
| `id` | `INTEGER` | PK, AUTOINCREMENT | Primärschlüssel |
| `shipment_id` | `INTEGER` | FK → courier_shipments.id | Zugehörige Sendung |
| `signature_id` | `INTEGER` | FK → courier_signatures.id | Zugehörige Unterschrift |
| `signed_document_path` | `TEXT` | NOT NULL | Pfad zum unterschriebenen PKL/Lieferschein |
| `archive_path` | `TEXT` | NOT NULL | Pfad im Archiv-Ordner |
| `archived_at` | `TEXT` | DEFAULT CURRENT_TIMESTAMP | Archivierungszeitpunkt |

### Relationen

```
carriers        1 ──── N  courier_shipments     (über carrier_id)
courier_shipments 1 ──── N  courier_documents   (über shipment_id)
carriers        1 ──── N  courier_signatures    (über carrier_id, pro Tag)
courier_shipments 1 ──── 1  courier_archive     (über shipment_id)
courier_signatures 1 ──── N  courier_archive    (über signature_id)
```

### Seed Data: Default Carriers

```sql
INSERT INTO carriers (name, display_name, detection_keywords, print_set_rules) VALUES
('fedex_tnt', 'FedEx / TNT', '["fedex","tnt","federal express"]', '["label","rechnung"]'),
('dhl', 'DHL', '["dhl","deutsche post"]', '["label","rechnung","lieferschein","pkl","edec","to"]'),
('ups', 'UPS', '["ups","united parcel"]', '["label","rechnung","lieferschein","pkl","edec","to"]');
```

Hinweis: FedEx Druckset = Label + Rechnung, TNT Druckset = Label + Rechnung + EDEC. Da beide unter `fedex_tnt` gruppiert sind, muss die Druckset-Logik im Backend differenzieren: Wenn das Keyword "tnt" matcht → EDEC zusätzlich drucken. Dies wird über ein `sub_carrier` Feld oder eine erweiterte `print_set_rules`-Struktur gelöst:

```json
{
  "default": ["label", "rechnung"],
  "overrides": {
    "tnt": ["label", "rechnung", "edec"]
  }
}
```

---

## 6. Authentifizierung & Rollen

Keine separate Auth für das Kurier-Modul — es nutzt die bestehende HandOver MSAL OAuth-Verbindung.

| Rolle | Beschreibung | Berechtigungen |
|---|---|---|
| Benutzer | Logistikmitarbeiter am Versand-PC | Voller Zugriff auf alle Kurier-Funktionen |

Auth-Flow (identisch mit HandOver):
1. User öffnet App → Prüfung ob OAuth-Token vorhanden und gültig
2. Falls nicht → MSAL Device Flow für Outlook-Postfach
3. Token wird für IMAP-Zugriff auf das dedizierte Kurier-Postfach verwendet
4. Postfach-Adresse wird in den Settings konfiguriert (separates Feld für Kurier-Postfach)

---

## 7. API / Backend-Endpunkte

Neue FastAPI-Routen unter `/api/courier/`:

### E-Mail & Parsing

| Methode | Route | Beschreibung |
|---|---|---|
| `GET` | `/api/courier/fetch-emails` | E-Mails vom Kurier-Postfach abrufen (Parameter: `date`, default heute) |
| `GET` | `/api/courier/parse-subject/{email_id}` | Lieferscheinnummern aus Betreff extrahieren |
| `POST` | `/api/courier/process-emails` | Batch: Alle E-Mails eines Tages abrufen, parsen, gruppieren, Dokumente zuordnen |

### Sendungen & Dokumente

| Methode | Route | Beschreibung |
|---|---|---|
| `GET` | `/api/courier/shipments` | Alle Sendungen eines Tages (Parameter: `date`) |
| `GET` | `/api/courier/shipments/{id}/documents` | Dokumente einer Sendung |
| `POST` | `/api/courier/shipments/{id}/download` | Anhänge einer Sendung herunterladen |
| `POST` | `/api/courier/shipments/{id}/print` | Druckset einer Sendung drucken |
| `POST` | `/api/courier/carrier/{carrier_id}/print-all` | Alle Drucksets eines Carriers drucken |

### Carrier-Erkennung

| Methode | Route | Beschreibung |
|---|---|---|
| `GET` | `/api/courier/carriers` | Alle konfigurierten Carrier abrufen |
| `POST` | `/api/courier/carriers` | Neuen Carrier anlegen |
| `PUT` | `/api/courier/carriers/{id}` | Carrier bearbeiten (Keywords, Druckset) |
| `DELETE` | `/api/courier/carriers/{id}` | Carrier deaktivieren |

### Unterschrift & Archivierung

| Methode | Route | Beschreibung |
|---|---|---|
| `POST` | `/api/courier/carrier/{carrier_id}/sign` | Gesammelte Unterschrift für Carrier speichern |
| `POST` | `/api/courier/carrier/{carrier_id}/archive` | Unterschrift auf alle PKL/Lieferscheine brennen & archivieren |
| `GET` | `/api/courier/archive` | Archivierte Sendungen durchsuchen (Parameter: `date_from`, `date_to`, `carrier`) |

### Kernlogik: `process-emails` Ablauf

```
1. IMAP-Connect zum Kurier-Postfach (OAuth Token)
2. E-Mails des Tages abrufen (SINCE date)
3. Pro E-Mail:
   a. Betreff parsen → Lieferscheinnummern extrahieren
   b. Carrier erkennen (Betreff + Dateinamen gegen carriers.detection_keywords matchen)
   c. Anhänge herunterladen
   d. Anhänge via Lieferscheinnummer im Dateinamen der Sendung zuordnen
   e. Dokumenttyp erkennen (Label/Rechnung/PKL/EDEC/TO via Dateiname-Pattern)
   f. Druckset automatisch setzen basierend auf Carrier print_set_rules
4. Multi-Lieferschein-Mails splitten → separate Shipment-Einträge
5. In SQLite persistieren
6. Gruppiert nach Carrier an Frontend zurückgeben
```

---

## 8. Farbschema / Theming

Mode-Switch über CSS Custom Properties im Root-Element:

```css
/* LKW-Modus (bestehend) */
:root[data-mode="lkw"] {
  --accent-primary: #F4A7BB;       /* Sakura Rosa */
  --accent-secondary: #D4829A;
  --accent-bg: #FFF5F7;
  --mode-indicator: #F4A7BB;
}

/* Kurier-Modus (neu) */
:root[data-mode="courier"] {
  --accent-primary: #5B8DB8;       /* Kühles Blau */
  --accent-secondary: #3D6E99;
  --accent-bg: #F0F5FA;
  --mode-indicator: #5B8DB8;
}
```

Der Mode-Switch in `ModeSwitch.vue` setzt `document.documentElement.dataset.mode` und aktualisiert den Pinia Store. Alle bestehenden Komponenten die bereits CSS Custom Properties nutzen, passen sich automatisch an.

---

## 9. Umgebungsvariablen

Keine neuen Umgebungsvariablen nötig. Das Kurier-Postfach wird in den App-Settings gespeichert (SQLite `settings`-Tabelle), nicht in .env.

```
# Bestehende .env (unverändert)
# Keine Erweiterung nötig — Kurier-Konfiguration läuft über Settings-UI
```

Neue Settings-Felder in der Settings-Tabelle:

| Key | Beschreibung |
|---|---|
| `courier_mailbox` | E-Mail-Adresse des Kurier-Postfachs |
| `courier_archive_path` | Lokaler Pfad für Kurier-Archiv |
| `courier_default_mode` | Welcher Modus beim App-Start aktiv ist (lkw / courier) |

---

## 10. Bekannte Risiken & Entscheidungen

| Thema | Entscheidung | Begründung / Risiko |
|---|---|---|
| FedEx/TNT Gruppierung | Eine Carrier-Gruppe mit Druckset-Override für TNT | Einfache Unterschrift, aber Druckset-Logik muss Sub-Carrier unterscheiden können |
| Carrier-Erkennung | Keyword-Matching in Betreff + Dateinamen | Einfach und robust bei 3–15 Sendungen/Tag. Risiko: unbekannter Carrier wird nicht erkannt → Fallback auf "Unbekannt" mit manuellem Assignment |
| Multi-Lieferschein Split | Zuordnung über Lieferscheinnummer im Dateinamen | Funktioniert bei klarer Benennung. Risiko: Datei ohne Nummer im Namen → manuelle Zuordnung nötig |
| Gleiches OAuth-Token | Kurier-Postfach über dasselbe MSAL-Token | Funktioniert nur wenn der User Zugriff auf beide Postfächer hat. Falls separater Account nötig → zweiter OAuth-Flow |
| Unterschrift auf PKL/Lieferschein | Bestehende Signatur-Engine wiederverwenden | Muss identifizieren welches PDF der PKL/Lieferschein ist (via `document_type`). Risiko: falsche Typerkennung |
| Carrier-Flexibilität | Konfigurierbare Carrier-Tabelle mit JSON-Regeln | Zukunftssicher für neue Carrier, aber JSON-Parsing in SQLite ist etwas unelegant — akzeptabel bei kleinem Volumen |

---

## 11. Wiederverwendbare HandOver-Komponenten

Folgende bestehende Komponenten/Services werden direkt wiederverwendet:

| Komponente/Service | Wiederverwendung im Kurier-Modul |
|---|---|
| E-Mail IMAP Engine | Abruf der Kurier-E-Mails (anderes Postfach, gleiche Logik) |
| PDF Download Service | Anhänge herunterladen und lokal speichern |
| PDF Viewer | Dokumentenvorschau in der Sendungsansicht |
| Print Service | Batch-Druck der ausgewählten Dokumente |
| Signature Canvas | Unterschrift-Eingabe (Canvas-Komponente) |
| Signature Burn-in | Unterschrift auf PDF einbrennen |
| Archive Service | Signierte PDFs im Archiv-Ordner ablegen |
| Settings Service | Erweitert um Kurier-spezifische Felder |

---

## 12. Nächste Schritte

- [ ] Architektur reviewen und freigeben
- [ ] Carrier-Seed-Daten mit Adam validieren (Keywords, Drucksets)
- [ ] UI/Design festlegen → *app-ui-design Skill*
- [ ] Entwicklung tracken → *app-dev-tracker Skill*

---

*Erstellt mit dem app-architecture Skill · 01.05.2026*
