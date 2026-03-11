# HandOver — Auto-Updater Setup

Der Updater läuft über GitHub Releases — kostenlos, kein eigener Server.

---

## Schritt 1: GitHub Repository erstellen

1. Gehe auf **github.com** und erstelle ein neues Repository: `handover`
2. Kann **privat** sein — Releases sind trotzdem öffentlich abrufbar

---

## Schritt 2: Signing Keys generieren

Tauri signiert jeden Update damit niemand gefälschte Updates einschleusen kann.

```powershell
# Im frontend/ Ordner:
npm run tauri signer generate -- -w ../updater_key.key

# Du siehst:
# Private key: updater_key.key  (GEHEIM halten!)
# Public key:  dxxx...          (kommt in tauri.conf.json)
```

Den **Public Key** in `tauri.conf.json` eintragen:
```json
"plugins": {
  "updater": {
    "pubkey": "HIER_DEN_PUBLIC_KEY_EINTRAGEN",
    ...
  }
}
```

Den **Private Key** als GitHub Secret speichern:
- GitHub Repository → Settings → Secrets → Actions
- Name: `TAURI_SIGNING_PRIVATE_KEY`
- Value: Inhalt der `updater_key.key` Datei

---

## Schritt 3: GitHub Actions Workflow erstellen

Erstelle die Datei `.github/workflows/release.yml` im `handover/` Ordner:

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install Rust
        uses: dtolnay/rust-toolchain@stable

      - name: Install Python dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Build Python backend
        run: |
          cd backend
          pip install pyinstaller
          pyinstaller --onefile --name handover-backend main.py
          copy dist\handover-backend.exe ..\frontend\src-tauri\

      - name: Install frontend dependencies
        run: |
          cd frontend
          npm install

      - name: Build Tauri app
        uses: tauri-apps/tauri-action@v0
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          TAURI_SIGNING_PRIVATE_KEY: ${{ secrets.TAURI_SIGNING_PRIVATE_KEY }}
        with:
          projectPath: frontend
          tagName: ${{ github.ref_name }}
          releaseName: "HandOver ${{ github.ref_name }}"
          releaseBody: "Neue Version von HandOver"
          releaseDraft: false
```

---

## Schritt 4: Update ausrollen

```powershell
# Version in src-tauri/tauri.conf.json erhöhen:
# "version": "1.0.1"

# Git Tag erstellen und pushen:
git add .
git commit -m "Version 1.0.1"
git tag v1.0.1
git push origin main --tags
```

GitHub Actions baut automatisch den Installer und erstellt ein Release.
Die App prüft beim nächsten Start ob ein Update verfügbar ist und zeigt den Banner.

---

## tauri.conf.json — GitHub URL anpassen

```json
"endpoints": [
  "https://github.com/DEIN_GITHUB_USERNAME/handover/releases/latest/download/latest.json"
]
```

`DEIN_GITHUB_USERNAME` durch deinen echten GitHub Username ersetzen.
