# HandOver Courier – UI/UX Design

> Basierend auf: handover-courier-concept.md + handover-courier-architecture.md
> Erweiterung des bestehenden Shoriu Design Systems für den Kurier-Modus

---

## 1. Design Persona

> "HandOver Courier feels **klar**, **schnell**, and **vertraut**. Es ist das Werkzeug, das den Versand-Mitarbeiter durch den täglichen Kurier-Workflow führt wie ein gut sortierter Arbeitstisch — alles liegt griffbereit, nichts lenkt ab, und man sieht auf einen Blick was erledigt ist und was noch offen."

### Kontext

- **Nutzer:** Logistikmitarbeiter am Versand-PC, arbeiten unter Zeitdruck (Deadline ~14:30, Fahrer kommt danach)
- **Umgebung:** Büro/Versandhalle, oft mit Handschuhen oder hektischem Umfeld → große Klickflächen, klare Hierarchie
- **Emotion:** Kontrolle & Überblick. Der User soll zu jeder Zeit wissen: was ist offen, was ist gedruckt, wer hat noch nicht unterschrieben

### Inspiration & Referenzen

- **HandOver (LKW-Modus)** — Identische Grundstruktur und Interaktionsmuster, damit kein Umlernen nötig ist
- **Linear** — Klare Status-Badges, kompakte Listen, schnelle Batch-Aktionen
- **Notion Kanban** — Gruppierte Karten mit visuellem Status-Feedback

---

## 2. Design System

### 2.1 Farbpalette

Das bestehende Shoriu Design System wird um einen Kurier-Modus erweitert. Beide Modi teilen sich die neutralen Farben; nur die Akzentfarben wechseln.

#### Geteilte Farben (beide Modi)

| Rolle | Variable | Hex | Usage |
|---|---|---|---|
| Background | `--color-bg` | `#FAFAFA` | Seitenhintergrund |
| Surface | `--color-surface` | `#FFFFFF` | Karten, Panels, Inputs |
| Border | `--color-border` | `#E5E5E5` | Trennlinien, Input-Rahmen |
| Text Primary | `--color-text` | `#1A1A1A` | Haupttext |
| Text Muted | `--color-text-muted` | `#737373` | Labels, Platzhalter, Zeitstempel |
| Success | `--color-success` | `#22C55E` | Archiviert, abgeschlossen |
| Warning | `--color-warning` | `#F59E0B` | Gedruckt aber noch nicht unterschrieben |
| Danger | `--color-danger` | `#EF4444` | Fehler, fehlende Zuordnung |

#### LKW-Modus (bestehend, Referenz)

| Rolle | Variable | Hex | Usage |
|---|---|---|---|
| Primary | `--color-primary` | `#F4A7BB` | Sakura Rosa — CTAs, aktive States |
| Primary Dark | `--color-primary-dark` | `#D4829A` | Hover States |
| Secondary | `--color-secondary` | `#E8D5DC` | Unterstützende Akzente |
| Accent BG | `--color-accent-bg` | `#FFF5F7` | Leichte Hintergrundtönung |

#### Kurier-Modus (neu)

| Rolle | Variable | Hex | Usage |
|---|---|---|---|
| Primary | `--color-primary` | `#5B8DB8` | Kühles Blau — CTAs, aktive States, Mode-Indikator |
| Primary Dark | `--color-primary-dark` | `#3D6E99` | Hover States |
| Secondary | `--color-secondary` | `#A8C8E0` | Unterstützende Akzente, Carrier-Header |
| Accent BG | `--color-accent-bg` | `#F0F5FA` | Leichte Hintergrundtönung |

#### Carrier-spezifische Farben (Akzente für Gruppierung)

| Carrier | Farbe | Hex | Verwendung |
|---|---|---|---|
| FedEx/TNT | Lila | `#4D148C` | Carrier-Badge, Gruppen-Rand |
| DHL | Gelb | `#FFCC00` | Carrier-Badge, Gruppen-Rand |
| UPS | Braun | `#6B3F23` | Carrier-Badge, Gruppen-Rand |
| Unbekannt | Grau | `#9CA3AF` | Fallback für nicht erkannte Carrier |

Diese Carrier-Farben werden nur als schmale Akzente eingesetzt (linker Rand der Gruppen-Karte, Badge-Hintergrund), nicht als Flächen — das Gesamtbild bleibt im kühlen Blau.

### 2.2 Typografie

Bestehende Shoriu-Typografie wird unverändert übernommen:

| Rolle | Font | Size | Weight | Usage |
|---|---|---|---|---|
| Heading 1 | Cormorant Garamond | 1.75rem | 600 | Seitentitel ("Kurier — 01.05.2026") |
| Heading 2 | Cormorant Garamond | 1.35rem | 600 | Carrier-Gruppenüberschriften |
| Heading 3 | Noto Serif JP | 1.1rem | 500 | Sendungs-Karten-Titel |
| Body | Noto Serif JP | 0.95rem | 400 | Haupttext, Dokumentennamen |
| Small | Noto Serif JP | 0.8rem | 400 | Labels, Zeitstempel, Meta |
| Mono | DM Mono | 0.85rem | 400 | Lieferscheinnummern, E-Mail-IDs |

### 2.3 Spacing & Layout

```
Base unit: 4px (identisch mit HandOver)

Spacing scale:
  xs:   4px   (0.25rem)   — Badge-Innenabstand
  sm:   8px   (0.5rem)    — Kompakte Elemente
  md:   16px  (1rem)      — Standard-Abstand
  lg:   24px  (1.5rem)    — Karten-Padding
  xl:   32px  (2rem)      — Sektionsabstand
  2xl:  48px  (3rem)      — Gruppenabstand

Border radius:
  sm:   4px    (Inputs, Tags, Badges)
  md:   8px    (Karten, Buttons)
  lg:   12px   (Modals, Panels)
  full: 9999px (Status-Pillen)

Shadows:
  sm:  0 1px 3px rgba(0,0,0,0.06)     — Sendungs-Karten
  md:  0 4px 12px rgba(0,0,0,0.08)    — Carrier-Gruppen, Hover
  lg:  0 8px 24px rgba(0,0,0,0.10)    — Modals, Unterschrift-Dialog
```

### 2.4 Komponenten

#### Mode-Switch (Header)

- Position: rechts im bestehenden Header, neben den Settings
- Style: Toggle-Pill mit zwei Segmenten: 「LKW」und 「Kurier」
- Aktives Segment: gefüllt mit `--color-primary` des jeweiligen Modus (Rosa oder Blau)
- Inaktives Segment: transparent mit `--color-text-muted`
- Übergang: sanfte 200ms Farbanimation beim Wechsel
- Größe: Höhe 36px, min. 160px breit

#### Carrier-Gruppen-Karte

- Background: `--color-surface`
- Linker Rand: 4px solid in Carrier-Farbe (FedEx Lila, DHL Gelb, UPS Braun)
- Header: Carrier-Logo/Name + Badge mit Anzahl Sendungen + Status-Badge (z.B. "3 offen")
- Aufklappbar/zuklappbar via Chevron
- Padding: `lg`
- Shadow: `sm`, auf Hover `md`

#### Sendungs-Karte (innerhalb Carrier-Gruppe)

- Kompakte Zeile/Karte pro Sendung
- Links: Lieferscheinnummer(n) in `DM Mono`
- Mitte: Dokumenten-Chips (Label ✓, Rechnung ✓, EDEC ✓ etc.)
- Rechts: Status-Badge + Aktions-Buttons
- Border-bottom: `1px solid --color-border` als Trenner
- Hover: leichter `--color-accent-bg` Hintergrund

#### Dokumenten-Chip

- Kleiner Pill/Tag pro Dokument
- Vorausgewählt (drucken): gefüllt mit `--color-primary` Hintergrund (10% Opacity), Text in `--color-primary`
- Nicht vorausgewählt: `--color-border` Hintergrund, `--color-text-muted` Text
- Klickbar zum Umschalten (Druckauswahl ändern)
- Icons: kleines Drucker-Icon wenn zum Druck markiert

#### Status-Badges

| Status | Farbe | Text |
|---|---|---|
| Offen | `--color-primary` (Blau) | Offen |
| Gedruckt | `--color-warning` (Amber) | Gedruckt |
| Unterschrieben | `--color-success` (Grün) | Unterschrieben |
| Archiviert | `--color-text-muted` (Grau) | Archiviert |
| Fehler | `--color-danger` (Rot) | Zuordnung prüfen |

#### Unterschrift-Dialog (Modal)

- Volle Breite Modal, zentriert
- Header: Carrier-Name + Anzahl Sendungen die unterschrieben werden
- Liste aller betroffenen Lieferscheinnummern (scrollbar wenn viele)
- Großes Signature-Canvas (min. 500×200px) — identisch mit bestehendem HandOver Canvas
- Optionales Textfeld: "Name des Fahrers"
- Buttons: "Unterschreiben & Archivieren" (Primary) / "Abbrechen" (Ghost)
- Shadow: `lg`

#### Buttons (bestehend, unverändert)

- Primary: gefüllt mit `--color-primary`, weißer Text, `border-radius: md`
- Secondary: outlined mit `--color-primary` Rand
- Danger: gefüllt mit `--color-danger`
- Ghost: kein Hintergrund, subtiler Hover
- Disabled: 40% Opacity

#### Toolbar (Aktionsleiste)

- Sticky am oberen Rand des Content-Bereichs (unter Header)
- Links: Datumswähler (heute vorausgewählt)
- Mitte: "E-Mails abrufen" Button (Primary)
- Rechts: Filter (Carrier-Dropdown), Suche (Lieferscheinnummer)
- Background: `--color-surface` mit `sm` Shadow

---

## 3. Seitenstruktur & Wireframes

### 3.1 Header mit Mode-Switch

```
┌──────────────────────────────────────────────────────────────┐
│  書 HandOver              ┌─────────────────┐    ⚙ Settings │
│                           │ LKW │▓ Kurier ▓│               │
│                           └─────────────────┘               │
└──────────────────────────────────────────────────────────────┘
```

- Logo + App-Name links
- Mode-Switch zentriert (oder leicht rechts)
- Settings-Zahnrad rechts
- Header-Hintergrund: `--color-surface`, untere Border `--color-primary` (2px) als Modus-Indikator

### 3.2 Kurier-Dashboard (Hauptansicht)

**Purpose:** Tagesübersicht aller Kuriersendungen, gruppiert nach Carrier
**Users:** Logistikmitarbeiter

```
┌──────────────────────────────────────────────────────────────┐
│  書 HandOver              │ LKW │▓ Kurier ▓│     ⚙ Settings │
├──────────────────────────────────────────────────────────────┤
│  📅 01.05.2026  │  🔄 E-Mails abrufen  │  Carrier ▾  │ 🔍  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Kurier — 01.05.2026                          12 Sendungen   │
│                                                              │
│  ┌─ FedEx / TNT ──────────────────────── 5 Sendungen ─────┐ │
│  │▓                                                        │ │
│  │▓  4500012345    [Label ✓] [Rechnung ✓]        ● Offen   │ │
│  │▓  4500012346    [Label ✓] [Rechnung ✓]        ● Offen   │ │
│  │▓  4500012347    [Label ✓] [Rechnung ✓]        ● Offen   │ │
│  │▓               [EDEC ✓]  ← TNT-Sendung                 │ │
│  │▓  4500012348    [Label ✓] [Rechnung ✓]        ● Gedruckt│ │
│  │▓  4500012349    [Label ✓] [Rechnung ✓]        ● Gedruckt│ │
│  │▓                                                        │ │
│  │▓  [ 🖨 Alle drucken ]   [ ✍ Unterschrift erfassen ]    │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌─ DHL ──────────────────────────────── 4 Sendungen ─────┐ │
│  │▓                                                        │ │
│  │▓  4500012350    [Label ✓] [Rechnung ✓] [PKL ✓]         │ │
│  │▓               [EDEC ✓] [TO ✓] [LS ✓]      ● Offen    │ │
│  │▓  ...                                                   │ │
│  │▓                                                        │ │
│  │▓  [ 🖨 Alle drucken ]   [ ✍ Unterschrift erfassen ]    │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌─ UPS ──────────────────────────────── 3 Sendungen ─────┐ │
│  │▓  ...                                                   │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Key elements:**
- Toolbar: Datumswähler, E-Mails abrufen, Carrier-Filter, Suchfeld
- Seitentitel mit Datum und Gesamtanzahl Sendungen
- Carrier-Gruppen: aufklappbare Karten mit linkem Farbrand
- Pro Sendung: Lieferscheinnummer (Mono), Dokumenten-Chips, Status-Badge
- Gruppen-Footer: "Alle drucken" + "Unterschrift erfassen" Buttons pro Carrier

**Empty state:** Zentrierte Illustration (minimalistisch, Shoriu-Style) mit Text: "Keine Sendungen für heute. E-Mails abrufen um zu starten." + Button "E-Mails abrufen"

**Loading state:** Skeleton-Loader in der Carrier-Gruppen-Struktur (3 graue Blöcke mit Puls-Animation)

### 3.3 Sendungs-Detail (Expandierte Ansicht)

**Purpose:** Alle Dokumente einer Sendung im Detail sehen und einzeln steuern
**Users:** Logistikmitarbeiter

```
┌─────────────────────────────────────────────────────────────┐
│  ← Zurück zur Übersicht                                     │
│                                                              │
│  Sendung 4500012345                          FedEx │ ● Offen │
│  E-Mail: "Versanddokumente 4500012345"                      │
│  Empfangen: 01.05.2026 13:42                                │
│                                                              │
│  Dokumente                                                   │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  ☑ 📄 FEDEX_Label_4500012345.pdf         [👁 Vorschau]│  │
│  │  ☑ 📄 Rechnung_4500012345.pdf            [👁 Vorschau]│  │
│  │  ☐ 📄 Lieferschein_4500012345.pdf        [👁 Vorschau]│  │
│  │  ☐ 📄 TO_4500012345.pdf                  [👁 Vorschau]│  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  [ 🖨 Ausgewählte drucken ]                                 │
│                                                              │
│  ┌─ PDF Vorschau ─────────────────────────────────────────┐  │
│  │                                                         │  │
│  │                  [PDF Viewer]                            │  │
│  │                                                         │  │
│  └─────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

**Key elements:**
- Breadcrumb-Navigation zurück zur Übersicht
- Sendungsinfo: Lieferscheinnummer, Carrier, Status, E-Mail-Referenz
- Dokumentenliste mit Checkboxen (vorausgewählt nach Carrier-Druckset)
- Vorschau-Button pro Dokument → öffnet PDF-Viewer (bestehende Komponente)
- Drucken-Button für ausgewählte Dokumente

**Empty state:** Nicht anwendbar (nur erreichbar wenn Sendung existiert)

**Loading state:** Spinner auf dem PDF-Viewer während Dokument geladen wird

### 3.4 Unterschrift-Modal

**Purpose:** Gesammelte Unterschrift für alle Sendungen eines Carriers erfassen
**Users:** Logistikmitarbeiter (erfasst Unterschrift des Kurierfahrers)

```
┌──────────────────────────────────────────────────────────────┐
│                                                          ✕   │
│  Unterschrift — FedEx / TNT                                  │
│  5 Sendungen werden unterschrieben                           │
│                                                              │
│  Betroffene Lieferscheine:                                   │
│  4500012345 · 4500012346 · 4500012347 · 4500012348 ·        │
│  4500012349                                                  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                                                        │  │
│  │                                                        │  │
│  │              [ Unterschrift-Canvas ]                    │  │
│  │                                                        │  │
│  │                                                        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                          [ 🗑 Löschen ]      │
│                                                              │
│  Name des Fahrers (optional): [________________________]     │
│                                                              │
│  ┌─────────────────────┐   ┌──────────────────────────────┐  │
│  │     Abbrechen        │   │  ✍ Unterschreiben & Archiv. │  │
│  └─────────────────────┘   └──────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

**Key elements:**
- Carrier-Name und Anzahl Sendungen im Header
- Auflistung aller Lieferscheinnummern (in DM Mono)
- Signature-Canvas (wiederverwendet von HandOver)
- Löschen-Button unter dem Canvas zum Zurücksetzen
- Optionales Fahrer-Name-Feld
- Primary-Button: "Unterschreiben & Archivieren" → brennt Unterschrift auf alle PKL/Lieferscheine und archiviert

**Bestätigung:** Nach erfolgreichem Archivieren → kurze Toast-Notification: "5 Sendungen archiviert ✓" + Carrier-Gruppe wechselt zu Status "Archiviert"

### 3.5 Carrier-Konfiguration (Settings-Erweiterung)

**Purpose:** Carrier verwalten — neue hinzufügen, Drucksets anpassen
**Users:** Teamleader / Admin

```
┌──────────────────────────────────────────────────────────────┐
│  Settings                                                    │
│                                                              │
│  ┌─ Allgemein ──────────────────────────────────────────────┐│
│  │  Kurier-Postfach: [kurier@firma.com___________]          ││
│  │  Archiv-Pfad:     [C:\Archiv\Kurier___________] [📁]    ││
│  │  Standard-Modus:  (○ LKW) (● Kurier)                    ││
│  └──────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌─ Carrier-Konfiguration ──────────────────────────────────┐│
│  │                                                          ││
│  │  FedEx / TNT                                    [✏][🗑] ││
│  │  Keywords: fedex, tnt, federal express                   ││
│  │  Druckset: Label, Rechnung (TNT: +EDEC)                 ││
│  │  ────────────────────────────────────────────────────    ││
│  │  DHL                                            [✏][🗑] ││
│  │  Keywords: dhl, deutsche post                            ││
│  │  Druckset: Alle Dokumente                                ││
│  │  ────────────────────────────────────────────────────    ││
│  │  UPS                                            [✏][🗑] ││
│  │  Keywords: ups, united parcel                            ││
│  │  Druckset: Alle Dokumente                                ││
│  │                                                          ││
│  │  [ + Neuen Carrier hinzufügen ]                          ││
│  └──────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
```

**Key elements:**
- Kurier-Postfach und Archivpfad Konfiguration
- Standard-Modus Auswahl (welcher Modus beim Start)
- Carrier-Liste mit Edit/Delete Buttons
- Pro Carrier: Keywords und Druckset-Regeln sichtbar
- "Neuen Carrier hinzufügen" Button → Inline-Formular oder kleines Modal

**Empty state:** Keine Carrier konfiguriert → Hinweis "Noch keine Carrier konfiguriert. Standard-Carrier laden?" + Button

---

## 4. Responsive Verhalten

HandOver ist eine Desktop-App (Tauri), daher kein echtes Responsive Design nötig. Trotzdem:

| Fenstergröße | Layout-Anpassungen |
|---|---|
| < 900px Breite | Carrier-Gruppen stacken vertikal, Dokumenten-Chips umbrechen |
| 900–1200px | Standard-Layout, eine Spalte |
| > 1200px | Standard-Layout, optional breitere PDF-Vorschau |

Minimale Fenstergröße: 800×600px (identisch mit HandOver)

---

## 5. Accessibility

- Farbkontrast: alle Texte ≥ 4.5:1 auf ihrem jeweiligen Hintergrund
- Carrier-Farben werden nie allein für Bedeutung verwendet — immer mit Text-Label kombiniert
- Fokus-Stile: sichtbarer `2px solid --color-primary` Outline auf allen interaktiven Elementen
- Tastaturnavigation: Tab durch Carrier-Gruppen → Enter zum Aufklappen → Tab durch Sendungen
- Unterschrift-Canvas: "Name des Fahrers" Textfeld als barrierefreie Alternative
- Status-Badges: Icon + Text, nicht nur Farbe (● Offen, ✓ Archiviert)

---

## 6. Übergänge & Animationen

| Element | Animation | Dauer |
|---|---|---|
| Mode-Switch | Sanftes Farb-Crossfade auf Root-CSS-Variablen | 200ms ease |
| Carrier-Gruppe aufklappen | Height-Animation mit opacity fade-in der Sendungen | 250ms ease-out |
| Status-Badge Wechsel | Kurzes Aufblitzen (scale 1.05 → 1.0) + Farbwechsel | 150ms |
| Unterschrift-Modal | Fade-in + leichtes slide-up | 200ms ease-out |
| Toast-Notification | Slide-in von rechts oben, auto-dismiss nach 3s | 300ms |
| Skeleton-Loader | Puls-Animation (opacity 0.4 → 1.0) | 1.5s infinite |

---

## 7. Nächste Schritte

- [ ] Design reviewen und freigeben
- [ ] CSS-Variablen für Kurier-Modus ins Projekt übernehmen
- [ ] Mode-Switch Komponente implementieren
- [ ] Carrier-Gruppen Karte als Vue-Komponente bauen
- [ ] Entwicklung tracken → *app-dev-tracker Skill*

---

*Erstellt mit dem app-ui-design Skill · 01.05.2026*
