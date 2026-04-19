# HandOver – Konzeptdokument

> Desktop-App für die Lagerlogistik, die den Warenausgangsprozess digitalisiert: Referenz einlesen, Versanddokumente automatisch per E-Mail holen, drucken, digital unterschreiben und archivieren.

---

## 1. Problem & Zielsetzung

In der Lagerlogistik werden Versanddokumente heute manuell gesucht, ausgedruckt und physisch unterschrieben — ein fehleranfälliger, zeitintensiver Prozess. Fahrernamen, Kennzeichen und Spediteure werden oft auf Papier erfasst und gehen verloren. Ziel von HandOver ist ein durchgängig digitaler Warenausgabeprozess der in unter 60 Sekunden abgeschlossen werden kann und alle relevanten Daten zentral archiviert.

---

## 2. Zielgruppe

| Nutzertyp | Beschreibung | Hauptbedürfnis |
|---|---|---|
| Lagerist / Disponent | Führt täglich mehrere Übergaben durch | Schnell, einfach, kein Papier |
| Teamleiter Logistik | Überwacht Übergaben, konfiguriert App | Übersicht, Kontrolle, Reportings |
| IT-Administrator | Installiert und wartet die App | Einfache Deployment, keine Serverinfrastruktur |
| Fahrer / Spediteur | Unterschreibt das Übergabedokument | Klarer Prozess, schnelle Abfertigung |

---

## 3. Kernfunktionen (MVP)

- **Referenz einlesen** — Manuelle Eingabe, Barcode-Scanner oder QR-Code kompatibel
- **E-Mail-Suche** — Automatische Suche nach Versanddokumenten im Outlook-Posteingang (OAuth2 IMAP)
- **PDF-Auswahl & Vorschau** — Alle gefundenen PDFs anzeigen, Vorschau öffnen, Unterschrift-Pflicht pro PDF wählbar
- **Drucken** — Direktdruck an konfigurierten Netzwerkdrucker
- **Digitale Unterschrift** — Canvas-Zeichenfläche (Touch + Maus), Unterschrift wird in PDF eingebettet
- **Archivierung** — Unterschriebenes PDF lokal gespeichert mit Timestamp und Fahrerdaten
- **Spediteur-Verwaltung** — Datenbank mit Autocomplete, automatisches Anlegen neuer Spediteure
- **Mehrbenutzer** — Admin- und Viewer-Rollen, JWT-Login pro Mitarbeiter
- **SetupWizard** — Geführte Ersteinrichtung (Firma, Drucker, Datenquelle, Admin-Account)

---

## 4. Erweiterungen (Phase 2+)

- Sōmei-Integration (Operational Intelligence)
- Statistiken und Exportfunktion (CSV, PDF-Report)
- Mehrere Standorte / Mandanten
- Mobile Companion App für Fahrer
- SAP/ERP-Direktanbindung als Datenquelle
- E-Mail-Rückversand des unterschriebenen PDFs

---

## 5. User Stories

- Als **Lagerist** möchte ich eine Referenznummer einlesen, damit die App automatisch die zugehörigen Dokumente findet.
- Als **Lagerist** möchte ich PDFs direkt vorschauen, damit ich das richtige Dokument identifiziere.
- Als **Lagerist** möchte ich die Unterschrift des Fahrers digital erfassen, damit ich kein Papier mehr brauche.
- Als **Lagerist** möchte ich dass das unterschriebene PDF automatisch archiviert wird, damit ich später darauf zugreifen kann.
- Als **Teamleiter** möchte ich Benutzerkonten anlegen und verwalten, damit jeder Mitarbeiter seinen eigenen Login hat.
- Als **Teamleiter** möchte ich den Drucker und die E-Mail-Quelle konfigurieren, damit die App mit der Firmeninfrastruktur arbeitet.
- Als **Teamleiter** möchte ich alle vergangenen Übergaben im Archiv einsehen, damit ich Nachweise vorlegen kann.
- Als **IT-Administrator** möchte ich die App ohne Adminrechte installieren, damit ich keine IT-Freigaben brauche.
- Als **Fahrer** möchte ich schnell und klar auf dem Bildschirm unterschreiben, damit meine Abfertigung zügig geht.

---

## 6. Nicht im Scope

- Cloud-Synchronisation oder zentraler Server
- Mobile App (nur Desktop Windows)
- Eigene E-Mail-Verwaltung (nur Lesen, kein Senden — ausser Rückversand in Phase 2)
- Rechnungsstellung oder Faktura-Funktionen
- Mehrsprachigkeit (nur Deutsch)
- Browser-Version

---

## 7. Technische Rahmenbedingungen

| Aspekt | Anforderung / Präferenz |
|---|---|
| Platform | Windows 10/11 Desktop (64-bit) |
| Nutzeranzahl | 1–20 pro Installation |
| Bestehende Systeme | Microsoft Outlook (IMAP OAuth2), Netzwerkdrucker |
| Offline-fähigkeit | Ja — alle Daten lokal, kein Internet für Kernfunktionen |
| Admin-Rechte | Nicht erforderlich (currentUser Install) |
| Wartung | Adam Kovacs / Shoriu, Auto-Updater integriert |
| Lizenzierung | Lizenzschlüssel pro Installation (HMAC-SHA256) |

---

## 8. Offene Fragen

- [ ] E-Mail-Suche findet nach OAuth2-Login keine E-Mails — Token-Übergabe an IMAP prüfen
- [ ] Settings-Felder (Outlook) leeren sich nach Reload — loadSettings() Fix ausstehend
- [ ] Auto-Updater vollständig testen (v1.5.0 → v1.5.1)
- [ ] Testdruck mit echtem Netzwerkdrucker noch ausstehend
- [ ] Ersten Lizenzschlüssel für medmix generieren

---

## 9. Nächste Schritte

- [ ] E-Mail-Suche debuggen (Token-Format / IMAP OAuth2)
- [ ] Settings Reload Fix deployen
- [ ] Auto-Updater Test abschliessen
- [ ] medmix Pilot als bezahlten Kunden konvertieren
- [ ] Architektur-Dokument → *handover-architecture.md*
- [ ] UI/Design-Dokument → *handover-ui-design.md*

---

*Erstellt mit dem app-concept Skill · April 2026*
