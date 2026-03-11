import platform
import subprocess
import os

def get_printer_name(db) -> str:
    from database import Setting
    s = db.query(Setting).filter(Setting.key == "printer_name").first()
    return s.value if s and s.value else ""


def print_document(pdf_path: str, db=None, printer_name: str = None):
    # Drucker-Name laden falls nicht übergeben
    if not printer_name and db:
        printer_name = get_printer_name(db)

    # PDF muss existieren
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF nicht gefunden: {pdf_path}")

    # Kein Drucker konfiguriert → Warnung, kein Fehler
    if not printer_name or printer_name.strip() == "":
        print(f"[INFO] Kein Drucker konfiguriert — PDF gespeichert unter: {pdf_path}")
        return

    system = platform.system()

    if system == "Windows":
        # Methode 1: SumatraPDF (falls installiert) — zuverlässiger
        sumatra = r"C:\Program Files\SumatraPDF\SumatraPDF.exe"
        if os.path.exists(sumatra):
            subprocess.run([sumatra, "-print-to", printer_name, pdf_path], check=True)
        else:
            # Methode 2: Standard Windows PDF-Druck via Acrobat/Edge
            cmd = [
                "powershell", "-Command",
                f'$pdf = "{pdf_path}"; '
                f'$printer = "{printer_name}"; '
                f'$shell = New-Object -ComObject Shell.Application; '
                f'$item = $shell.Namespace(0).ParseName($pdf); '
                f'$item.InvokeVerb("Print")'
            ]
            subprocess.run(cmd, check=True, timeout=30)

    elif system == "Darwin":
        if printer_name:
            subprocess.run(["lpr", "-P", printer_name, pdf_path], check=True)
        else:
            subprocess.run(["lpr", pdf_path], check=True)

    elif system == "Linux":
        if printer_name:
            subprocess.run(["lp", "-d", printer_name, pdf_path], check=True)
        else:
            subprocess.run(["lp", pdf_path], check=True)

    else:
        raise RuntimeError(f"Betriebssystem nicht unterstützt: {system}")
