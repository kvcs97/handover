# HandOver – Bugfix & Improvement Tasks
**Erstellt:** 2026-04-22  
**Für:** Claude Code  
**Stack:** Tauri 2.0 · Vue 3 · FastAPI · SQLite  
**Priorität:** Hoch → Mittel → Niedrig

---

## Kontext für Claude Code

HandOver ist eine Tauri 2.0 Desktop-App (Windows) für Lagerlogistik-Warenausgangsprozesse.
- Frontend: Vue 3 (Composition API, `src/`)
- Backend: FastAPI Python (`backend/`)
- Datenbank: SQLite (lokale `.db`-Datei)
- Auth: Lokale Benutzer-Logins mit Rollen (`admin`, `user`)
- Relevante Views: `Settings.vue`, `Archive.vue`, `SignatureModal.vue`, Drucker-Komponente

Lies zuerst die relevanten Dateien bevor du Änderungen machst. Mache minimale, gezielte Diffs — keine vollständigen Rewrites.

---

## 🔴 PRIORITÄT 1 — Admin-Einstellungen gelten global für alle Benutzer

### Problem
Wenn ein Admin Einstellungen speichert (Firmendaten, Archivordner, Drucker, Datenquelle inkl. Outlook-Profil), gelten diese nur für den eigenen Account. Alle anderen Benutzer müssen dieselben Einstellungen nochmals manuell setzen.

### Erwartetes Verhalten
- Einstellungen die ein **Admin** speichert → werden in eine **globale/systemweite Tabelle** geschrieben
- Alle anderen Benutzer lesen diese globalen Werte automatisch
- Wenn ein Outlook-Profil als Datenquelle hinterlegt wurde → gilt automatisch als **Standard-Datenquelle** für jeden Benutzer beim Login
- Benutzer (Nicht-Admins) sehen die Einstellungen als read-only oder können sie nicht überschreiben

### Umsetzung

**Backend (`backend/`):**
```
1. In der SQLite-DB eine Tabelle `global_settings` erstellen (falls nicht vorhanden):
   - key TEXT PRIMARY KEY
   - value TEXT
   - updated_by TEXT
   - updated_at DATETIME

2. Neuer FastAPI-Endpoint: PUT /settings/global
   - Nur zugänglich wenn user.role == "admin"
   - Schreibt alle Felder (Firmendaten, Archivordner, Drucker, Datenquelle) in global_settings

3. Neuer FastAPI-Endpoint: GET /settings/global
   - Gibt alle globalen Einstellungen zurück (für alle Benutzer lesbar)

4. Beim Login / App-Start:
   - global_settings laden
   - Wenn "datasource_type" == "outlook" → als aktive Datenquelle für die Session setzen
```

**Frontend (`Settings.vue`):**
```
1. Beim Laden der Seite: GET /settings/global aufrufen, Felder befüllen
2. Speichern-Button:
   - Wenn eingeloggter User role == "admin" → PUT /settings/global
   - Wenn role == "user" → Felder als disabled anzeigen, kein Speichern möglich
3. Hinweis-Text einblenden: "Diese Einstellungen gelten für alle Benutzer"
   (nur sichtbar für Admins)
```

**Migration:**
```
Bestehende user-spezifische Einstellungen des ersten Admin-Accounts
in global_settings kopieren (einmalige Migration beim App-Start prüfen).
```

---

## 🔴 PRIORITÄT 2 — PDF-Icon im Archivfenster ist nicht klickbar

### Problem
Im Archivfenster (`Archive.vue`) gibt es bei bereits archivierten Abholungen ganz rechts ein PDF-Icon. Ein Klick darauf löst keine Aktion aus.

### Erwartetes Verhalten
Klick auf das PDF-Icon → öffnet die archivierte PDF-Datei (lokal, mit dem Standard-PDF-Viewer des Systems)

### Umsetzung

**Frontend (`Archive.vue`):**
```
1. Suche die Tabellen-Zeilen-Komponente mit dem PDF-Icon
2. Prüfe ob ein @click / v-on:click Handler vorhanden ist
   → Falls nein: Handler hinzufügen

3. Handler-Logik:
   async function openArchivedPdf(archiveEntry) {
     const filePath = archiveEntry.pdf_path  // oder equivalent field
     await invoke('open_file', { path: filePath })
     // Tauri shell.open() oder custom command
   }
```

**Backend / Tauri (`src-tauri/`):**
```
1. Prüfe ob ein Tauri-Command "open_file" oder äquivalent existiert
2. Falls nicht: in main.rs / commands.rs hinzufügen:

   #[tauri::command]
   fn open_file(path: String) -> Result<(), String> {
     opener::open(&path).map_err(|e| e.to_string())
   }
   // Crate: "opener" in Cargo.toml hinzufügen falls nicht vorhanden
   // Alternative: tauri::api::shell::open()

3. Command in tauri::Builder registrieren (.invoke_handler)
```

**Fallback falls Pfad nicht mehr existiert:**
```
- Fehlermeldung anzeigen: "Datei nicht mehr vorhanden: [Pfad]"
- Icon als disabled stylen wenn pdf_path null/leer ist
```

---

## 🟡 PRIORITÄT 3 — Nicht-Netzwerkdrucker in der Druckerauswahl verfügbar machen

### Problem
In der Druckerauswahl werden nur Netzwerkdrucker angezeigt. Lokal angeschlossene Drucker (USB, direkt) fehlen.

### Erwartetes Verhalten
Alle auf dem Windows-System installierten Drucker werden angezeigt — Netzwerkdrucker **und** lokale Drucker.

### Umsetzung

**Backend (`backend/routers/printer.py` oder equivalent):**
```
1. Prüfe wie Drucker aktuell abgefragt werden
   → Wahrscheinlich über win32print oder subprocess mit PowerShell

2. Aktueller Filter entfernen (z.B. "Network" in printer_type o.ä.)

3. Korrekte Abfrage aller installierten Drucker:

   import win32print

   def get_all_printers():
       printers = []
       for p in win32print.EnumPrinters(
           win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS,
           None, 4
       ):
           printers.append({
               "name": p["pPrinterName"],
               "port": p.get("pPortName", ""),
               "type": "local" if "USB" in p.get("pPortName","") else "network"
           })
       return printers

   Flags:
   - PRINTER_ENUM_LOCAL        → lokal installierte Drucker
   - PRINTER_ENUM_CONNECTIONS  → Netzwerkdrucker / verbundene Drucker
   Beide Flags kombinieren um alle zu erhalten.
```

**Frontend (Druckerauswahl-Komponente):**
```
- Optional: Typ-Badge anzeigen ("Lokal" / "Netzwerk") zur besseren Übersicht
- Kein weiterer Änderungsbedarf wenn API alle Drucker zurückgibt
```

---

## 🟡 PRIORITÄT 4 — Unterschriftsfeld: eingeloggter Name + Datum + höheres Feld

### Problem
Im Unterschriftsfeld steht bei "Unterzeichnet:" kein Name des eingeloggten Mitarbeiters und kein Datum. Das Feld ist außerdem zu klein.

### Erwartetes Verhalten
- Unter dem Unterschrifts-Canvas steht automatisch:  
  `Unterzeichnet: [Vorname Nachname] – [DD.MM.YYYY]`
- Das Unterschriftsfeld (Canvas) ist ca. **2 Punkte (Einheiten)** höher als aktuell

### Umsetzung

**Frontend (`SignatureModal.vue` oder equivalent):**
```
1. Eingeloggten Benutzer aus dem Auth-Store lesen:
   const authStore = useAuthStore()
   const employeeName = computed(() =>
     `${authStore.user.firstname} ${authStore.user.lastname}`
   )

2. Aktuelles Datum formatieren:
   const today = computed(() => {
     const d = new Date()
     return d.toLocaleDateString('de-AT')  // → DD.MM.YYYY
   })

3. Im Template unter dem Canvas einfügen:
   <p class="signature-label">
     Unterzeichnet: {{ employeeName }} – {{ today }}
   </p>

4. Unterschriftsbereich nach oben verschieben:
   Den gesamten Container (Canvas + Label) um 2–3 Punkte höher positionieren.
   → CSS: margin-top: -2px / margin-top: -3px auf dem umschließenden Container
   → Oder: transform: translateY(-2px) / translateY(-3px)
   → Nicht die Canvas-Größe ändern, nur die vertikale Position des Bereichs anpassen

5. Beim Einbrennen der Unterschrift (burn-in):
   - Den Text "Unterzeichnet: [Name] – [Datum]" ebenfalls ins PDF einbrennen
   - Als separates Text-Overlay unterhalb der Unterschrift positionieren
```

**Backend (Signatur-Einbrennen, z.B. `backend/services/signature.py`):**
```
- Beim Erstellen des finalen PDFs den Signatur-Text als Annotation hinzufügen
- Name und Datum aus dem Request-Body mitübergeben (Frontend sendet beide)
- Beispiel mit pymupdf/fitz:
  page.insert_text((x, y), f"Unterzeichnet: {name} – {date}", fontsize=9)
```

---

## 🟢 PRIORITÄT 5 — Doppelte Archivierung: nicht überschreiben, sondern mit Suffix speichern

### Problem
Wenn beim Archivieren dieselbe Referenznummer / derselbe Text erneut eingegeben wird, wird der bestehende Archiveintrag überschrieben.

### Erwartetes Verhalten
- Bestehendes Archiv wird **niemals überschrieben**
- Zweiter Eintrag mit gleicher Referenz wird gespeichert als: `REFERENZNUMMER_2`
- Dritter Eintrag → `REFERENZNUMMER_3`, usw.
- Das PDF wird ebenfalls mit dem neuen Namen gespeichert

### Umsetzung

**Backend (`backend/routers/archive.py` oder equivalent):**
```
def get_unique_reference(db, base_ref: str) -> str:
    """Gibt eine eindeutige Referenz zurück, mit _2, _3 Suffix falls nötig."""
    existing = db.execute(
        "SELECT reference FROM archives WHERE reference LIKE ?",
        (f"{base_ref}%",)
    ).fetchall()

    existing_refs = {row["reference"] for row in existing}

    if base_ref not in existing_refs:
        return base_ref

    counter = 2
    while f"{base_ref}_{counter}" in existing_refs:
        counter += 1
    return f"{base_ref}_{counter}"


# Im Archivierungs-Endpoint:
@router.post("/archive")
def create_archive(payload: ArchiveCreate, db=Depends(get_db)):
    unique_ref = get_unique_reference(db, payload.reference)
    
    # PDF umbenennen falls Referenz geändert wurde
    if unique_ref != payload.reference:
        # Zieldateiname anpassen
        pdf_filename = pdf_filename.replace(payload.reference, unique_ref)
    
    # Normales Speichern mit unique_ref
    ...
```

**Frontend (Archivierungs-Formular):**
```
- Kein zusätzlicher Hinweis nötig (transparentes Verhalten)
- Optional: Toast-Meldung anzeigen wenn Suffix vergeben wurde:
  "Referenz bereits vorhanden – gespeichert als REFERENZNUMMER_2"
```

**Datenbank:**
```
- Sicherstellen dass kein UNIQUE constraint auf der reference-Spalte liegt
  (oder den Constraint entfernen falls vorhanden)
- Migration: ALTER TABLE archives ... (falls nötig)
```

---

## Zusammenfassung

| # | Fix | Priorität | Bereich |
|---|-----|-----------|---------|
| 1 | Admin-Einstellungen global für alle Benutzer | 🔴 Hoch | Backend + Settings.vue |
| 2 | PDF-Icon im Archiv klickbar machen | 🔴 Hoch | Archive.vue + Tauri |
| 3 | Nicht-Netzwerkdrucker anzeigen | 🟡 Mittel | Backend Printer-API |
| 4 | Unterschriftsfeld: Name + Datum + höher | 🟡 Mittel | SignatureModal.vue + PDF-Service |
| 5 | Doppelte Referenz nicht überschreiben | 🟢 Niedrig | Backend Archive-Endpoint |

---

*Datei für Claude Code – minimale Diffs bevorzugen, relevante Dateien zuerst lesen.*
