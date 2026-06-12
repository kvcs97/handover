# HandOver – PKL Übersicht Integration

**Modul:** HandOver (Haupt-App)
**Priorität:** Medium – nach AppLocker-Freigabe umsetzen
**Status:** Anforderungen definiert · noch nicht implementiert
**Erstellt:** Juni 2026 · Adam Kovacs / Shoriu

---

## Ziel

HandOver soll beim Öffnen einer Sendung automatisch anzeigen, in welcher Lagerzone und Reihe die Paletten stehen. Die Daten kommen direkt aus der PKL Übersicht App (JSONBin.io) – keine manuelle Eingabe nötig. Wenn HandOver eine Sendung archiviert, wird der entsprechende PKL-Eintrag automatisch gelöscht.

---

## Datenquelle: PKL Übersicht (JSONBin.io)

### Zugangsdaten

| Parameter | Wert |
|-----------|------|
| **Service** | JSONBin.io |
| **BIN_ID** | `6a2807caf5f4af5e29d1937c` |
| **API_KEY** | `$2a$10$Q499xwgCtri2CF3v0kc5d.47sfykEoIAs34TfnAKlxPK/HLI9B/0m` |
| **Lesen** | `GET https://api.jsonbin.io/v3/b/6a2807caf5f4af5e29d1937c/latest` |
| **Schreiben** | `PUT https://api.jsonbin.io/v3/b/6a2807caf5f4af5e29d1937c` |
| **Header (beide)** | `X-Master-Key: {API_KEY}` |
| **Content-Type (PUT)** | `application/json` |

> ⚠️ Zugangsdaten nicht hardcodiert im Quellcode speichern. Empfehlung: separate `pkl_config.json` im AppData-Verzeichnis von HandOver, analog zur bestehenden HandOver-Konfiguration.

### Datenstruktur (GET-Antwort)

```json
{
  "record": {
    "data": {
      "A": {
        "R1": { "0": "4512345", "1": "4567890" },
        "R3": { "0": "9988776" }
      },
      "B": {
        "K1": { "0": "9876543" }
      }
    },
    "config": {
      "A": { "rows": ["R1","R2","R3","R4","R5","R6","R7"] },
      "B": { "rows": ["K1","K2","K3","K4","K5","K6","K7","K8","K9","K10","K11"] },
      "C": { "rows": ["C1","C-Gang1"] },
      "D": { "rows": ["D1","D2","D3"] },
      "E": { "rows": ["E1","E2","E3","E4","E5","E6"] }
    },
    "_ts": 1718000000000
  }
}
```

**Schlüsselpunkte:**
- `record.data[Zone][Reihe][Slot]` = Lieferscheinnummer als String
- Slot-Schlüssel: `"0"` bis `"4"` (String, nicht Integer)
- Zonen: `A`, `B`, `C`, `D`, `E`
- `_ts` = Unix-Timestamp in Millisekunden (letztes Schreiben)
- Eine Sendung kann in **mehreren Reihen gleichzeitig** eingetragen sein (z.B. große Sendung aufgeteilt)

### Lookup: LS-Nummer → Lagerort(e)

Alle Ebenen von `record.data` durchlaufen:
für jede Zone → für jede Reihe → für Slots `"0"` bis `"4"`.
Wenn Wert == gesuchte LS-Nummer → Treffer: `Zone {Z} · {Reihe}`.
**Alle Treffer sammeln** (Mehrfach-Lagerort möglich).

---

## Anforderungen: Lagerort-Anzeige in HandOver

### Wo

Im Hauptfenster, **unterhalb des Sendungs-Headers** (Ladereferenz / LS-Nummer), als kompaktes Info-Banner. Erscheint nur wenn ein Treffer gefunden wird.

### Anzeige-Verhalten

| Situation | Anzeige |
|-----------|---------|
| 1 Lagerort gefunden | `📦 Lagerort: Zone A · R3` |
| Mehrere Lagerorte | `📦 Lagerort: Zone A · R3  \|  Zone B · K2` |
| Nicht eingetragen | Kein Banner (Normalfall – Sendung noch nicht eingelagert) |
| PKL nicht erreichbar | Kein Banner, kein Fehler in der UI |

### Timing

- Lookup wird ausgelöst wenn eine Sendung geöffnet oder geladen wird
- Ergebnis wird **asynchron** angezeigt – kein Blocking des UI
- Timeout: GET-Request nach 3 Sekunden abbrechen wenn keine Antwort
- Kein automatisches Polling innerhalb HandOver

---

## Anforderungen: Automatisches Löschen bei Archivierung

Wenn HandOver eine Sendung **archiviert** (Unterschrift eingebrannt + archiviert), soll der PKL-Eintrag dieser LS-Nummer automatisch gelöscht werden.

### Ablauf

1. Aktuellen JSONBin-Inhalt laden (GET latest)
2. In `record.data` alle Slots suchen, die die LS-Nummer enthalten
3. Gefundene Slots leeren (Wert entfernen)
4. Geänderten Inhalt zurückschreiben (PUT), mit aktuellem `_ts` = `Date.now()` / `time.time() * 1000`
5. Bei Fehlschlag: Warnung anzeigen (siehe Fehlerbehandlung)

### Wichtig beim Schreiben (PUT)

Der vollständige `data`- und `config`-Block muss mitgesendet werden – JSONBin überschreibt den gesamten Bin-Inhalt:

```json
{
  "data": { ... },
  "config": { ... },
  "_ts": 1718000000001
}
```

---

## Fehlerbehandlung

| Fehler | Verhalten |
|--------|-----------|
| GET schlägt fehl (Offline, Timeout) | Kein Lagerort-Banner, kein Fehler in UI |
| LS-Nummer nicht in PKL eingetragen | Kein Banner (kein Fehler) |
| PUT schlägt fehl beim Archivieren | Warnung: `"PKL-Eintrag konnte nicht gelöscht werden – bitte manuell in PKL Übersicht leeren."` |
| Timeout GET | Nach 3 Sekunden abbrechen, weiterfahren |

---

## Zonen-Referenz

| Zone | Name | Reihen |
|------|------|--------|
| A | Lange Reihen | R1 – R7 |
| B | Kurze Reihen | K1 – K11 |
| C | Blocklager gemischt | C1, C-Gang1 |
| D | Blocklager gemischt | D1 – D3 |
| E | Kleinere Sendungen | E1 – E6 |

---

## Kapazität & Limits

JSONBin Free Tier: ~10.000 Requests/Monat.
Bei 10–25 Sendungen/Tag × (1 GET Lookup + 1 PUT Löschen) = max. ~50 Requests/Tag → **weit unter dem Limit**.

---

*Erstellt: Juni 2026 · Shoriu / Adam Kovacs*
