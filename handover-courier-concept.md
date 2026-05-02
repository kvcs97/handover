# HandOver Courier – Konzeptdokument

> Ein Erweiterungsmodul für HandOver, das den täglichen Kurier-Versandprozess digitalisiert — vom E-Mail-Eingang über die carrierbasierte Dokumentenzuordnung und Druck bis zur gesammelten Fahrerunterschrift pro Kurierdienstleister.

---

## 1. Problem & Zielsetzung

Der tägliche Kurier-Versandprozess ist repetitiv und fehleranfällig: E-Mails werden einzeln durchgeklickt, Dokumente manuell zugeordnet, ausgedruckt und physisch in Versandtaschen sortiert. Bei mehreren Sendungen pro Mail (Multi-Lieferschein) steigt die Komplexität. Die Unterschrift des Kurierfahrers erfolgt auf Papier ohne digitale Archivierung.

**Ziel:** Alle Versanddokumente eines Tages in einem Workflow erfassen, automatisch nach Carrier und Sendung gruppieren, mit einem Klick das korrekte Druckset ausgeben und die Fahrerunterschrift gesammelt pro Carrier digital auf den PKL/Lieferschein brennen und archivieren.

---

## 2. Zielgruppe

| Nutzertyp | Beschreibung | Hauptbedürfnis |
|---|---|---|
| Logistikmitarbeiter (Versand) | Bearbeitet täglich eingehende Versand-E-Mails, druckt Dokumente, bereitet Pakete vor | Kein manuelles Durchklicken einzelner Mails; alles auf einen Blick, ein Klick zum Drucken |
| Teamleader Logistik | Überwacht den Versandprozess, braucht Nachvollziehbarkeit | Digitales Archiv mit Unterschriften, Tagesübersicht |
| Kurierfahrer (FedEx, TNT, DHL, UPS) | Scannt Pakete ab, unterschreibt Übernahme | Eine Unterschrift pro Abholung statt pro Paket |

---

## 3. Kernfunktionen (MVP)

- **Dediziertes Postfach abrufen** – Verbindung zum Kurier-E-Mail-Postfach via IMAP/OAuth. Alle E-Mails eines Tages (oder Zeitfensters bis ~14:30) abrufen. E-Mails kommen von verschiedenen Personen/Abteilungen — der Absender ist kein zuverlässiger Filter, das dedizierte Postfach selbst ist der Filter. Wiederverwendung der bestehenden HandOver-E-Mail-Engine.

- **Lieferscheinnummer-Parsing** – Betreffzeilen parsen und Lieferscheinnummern extrahieren. Unterstützung für Multi-Lieferschein-Mails (2–3 Nummern im Betreff).

- **Automatische Carrier-Erkennung** – Carrier wird aus dem E-Mail-Betreff oder den Dateinamen der Anhänge erkannt (FedEx, TNT, DHL, UPS). TNT wird als FedEx-Tochter zusammengefasst → eine gemeinsame Carrier-Gruppe "FedEx/TNT" mit jeweiligem Druckset. Bestimmt automatisch das korrekte Druckset.

- **Carrier-basiertes Druckset** – Automatische Vorauswahl der zu druckenden Dokumente pro Sendung:
  - **FedEx:** Label + Rechnung
  - **TNT:** Label + Rechnung + EDEC (trotz FedEx-Gruppierung eigenes Druckset)
  - **DHL / UPS:** Alle Dokumente

- **Dokumenten-Zuordnung pro Sendung** – Anhänge anhand der Lieferscheinnummer im Dateinamen der jeweiligen Sendung zuordnen. Bei Multi-Lieferschein-Mails korrekt splitten.

- **Tagesübersicht mit Carrier-Gruppierung** – Dashboard-Ansicht: alle Sendungen des Tages, gruppiert nach Carrier. Status pro Sendung (offen / gedruckt / unterschrieben / archiviert).

- **Batch-Druck** – Alle Dokumente einer Sendung oder eines ganzen Carriers in einem Rutsch drucken.

- **Gesammelte Unterschrift pro Carrier** – Unterschriftfeld pro Carrier-Gruppe (nicht pro Sendung). FedEx und TNT werden zusammengefasst → eine Unterschrift für alle FedEx/TNT-Sendungen. DHL und UPS jeweils separat. Unterschrift wird auf den PKL/Lieferschein jeder zugehörigen Sendung eingebrannt.

- **Archivierung** – Unterschriebene PKL/Lieferscheine archivieren (lokaler Ordner). Gleiche Archivierungs-Engine wie HandOver.

---

## 4. Erweiterungen (Phase 2+)

- **Tracking-Nummer Extraktion** – Tracking-Nummern aus Labels extrahieren und in der Übersicht anzeigen.
- **Abholzeitfenster** – Erwartete Abholzeit pro Carrier hinterlegen, Countdown/Reminder.
- **Statistik-Dashboard** – Sendungen pro Tag/Woche/Carrier, Volumen-Trends.
- **Automatische Carrier-Benachrichtigung** – E-Mail an OM oder Carrier wenn alle Sendungen bereit sind.
- **Barcode/QR-Scan** – Paketnummer scannen um Sendung in der App zu matchen (z.B. via USB-Scanner).
- **Multi-Standort** – Mehrere Versandstandorte mit jeweils eigenem Postfach verwalten.

---

## 5. User Stories

- Als **Logistikmitarbeiter** möchte ich **alle Versand-E-Mails des Tages auf einen Blick sehen**, damit **ich nicht jede Mail einzeln öffnen muss**.

- Als **Logistikmitarbeiter** möchte ich **dass Dokumente automatisch der richtigen Sendung zugeordnet werden**, damit **ich keine Dokumente verwechsle**.

- Als **Logistikmitarbeiter** möchte ich **dass das Druckset automatisch nach Carrier vorausgewählt wird**, damit **ich nicht jedes Mal überlegen muss welche Dokumente gedruckt werden müssen**.

- Als **Logistikmitarbeiter** möchte ich **alle Dokumente eines Carriers mit einem Klick drucken**, damit **der Druckvorgang schnell geht und ich keine Sendung vergesse**.

- Als **Logistikmitarbeiter** möchte ich **eine Unterschrift pro Carrier erfassen**, damit **der Fahrer nur einmal unterschreiben muss und nicht für jedes Paket einzeln**.

- Als **Teamleader** möchte ich **sehen welche Sendungen noch offen, gedruckt oder abgeschlossen sind**, damit **ich den Tagesstatus im Blick habe**.

- Als **Teamleader** möchte ich **archivierte Lieferscheine mit Unterschrift nachschlagen können**, damit **ich bei Rückfragen einen Nachweis habe**.

- Als **Kurierfahrer** möchte ich **einmal für alle meine Sendungen unterschreiben**, damit **die Abholung schnell geht**.

---

## 6. Nicht im Scope

- **Keine Paketverfolgung** – Das Modul trackt keine Sendungen nach Abholung. Tracking ist Sache der Carrier-Portale.
- **Kein ERP/WMS-Anbindung** – Keine direkte Integration mit SAP oder anderen Systemen. Die E-Mail bleibt der Eingabekanal.
- **Kein Etikettendruck auf Spezialdrucker** – Labels werden auf normalem Papier gedruckt (wie heute). Kein Thermolabeldruck.
- **Keine Carrier-API-Integration** – Kein automatisches Buchen von Abholungen oder Sendungserstellung über Carrier-APIs.
- **Keine automatische Paket-Zuordnung** – Die physische Zuordnung Versandtasche → Karton bleibt manuell.

---

## 7. Technische Rahmenbedingungen

| Aspekt | Anforderung / Präferenz |
|---|---|
| Platform | Windows Desktop (Erweiterung von HandOver) |
| Stack | Tauri 2.0 + Vue 3 + FastAPI + SQLite (identisch mit HandOver) |
| E-Mail-Zugang | IMAP via MSAL OAuth (dediziertes Outlook-Postfach) |
| PDF-Handling | Bestehende HandOver-Engine (Download, Anzeige, Druck, Signatur) |
| Nutzeranzahl | 1–5 Mitarbeiter pro Standort |
| Tagesvolumen | 3–15 Kuriersendungen pro Tag |
| Wartung | Adam (Solo-Entwickler) |
| Integration | Mode-Switch in der Header-Leiste ("LKW-Verladung" ↔ "Kurier") mit kühlem Blau als Akzentfarbe für den Kurier-Modus (Kontrast zum Sakura-Rosa des LKW-Modus) |
| Carrier-Verwaltung | Flexibel/konfigurierbar — neue Carrier mit eigenem Druckset sollen einfach hinzufügbar sein |

---

## 8. Geklärte Fragen

| Frage | Antwort |
|---|---|
| Carrier-Erkennung | Über Betreff oder Dateinamen — beides auswerten |
| E-Mail-Absender | Verschiedene Personen — Postfach selbst ist der Filter |
| Modul-Integration | Mode-Switch mit eigenem Farbschema pro Modus |
| Tagesvolumen | 3–15 Sendungen pro Tag |
| TNT / FedEx | Zusammenfassen zu einer Carrier-Gruppe, aber Drucksets bleiben unterschiedlich |
| Lieferschein bearbeiten | Nein — PDF wird direkt verwendet wie angeliefert |

## 9. Offene Fragen

Alle Fragen geklärt — keine offenen Punkte mehr.

### Zusätzlich geklärte Design-Entscheidungen

| Frage | Antwort |
|---|---|
| Farbschema Kurier-Modus | Kühles Blau als Kontrast zum bestehenden Sakura-Rosa des LKW-Modus |
| Mode-Switch Platzierung | Header-Leiste (oben), immer sichtbar und erreichbar |
| Weitere Carrier | Unsicher — Carrier-Liste flexibel/konfigurierbar bauen, damit neue Carrier (GLS, DPD, Post etc.) einfach hinzugefügt werden können inkl. eigenem Druckset |

---

## 10. Nächste Schritte

- [ ] Konzept reviewen und offene Fragen klären
- [ ] Technische Architektur ausarbeiten → *app-architecture Skill*
- [ ] UI/Design festlegen → *app-ui-design Skill*
- [ ] Entwicklung starten → *app-dev-tracker Skill*

---

*Erstellt mit dem app-concept Skill · 01.05.2026*
