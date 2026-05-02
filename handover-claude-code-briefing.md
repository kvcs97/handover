# HandOver – Claude Code Briefing
**Stand:** 22. April 2026 · **Version:** v1.6.4  
**Repo:** `kvcs97/handover` (GitHub)

---

## Projekt-Kontext

HandOver ist eine **Tauri 2.0 Desktop-App (Windows)** für Lagerlogistik-Warenausgangsprozesse bei Industrieunternehmen (Pilot: medmix Switzerland AG).

**Stack:**
- Frontend: Vue 3 (Composition API) — `src/`
- Backend: FastAPI + Python — `backend/`
- Datenbank: SQLite — `~/.handover/handover.db`
- Desktop-Bridge: Tauri 2.0 + `tauri-plugin-shell`
- Auth: Lokale Benutzer mit Rollen (`admin` / `user`), JWT
- PDF-Verarbeitung: pymupdf / fitz
- Outlook-Integration: MSAL Device Flow, XOAUTH2, IMAP

**Workflow der App:**
Referenz eingeben → PDFs via Outlook-IMAP suchen & herunterladen → Auswahl drucken → Unterschrift auf Canvas zeichnen → Unterschrift ins PDF einbrennen → Archivieren

**Wichtige Regeln:**
- Immer zuerst die relevanten Dateien lesen bevor Änderungen gemacht werden
- Minimale, gezielte Diffs — keine vollständigen Rewrites
- Keine hardcodierten Pfade — Konfiguration kommt aus Settings/DB

---

## Aktueller Stand

| Phase | Fortschritt |
|---|---|
| Setup & Infrastruktur | 9/10 (90%) — Sidecar wartet auf IT-Freigabe |
| Auth & Benutzerverwaltung | 5/5 (100%) ✅ |
| Kernworkflow | 12/13 (92%) |
| Outlook / E-Mail | 11/11 (100%) ✅ |
| Einstellungen | 6/8 (75%) |
| Lizenz | 5/5 (100%) ✅ |
| UI / Design | 10/10 (100%) ✅ |
| Testing & Deployment | 4/7 (57%) |
| **Gesamt** | **55/63 (87%)** |

---

## 🔴 TODO 1 — PDF Signatur-Einbettung fixen (Bug v1.6.4)

**Priorität: Kritisch** — Kernfunktion der App

### Problem
Die Unterschrift wird im Canvas korrekt angezeigt, aber **nicht ins archivierte PDF eingebettet**. Der Burn-in schlägt still fehl.

### Debug-Reihenfolge

**Schritt 1 — Canvas-Export prüfen (Frontend)**
```
Datei: SignatureModal.vue oder Handover.vue

canvas.toDataURL('image/png') in der Console loggen.
Ist der String leer oder nur "data:image/png;base64,"?
→ Ja: Canvas wird zu früh exportiert (vor dem Zeichnen)
→ Nein: weiter zu Schritt 2
```

**Schritt 2 — Request-Payload prüfen (DevTools Network Tab)**
```
Request an /handover/sign oder /archive inspizieren.
Ist das Feld "signature" / "signature_data" im Body vorhanden und nicht leer?
→ Fehlt: Frontend sendet Base64 nicht korrekt mit
→ Vorhanden: weiter zu Schritt 3
```

**Schritt 3 — Backend Signature-Service debuggen**
```
Datei: backend/services/signature.py (oder equivalent)

try/except um den fitz-Block ergänzen, Fehler explizit loggen.
Häufigster Fehler: Base64-Header wird nicht abgeschnitten:

  # FALSCH:
  img_data = base64.b64decode(signature_b64)

  # RICHTIG:
  img_data = base64.b64decode(signature_b64.split(",")[1])

Test:
  import base64, io
  from PIL import Image
  img = Image.open(io.BytesIO(img_data))
  # Exception hier → Base64 ist korrupt
```

**Schritt 4 — Koordinaten prüfen**
```
Aktuelle Zielposition: x=51, y=448 (355pt von oben auf A4)
A4 in fitz = 595 x 842 pt

page.rect ausgeben — Koordinaten müssen innerhalb liegen.
```

**Schritt 5 — Save-Reihenfolge prüfen**
```
doc.save(output_path) muss NACH dem Einbetten aufgerufen werden.
Nicht doc.save(input_path) — Quelldatei nie überschreiben.
output_path muss die archivierte Zieldatei sein, nicht die temporäre.
```

**Schritt 6 — Minimaler Reproduktionstest**
```
Festes Test-PNG (nicht vom Canvas) direkt per fitz einbetten.
Wenn das funktioniert → Problem liegt im Canvas-Export oder Base64-Transfer.
Wenn das auch fehlschlägt → Problem liegt im fitz-Service selbst.
```

---

## 🟡 TODO 2 — Drucker-Picker Modal (Verbesserung)

**Priorität: Mittel**

### Problem
Druckername muss aktuell manuell eingetippt werden — fehleranfällig.

### Erwartetes Verhalten
Klick auf Drucker-Feld → Modal öffnet sich mit allen installierten Druckern → Klick auf Eintrag → Name übernommen.

### Umsetzung

**Backend:** Kein Aufwand — `GET /settings/printers` existiert bereits und gibt alle lokalen + Netzwerkdrucker zurück (win32print, v1.6.4).

**Frontend — Settings.vue (Drucker-Karte):**
```vue
<!-- Textfeld ersetzen durch: -->
<div class="printer-field">
  <span class="printer-display">
    {{ selectedPrinter || 'Kein Drucker gewählt' }}
  </span>
  <button class="btn-secondary" @click="showPrinterPicker = true">
    Auswählen
  </button>
</div>

<PrinterPickerModal
  v-if="showPrinterPicker"
  @select="onPrinterSelected"
  @close="showPrinterPicker = false"
/>
```

**Neue Datei: `src/components/PrinterPickerModal.vue`**
```vue
<script setup>
import { ref, computed, onMounted } from 'vue'
const emit = defineEmits(['select', 'close'])

const printers = ref([])
const search = ref('')

onMounted(async () => {
  const res = await fetch('/settings/printers', { headers: { Authorization: ... } })
  printers.value = await res.json()
})

const filtered = computed(() =>
  printers.value.filter(p =>
    p.name.toLowerCase().includes(search.value.toLowerCase())
  )
)

function select(name) {
  emit('select', name)
  emit('close')
}
</script>

<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-card">
      <h3>Drucker auswählen</h3>
      <input v-model="search" placeholder="Drucker suchen..." class="search-input" />
      <ul class="printer-list">
        <li v-for="p in filtered" :key="p.name" @click="select(p.name)">
          <span>{{ p.name }}</span>
          <span class="badge" :class="p.type">{{ p.type }}</span>
        </li>
      </ul>
      <button class="btn-ghost" @click="$emit('close')">Abbrechen</button>
    </div>
  </div>
</template>
```

**Styling:** Konsistent mit anderen Modals in der App (Sakura-Design, `#c0546a` Akzentfarbe, Instrument Serif / DM Sans).

---

## ⏳ Weitere offene Tasks (nach den obigen)

| Task | Beschreibung | Abhängigkeit |
|---|---|---|
| `4.5` Testdruck | Echter Netzwerkdrucker nötig | vor Ort bei medmix |
| `4.6` Outlook /test-Endpoint | XOAUTH2-Fix im Verbindungstest | — |
| `7.1` Pilot medmix | Installation + vollständiger Test | AppLocker IT-Freigabe |
| `7.3` Netzwerkdrucker-Test | Live-Test vor Ort | bei medmix |
| `7.7` Bezahlter Kunde | medmix → erste Rechnung | nach Pilot |

---

## 🔴 Offener Blocker (extern)

**AppLocker IT-Freigabe bei medmix**
- v1.5.7 enthält den Tauri Sidecar-Fix (Backend als `externalBin` statt standalone `.exe`)
- Windows/AppLocker blockiert aktuell den Backend-Sidecar
- Freigabe muss von der medmix IT erteilt werden — kein technischer Workaround möglich
- Sobald Freigabe da: Tasks 7.1 + 7.3 + 4.5 in einem Termin abarbeiten

---

## Bekannte Entscheidungen & Constraints

| Thema | Entscheidung |
|---|---|
| Outlook Auth | MSAL Device Flow + XOAUTH2 (BasicAuth gesperrt) |
| Azure Authority | `/consumers` Endpoint (persönliche MS-Konten) |
| Client ID | `030d437c-961a-49a4-b088-f2f493d9b71d` |
| Install-Modus | `currentUser` (AppData\Local) — kein Admin nötig |
| Lizenz | HMAC-SHA256, lokal in `~/.handover/licenses.json` |
| PDF-Signatur-Position | x=51, y=448 / 355pt von oben (medmix Lieferschein-Layout) |
| Archiv-Pfad | Konfigurierbar via Settings, Default `%USERPROFILE%\.handover\archive\` |
| Globale Settings | `GET/PUT /settings/global` — Admin schreibt, alle lesen |
| Doppelte Referenzen | `get_unique_reference()` vergibt `_2`, `_3` Suffix |

---

*Briefing Stand: 22. April 2026 · Nächste Priorität: PDF Signatur-Burn-in fixen*
