"""
Windows DPAPI wrapper — verschlüsselt Strings an den aktuellen Windows-User gebunden.
Kein Passwort nötig; die OS-eigene Schlüsselverwaltung übernimmt die Sicherheit.

Gespeicherte Werte tragen das Prefix "DPAPI:" damit alte Klartextwerte
ohne Fehler weiterhin gelesen werden können (Rückwärtskompatibilität).
"""
import ctypes
import base64

_PREFIX = "DPAPI:"


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", ctypes.c_ulong),
        ("pbData", ctypes.POINTER(ctypes.c_char)),
    ]


def encrypt(plaintext: str) -> str:
    """Gibt einen DPAPI-verschlüsselten, Base64-codierten String zurück (mit DPAPI:-Prefix)."""
    data = plaintext.encode("utf-8")
    buf = ctypes.create_string_buffer(data, len(data))
    inp = _DataBlob(cbData=len(data), pbData=buf)
    out = _DataBlob()

    ok = ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(inp), None, None, None, None, 0, ctypes.byref(out)
    )
    if not ok:
        code = ctypes.windll.kernel32.GetLastError()
        raise RuntimeError(f"CryptProtectData fehlgeschlagen (0x{code:08X})")

    encrypted = ctypes.string_at(out.pbData, out.cbData)
    ctypes.windll.kernel32.LocalFree(out.pbData)
    return _PREFIX + base64.b64encode(encrypted).decode("ascii")


def decrypt(value: str) -> str:
    """Entschlüsselt einen mit encrypt() erstellten Wert.
    Werte ohne DPAPI:-Prefix werden unverändert zurückgegeben (Rückwärtskompatibilität)."""
    if not value or not value.startswith(_PREFIX):
        return value  # Alter Klartextwert — unverändert durchreichen

    data = base64.b64decode(value[len(_PREFIX):])
    buf = ctypes.create_string_buffer(data, len(data))
    inp = _DataBlob(cbData=len(data), pbData=buf)
    out = _DataBlob()

    ok = ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(inp), None, None, None, None, 0, ctypes.byref(out)
    )
    if not ok:
        code = ctypes.windll.kernel32.GetLastError()
        raise RuntimeError(f"CryptUnprotectData fehlgeschlagen (0x{code:08X})")

    plaintext = ctypes.string_at(out.pbData, out.cbData)
    ctypes.windll.kernel32.LocalFree(out.pbData)
    return plaintext.decode("utf-8")
