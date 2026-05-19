# HandOver — Verbesserungs- & Optimierungsdokument

> Lebendiges Dokument · Zuletzt aktualisiert: 2026-05-19  
> Status-Legende: 🔴 Offen · 🟡 In Arbeit · 🟢 Erledigt

---

## #1 — Firmenname & Logo im Header

**Priorität:** Hoch · **Status:** 🔴 Offen · **Bereich:** UI / Settings

Links oben beim Logo wird statisch der Text „meine Firma" angezeigt, anstatt den tatsächlichen Firmennamen aus den Einstellungen zu übernehmen.

**Gewünschtes Verhalten:**
- Firmenname wird dynamisch aus den App-Einstellungen übernommen
- Fallback: „meine Firma" nur wenn kein Name hinterlegt ist
- Firmenlogo: Mögliche Positionen zur Diskussion:

| Option | Position | Pro | Con |
|--------|----------|-----|-----|
| A | Header links, neben App-Logo | Gut sichtbar, professionell | Platzbedarf bei langen Namen |
| B | Header rechts | Klare Trennung App ↔ Firma | Weniger prominent |
| C | Nur in der LKW-Mode Übergabeansicht | Relevant wo Fahrer es sieht | Nicht überall präsent |
| D | Druckfußzeile / Archiv-Dokument | Dokumentenidentifikation | Nur in Outputs sichtbar |

---

## #2 — Archivierung: Duplikat-Dateinamen mit Nummerierung

**Priorität:** Hoch · **Status:** 🔴 Offen · **Bereich:** Backend / Archivierung

Wenn beim Archivieren bereits eine Datei mit demselben Namen existiert, wird diese überschrieben oder ein Fehler ausgelöst.

**Gewünschtes Verhalten:**
- Automatische Nummerierung bei Namenskollision
- Beispiel: `signed_dateiname.pdf` bereits vorhanden → neue Datei wird `signed_dateiname_1.pdf`, bei erneuter Kollision `signed_dateiname_2.pdf` usw.

---

## #3 — Drucken über USB funktioniert nicht

**Priorität:** Hoch · **Status:** 🔴 Offen · **Bereich:** Drucker / Windows

Druckaufträge über USB-angeschlossene Drucker schlagen fehl.

**Mögliche Ursachen:**
- Der im Code verwendete Druckername stimmt nicht mit dem tatsächlichen Windows-Druckernamen überein (USB-Drucker werden unter Windows teils mit abweichendem internen Namen registriert)
- Fehlende Fehlerausgabe beim Druckversuch erschwert die Diagnose

**Nächste Schritte:**
- Fehlerlog beim Druckversuch erfassen und sichtbar ausgeben
- Exakten Windows-Druckernamen auf dem medmix-Gerät auslesen und mit dem Code-String abgleichen

---

## #4 — LKW-Mode Übergabeansicht: Vollbild-Skalierung

**Priorität:** Mittel · **Status:** 🔴 Offen · **Bereich:** UI / LKW-Mode

Beim Wechsel in den Vollbildmodus bleibt die Übergabeansicht in der ursprünglichen Größe und Position.

**Gewünschtes Verhalten:**
- Inhalt zentriert sich im Vollbild
- Schrift und UI-Elemente skalieren proportional mit der Fenstergröße
- Lesbarkeit für LKW-Fahrer aus Abstand gewährleistet

---

## #5 — Dashboard: Offene Übergaben — Interaktion

**Priorität:** Hoch · **Status:** 🔴 Offen · **Bereich:** Dashboard / Workflow

Offene Übergaben im Dashboard sind aktuell nur zur Ansicht, es fehlt die Möglichkeit direkt zu interagieren.

**Gewünschtes Verhalten:**
- Jede offene Übergabe ist anklickbar und öffnet den bestehenden Vorgang zur Weiterführung
- Zusätzlich: Option zum vollständigen Abbrechen einer offenen Übergabe

---

## #6 — Dashboard: Letzte Übergaben — Limitierung & Mehr-Button

**Priorität:** Mittel · **Status:** 🔴 Offen · **Bereich:** Dashboard

Die Liste der letzten Übergaben zeigt aktuell alle Einträge ungefiltert.

**Gewünschtes Verhalten:**
- Maximal 10 Einträge werden standardmäßig angezeigt
- Ein „Alle anzeigen"-Button lädt die vollständige Liste nach

---

## #7 — Archivmenü: Öffnen & Download-Button defekt + falsches Dokument

**Priorität:** Hoch · **Status:** 🔴 Offen · **Bereich:** Archiv

Zwei separate Probleme im Archivmenü:

1. **Buttons funktionieren nicht:** Die Schaltflächen „Öffnen" und „Download" reagieren nicht oder schlagen fehl.
2. **Falsches Dokument:** Es wird das von der App generierte Dokument angezeigt, nicht das tatsächlich unterschriebene (archivierte) Dokument.

**Gewünschtes Verhalten:**
- „Öffnen" öffnet das unterschriebene PDF direkt im System-Viewer
- „Download" speichert das unterschriebene PDF an einem vom Nutzer gewählten Ort
- Angezeigtes Dokument ist immer die final unterschriebene Version

---

## #8 — Statistik: Monatsauswertung + Carrier-Auswertung

**Priorität:** Mittel · **Status:** 🔴 Offen · **Bereich:** Statistik

**Gewünschtes Verhalten:**
- Auswertung standardmäßig auf den aktuellen Monat gefiltert (anpassbar)
- Kurier-Statistik: Aufschlüsselung nach Carrier (z.B. DHL, UPS, DPD …) — Anzahl Übergaben pro Carrier, Vergleich über Zeit

---

## #9 — Kurier: Manuelle Sendungserfassung überarbeiten

**Priorität:** Mittel · **Status:** 🔴 Offen · **Bereich:** Kurier-Modul

Die manuelle Sendungserfassung im Kurier-Bereich muss überarbeitet werden.

**Details:** *(noch zu spezifizieren — bitte Anforderungen ergänzen)*

---

## Backlog / Weitere Punkte

| # | Beschreibung | Priorität | Status |
|---|---|---|---|
| 10 | *(folgt)* | — | 🔴 Offen |

---

*Dieses Dokument wird laufend ergänzt.*
