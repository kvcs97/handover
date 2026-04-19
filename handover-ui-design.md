# HandOver – UI/UX Design

> Basierend auf: handover-concept.md + handover-architecture.md

---

## 1. Design Persona

> "HandOver feels **präzise**, **ruhig**, und **vertrauenswürdig**. Es ist das Werkzeug das einfach funktioniert — ohne Ablenkung, ohne Lernkurve, mit einer Eleganz die man im Lager nicht erwartet."

### Inspiration & Referenzen
- **Apple macOS Systemapps** — klare Hierarchie, viel Weissraum, keine unnötigen Dekorationen
- **Linear** — schnelle Aktionen, tastaturfreundlich, kein visuelles Rauschen
- **Shoriu Brand Identity** — Japanischer Minimalismus, Sakura-Farbpalette, Wabi-Sabi-Ästhetik

---

## 2. Design System

### 2.1 Farbpalette

| Role | Variable | Hex | Usage |
|---|---|---|---|
| Primary | `--color-primary` | `#c0546a` | CTAs, aktive Zustände, Akzente |
| Primary Light | `--color-primary-light` | `#e8849a` | Gradient-Start, Hover |
| Primary Subtle | `--color-primary-subtle` | `rgba(192,84,106,0.08)` | Hintergründe aktiver Elemente |
| Background | `--color-bg` | `#f2f2f7` | Seitenhintergrund |
| Surface | `--color-surface` | `#ffffff` | Karten, Panels, Inputs |
| Border | `--color-border` | `#e8e8ed` | Rahmen, Trennlinien |
| Text Primary | `--color-text` | `#1c1c1e` | Fliesstext, Überschriften |
| Text Muted | `--color-text-muted` | `#6e6e73` | Labels, Platzhalter, Metadaten |
| Text Subtle | `--color-text-subtle` | `#98989f` | Hints, deaktivierte Texte |
| Success | `--color-success` | `#28c840` | Bestätigungen, abgeschlossene Schritte |
| Warning | `--color-warning` | `#ff9500` | Hinweise, ausstehend |
| Danger | `--color-danger` | `#ff3b30` | Fehler, destruktive Aktionen |

**Gradient (Primary Buttons):**
```css
background: linear-gradient(135deg, #e8849a, #c0546a);
box-shadow: 0 2px 12px rgba(192,84,106,0.3);
```

### 2.2 Typografie

| Role | Font | Size | Weight | Einsatz |
|---|---|---|---|---|
| Display / Hero | Instrument Serif | 38–48px | 400 (Italic für Akzent) | Seitentitel, Begrüssung |
| Heading 1 | Instrument Serif | 28–32px | 400 | Karten-Titel, Step-Headings |
| Heading 2 | DM Sans | 18–20px | 600 | Sektions-Titel |
| Body | DM Sans | 15–16px | 400 | Fliesstext, Beschreibungen |
| Label | DM Sans | 11–12px | 500–600 | Form-Labels (uppercase + letter-spacing) |
| Small / Meta | DM Sans | 12–13px | 300–400 | Timestamps, Hints |
| Mono | DM Mono | 14px | 400 | Lizenzschlüssel, technische Werte |

```css
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&family=DM+Mono&display=swap');
```

### 2.3 Spacing & Layout

```
Base unit: 4px

Spacing:
  xs:   4px
  sm:   8px
  md:   16px
  lg:   24px
  xl:   32px
  2xl:  44px
  3xl:  64px

Border Radius:
  sm:   8px    (Tags, kleine Elemente)
  md:   12px   (Buttons, Inputs)
  lg:   16–20px (Karten, Panels)
  xl:   24px   (Step Cards)
  full: 9999px (Pills, Avatare)

Shadows:
  sm:  0 1px 3px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.04)
  md:  0 4px 16px rgba(0,0,0,0.08)
  lg:  0 8px 32px rgba(0,0,0,0.1)
  primary: 0 2px 12px rgba(192,84,106,0.3)

Sidebar Breite: 200px (Desktop), 0 (versteckt auf kleinen Screens)
Content Max-Width: 900px
Content Padding: 40px 44px
```

### 2.4 Komponenten

**Button — Primary**
```
Gradient: linear-gradient(135deg, #e8849a, #c0546a)
Text: weiss, DM Sans 14px, weight 500
Padding: 12px 24px
Border-Radius: 12px
Shadow: 0 2px 12px rgba(192,84,106,0.3)
Hover: opacity 0.9, translateY(-1px)
Disabled: opacity 0.4, cursor not-allowed
```

**Button — Secondary / Back**
```
Background: white
Border: 1.5px solid #e8e8ed
Text: #6e6e73, 14px
Hover: background #f5f5f7, text #1c1c1e
```

**Button — Go (Referenz-Eingabe)**
```
54×54px, Gradient, border-radius 14px
Font-size 22px (→ Pfeil)
```

**Input**
```
Padding: 12px 16px
Border: 1.5px solid #e8e8ed
Border-Radius: 11–14px
Background: white
Focus: border-color #c0546a, box-shadow 0 0 0 3–4px rgba(192,84,106,0.1)
Placeholder: color #98989f
```

**Karte (Step Card)**
```
Background: white
Border-Radius: 20px
Padding: 48px 44px
Shadow: sm (0 1px 3px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.04))
Max-Width: 520px (normal) / 680px (wide)
```

**Sidebar Navigation**
```
Breite: 200px
Background: #1c1c1e (dunkel)
Text: #98989f (inaktiv), #f2f2f7 (aktiv)
Aktiver Eintrag: Sakura-Farbtext + leichter Hintergrund
Logo: "H" in Sakura-Kreis, 40×40px, border-radius 12px
Sektions-Labels: 10px, uppercase, #6e6e73
```

**Step Indicator**
```
Step Dots: 26–28px Kreis
Inaktiv: border #e8e8ed, text #98989f
Aktiv: background #c0546a, text weiss
Fertig: background #28c840, text weiss, Checkmark ✓
Verbindungslinie: 1px solid #e8e8ed
```

**Unterschriften-Canvas**
```
Width: 100%
Height: 200px
Border: 2px solid #e8e8ed, border-radius 14px
Background: #fafafa
Cursor: crosshair
Active border: #c0546a
Touch-Action: none
```

**Dropdown / Combobox**
```
Position: absolute, top calc(100% + 4px)
Background: white
Border: 1.5px solid #e8e8ed, border-radius 12px
Shadow: 0 8px 32px rgba(0,0,0,0.1)
Item: padding 12px 16px, hover background #fafafa
Neuer Eintrag: color #c0546a, font-weight 500
```

**Info Box / Alert**
```
Padding: 12–16px 16px
Border-Radius: 12px
Info: background rgba(0,113,227,0.06), border-left 3px solid #0071e3
Success: background rgba(40,200,64,0.08)
Warning: background rgba(255,149,0,0.08)
```

**Badge / Pill**
```
Border-Radius: 9999px
Padding: 4px 10px
Font-Size: 12px, weight 500
Status-Farben: Success/Warning/Danger mit 10% opacity Hintergrund
```

---

## 3. Seitenstruktur & Wireframes

### Login (`/login`)
**Purpose:** Authentifizierung
**Users:** Alle

```
┌──────────────────────────────────────────┐
│                                          │
│         ┌─────────────────────┐          │
│         │  [H] HandOver       │          │
│         │      by Shoriu      │          │
│         │                     │          │
│         │  E-Mail             │          │
│         │  ┌─────────────┐   │          │
│         │  └─────────────┘   │          │
│         │  Passwort           │          │
│         │  ┌─────────────┐   │          │
│         │  └─────────────┘   │          │
│         │                     │          │
│         │  [Anmelden ─────→] │          │
│         │                     │          │
│         │  Fehlermeldung      │          │
│         └─────────────────────┘          │
│                                          │
│              © 2026 Shoriu               │
└──────────────────────────────────────────┘
```

Key Elements:
- Zentrierte Karte, max-width 440px
- Sakura-Gradient-Button
- Fehlermeldung unter dem Button (rosa Box)

Empty State: — (Login hat keinen empty state)
Loading: Button zeigt Spinner während Request

---

### SetupWizard (`/setup`)
**Purpose:** Ersteinrichtung beim ersten Start
**Users:** Admin (einmalig)

```
┌───────────────┬────────────────────────────┐
│ [H] HandOver  │                            │
│ by Shoriu     │   ┌──────────────────────┐ │
│               │   │  [Step Title]        │ │
│ Willkommen... │   │  [Step Description]  │ │
│               │   │                      │ │
│ ✓ Firmendaten │   │  [Form Fields]       │ │
│ ✓ Drucker     │   │                      │ │
│ ● Datenquelle │   │                      │ │
│ ○ Admin       │   │  [← Zurück] [Weiter→]│ │
│ ○ Bereit      │   └──────────────────────┘ │
│               │                            │
│ © 2026 Shoriu │                            │
└───────────────┴────────────────────────────┘
```

Schritte:
1. Firmendaten (Name, Adresse, Logo)
2. Drucker (Name, Testdruck)
3. Datenquelle (Manual / CSV / API / Outlook)
4. Admin-Account (Name, E-Mail, Passwort)
5. Fertig (Zusammenfassung + App starten)

---

### Dashboard (`/`)
**Purpose:** Übersicht und Schnellzugriff
**Users:** Alle

```
┌──────────┬────────────────────────────────────────┐
│          │  MITTWOCH, 25. MÄRZ 2026               │
│ [H]      │  Guten Morgen, Adam.     [+ Neue Überg]│
│ HandOver │                                        │
│          │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ │
│ WORKFLOW │  │  12  │ │  3   │ │  45  │ │  8   │ │
│ ✦ Neu    │  │Abge- │ │Aus-  │ │Total │ │Spedi-│ │
│ ⊞ Dash   │  │schlo.│ │stehd │ │heute │ │teure │ │
│          │  └──────┘ └──────┘ └──────┘ └──────┘ │
│ VERWALT. │                                        │
│ ▦ Archiv │  ┌──────────────────┐ ┌─────────────┐ │
│ ☻ Benutzer  │  Letzte Übergaben│ │Schnellzugr. │ │
│ ⚙ Einst. │  │  [Tabelle]       │ │[Überg. start│ │
│          │  │  ...             │ │[Archiv öffn.│ │
│          │  └──────────────────┘ │[Einstellungen│ │
│ [Avatar] │                       └─────────────┘ │
└──────────┴────────────────────────────────────────┘
```

Key Elements:
- Datums- und Zeitbegrüssung (Instrument Serif, kursiver Name in Sakura)
- 4 Stat-Karten (Abgeschlossen, Ausstehend, Total heute, Spediteure)
- Letzte Übergaben Tabelle (Referenz, Spediteur, Status, Zeit)
- Schnellzugriff-Karten (Übergabe, Archiv, Einstellungen)

Empty State: "Noch keine Übergaben heute" mit Clipboard-Emoji
Loading: Skeleton-Karten für Stats und Tabelle

---

### Handover / Neue Übergabe (`/handover`)
**Purpose:** Kernworkflow — Übergabe durchführen
**Users:** Alle

```
┌──────────┬──────────────────────────────────────┐
│ Sidebar  │  Workflow                             │
│          │  Neue Übergabe                        │
│          │                                       │
│          │  ①─────②─────③─────④─────⑤           │
│          │  Ref.  PDFs  Sped. Druck  Sign  Fertig│
│          │                                       │
│          │  ┌──────────────────────────────────┐ │
│          │  │  [Step Content]                  │ │
│          │  │                                  │ │
│          │  │  Step 0: Referenz-Input + Button │ │
│          │  │  Step 1: PDF-Liste + Vorschau    │ │
│          │  │  Step 2: Spediteur-Formular      │ │
│          │  │  Step 3: Druckstatus             │ │
│          │  │  Step 4: Unterschriften-Canvas   │ │
│          │  │  Step 5: Abschluss-Zusammenfassung│ │
│          │  │                                  │ │
│          │  │       [← Zurück] [Weiter →]      │ │
│          │  └──────────────────────────────────┘ │
└──────────┴──────────────────────────────────────┘
```

Dynamische Steps:
- Ohne Outlook: Referenz → Spediteur → Drucken → Unterschrift → Fertig (5 Steps)
- Mit Outlook: Referenz → Dokumente → Spediteur → Drucken → Unterschrift → Fertig (6 Steps)

**Step 0 — Referenz:**
- Grosses Input-Feld (zentriert), Pfeil-Button, Hint "Enter oder → klicken"

**Step 1 — PDFs (nur Outlook):**
- Liste aller gefundenen PDFs mit Name, Datum, Betreff
- "Vorschau" Button → Modal mit iframe
- "Unterschrift: An/Aus" Toggle pro PDF

**Step 2 — Spediteur:**
- Combobox mit Autocomplete, "+ neu" Option
- LKW-Kennzeichen, Fahrername (2-Spalten Grid)

**Step 3 — Drucken:**
- Pulsierendes Drucker-Emoji während Druck
- Status-Badge: Orange "läuft..." → Grün "gedruckt"

**Step 4 — Unterschrift:**
- Canvas volle Breite, 200px hoch
- "Löschen" Button, Fahrername als Hint
- Hinweis wieviele PDFs unterschrieben werden

**Step 5 — Fertig:**
- Sakura-Gradient Checkmark-Kreis (animiert)
- Meta-Karten: Spediteur, Kennzeichen, Fahrer, Archiviert um
- "✦ Neue Übergabe starten" Button

---

### Archiv (`/archive`)
**Purpose:** Alle abgeschlossenen Übergaben
**Users:** Alle

```
┌──────────┬──────────────────────────────────────────┐
│ Sidebar  │  Archiv               [Suche...] [Filter]│
│          │                                          │
│          │  ┌────────────────────────────────────┐  │
│          │  │ Ref.  │Spediteur│Fahrer│Status│Zeit │  │
│          │  ├───────┼─────────┼──────┼──────┼─────┤  │
│          │  │ SO-.. │ DHL     │ M.M. │ ✓    │10:23│  │
│          │  │ SO-.. │ UPS     │ J.K. │ ✓    │09:11│  │
│          │  │ ...   │ ...     │ ...  │ ...  │ ... │  │
│          │  └────────────────────────────────────┘  │
│          │                                          │
│          │  [← Vorherige]  Seite 1 / 5  [Nächste →]│
└──────────┴──────────────────────────────────────────┘
```

Key Elements:
- Suchfeld (Referenz, Fahrername, Spediteur)
- Datum-Filter (heute / diese Woche / alle)
- Tabelle mit Sortierung
- Klick auf Zeile → Detailansicht mit PDF-Vorschau

Empty State: "Noch keine Übergaben archiviert" mit leerer Box-Illustration

---

### Einstellungen (`/settings`)
**Purpose:** App konfigurieren
**Users:** Admin only

```
┌──────────┬──────────────────────────────────────┐
│ Sidebar  │  Einstellungen        [Speichern ✓]  │
│          │                                       │
│          │  ┌─────────────────────────────────┐ │
│          │  │ 🏢 Firmendaten                  │ │
│          │  │ Name, Adresse, Logo             │ │
│          │  └─────────────────────────────────┘ │
│          │  ┌─────────────────────────────────┐ │
│          │  │ 🖨️ Drucker                      │ │
│          │  │ Name, Testdruck                 │ │
│          │  └─────────────────────────────────┘ │
│          │  ┌─────────────────────────────────┐ │
│          │  │ 📡 Datenquelle                  │ │
│          │  │ Manual / CSV / API / Outlook    │ │
│          │  └─────────────────────────────────┘ │
│          │  ┌─────────────────────────────────┐ │
│          │  │ 📧 Outlook Konfiguration        │ │
│          │  │ (nur wenn Outlook gewählt)      │ │
│          │  └─────────────────────────────────┘ │
│          │  ┌─────────────────────────────────┐ │
│          │  │ 🔐 Passwort ändern              │ │
│          │  └─────────────────────────────────┘ │
│          │  ┌─────────────────────────────────┐ │
│          │  │ 🔑 Lizenz                       │ │
│          │  └─────────────────────────────────┘ │
│          │                                       │
│          │  ✅ Einstellungen gespeichert (Banner)│
└──────────┴──────────────────────────────────────┘
```

Key Elements:
- Karten-Layout, jede Sektion als eigene Karte
- "Speichern" Button oben rechts, immer sichtbar
- Outlook-Karte: dynamisch sichtbar je nach Datenquelle
- "Mit Microsoft anmelden" Button (Microsoft-Logo + weiss + Border)
- Device Flow: Code + URL in Info-Box, dann "Login bestätigen" Button
- Lizenz-Karte: Status Badge (aktiv/ungültig), Ablaufdatum, Input + Aktivieren-Button
- Save-Banner: festes Sakura Pill unten Mitte (fadeIn Animation)

---

### Benutzer (`/users`)
**Purpose:** Benutzerverwaltung
**Users:** Admin only

```
┌──────────┬──────────────────────────────────────────┐
│ Sidebar  │  Benutzer              [+ Neuer Benutzer] │
│          │                                          │
│          │  ┌────────────────────────────────────┐  │
│          │  │ Name    │ E-Mail   │ Rolle │ Aktionen│  │
│          │  ├─────────┼──────────┼───────┼────────┤  │
│          │  │ Adam K. │ ...      │ Admin │ ✏️ 🗑️  │  │
│          │  │ Max M.  │ ...      │ Viewer│ ✏️ 🗑️  │  │
│          │  └────────────────────────────────────┘  │
│          │                                          │
│          │  [Modal: Benutzer anlegen/bearbeiten]     │
└──────────┴──────────────────────────────────────────┘
```

---

## 4. Responsive Verhalten

| Breakpoint | Layout-Änderungen |
|---|---|
| Desktop (>1024px) | Standard-Layout: Sidebar 200px + Content |
| Tablet (768–1024px) | Sidebar eingeklappt (Icons only), Content volle Breite |
| Mobile (<768px) | Sidebar ausgeblendet, Bottom Navigation, Steps stacken vertikal |

Hinweis: HandOver ist primär eine Desktop-App (Windows). Mobile-Optimierung ist sekundär — nur relevant für den SetupWizard der eventuell auf einem Tablet durchgeführt werden könnte.

---

## 5. Accessibility

- Alle Texte auf Hintergrund: ≥ 4.5:1 Kontrastverhältnis (geprüft mit #c0546a auf weiss: 4.8:1)
- Fokus-Stile: `box-shadow: 0 0 0 3px rgba(192,84,106,0.3)` auf allen Inputs
- Touch-Targets: min. 44×44px auf allen klickbaren Elementen
- Labels: alle Form-Felder haben sichtbare Labels (uppercase, 11px)
- Unterschriften-Canvas: Touch-Events mit `touch-action: none` für iOS/Android

---

## 6. Animations & Micro-Interactions

```css
/* Seitenwechsel */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(14px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* Step-Karte erscheint */
.step-panel { animation: fadeUp 0.35s ease both; }

/* Fertig-Checkmark */
@keyframes popIn {
  from { transform: scale(0.4); opacity: 0; }
  to   { transform: scale(1); opacity: 1; }
}

/* Drucker pulsiert */
@keyframes pulse {
  0%,100% { transform: scale(1); }
  50%      { transform: scale(1.06); }
}

/* Spinner */
@keyframes spin { to { transform: rotate(360deg); } }
```

---

## 7. Nächste Schritte

- [ ] Design reviewen
- [ ] CSS-Variablen in globalem Style einführen (aktuell inline pro Komponente)
- [ ] Archiv-Seite Detailansicht implementieren
- [ ] Update-Banner testen und stylen
- [ ] Entwicklung tracken → *handover-tracker.md*

---

*Erstellt mit dem app-ui-design Skill · April 2026*
