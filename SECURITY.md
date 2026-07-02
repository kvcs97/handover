# Security Policy

## Unterstützte Versionen

HandOver befindet sich in aktiver Entwicklung. Sicherheitsupdates werden ausschließlich für die **jeweils aktuellste veröffentlichte Version** bereitgestellt (siehe [Releases](../../releases)).

| Version        | Unterstützt        |
| -------------- | ------------------- |
| Aktuellste Release | ✅ |
| Ältere Versionen  | ❌ |

Wir empfehlen, den in HandOver integrierten Auto-Updater zu nutzen, um stets auf dem aktuellen Stand zu bleiben.

## Sicherheitslücke melden

Bitte meldet Sicherheitslücken **nicht** über ein öffentliches Issue.

Meldet sie stattdessen auf einem der folgenden Wege:

- **GitHub Private Vulnerability Reporting:** über den Tab [Security → Report a vulnerability](../../security/advisories/new) in diesem Repository
- **E-Mail:** shoriu@outlook.com] 

Bitte gebt in der Meldung nach Möglichkeit an:
- Betroffene Version von HandOver
- Kurze Beschreibung der Schwachstelle und potenzielle Auswirkung
- Schritte zur Reproduktion (falls vorhanden)
- Ob euch ein Proof-of-Concept vorliegt

## Was ihr erwarten könnt

- **Reaktionszeit:** Rückmeldung innerhalb von 5 Werktagen
- **Statusupdate:** Regelmäßige Rückmeldung zum Bearbeitungsstand, bis die Lücke geschlossen oder als nicht relevant eingestuft ist
- **Fix & Veröffentlichung:** Kritische Lücken werden priorisiert behoben; ein Fix wird über ein neues Release inkl. Auto-Update ausgerollt
- **Kein Bug-Bounty-Programm** — HandOver ist ein internes Tool ohne Vergütungsprogramm für Meldungen, Meldungen werden aber ernst genommen und wertgeschätzt

## Scope

Diese Policy gilt für:
- Die HandOver Desktop-Anwendung (Tauri/Vue-Frontend + FastAPI-Backend)
- Den Auto-Updater und dessen Signaturprüfung
- Die Build-/Release-Pipeline (GitHub Actions)

Nicht im Scope:
- Social-Engineering- oder Phishing-Angriffe auf Nutzer

## Bekannte Sicherheitsmaßnahmen

HandOver enthält u. a. folgende Schutzmechanismen:
- Geräte-spezifisches JWT-Secret
- DPAPI-verschlüsselte OAuth-Tokens
- Rate-Limiting beim Login (5 Versuche / 15 Min. Sperre)
- 12-Zeichen-Passwortrichtlinie mit Upgrade-Flow
- Tägliches automatisches SQLite-Backup (30 Tage Aufbewahrung)
- Signierte Auto-Updates via Tauri Updater
