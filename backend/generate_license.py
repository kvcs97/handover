"""
Lizenzschlüssel Generator — nur für dich als Shoriu-Gründer
Ausführen: python generate_license.py
"""
from services.license_service import generate_license, validate_license

print("=" * 50)
print("HandOver — Lizenzschlüssel Generator")
print("=" * 50)

name  = input("Kundenname: ").strip()
email = input("E-Mail:     ").strip()
plan  = input("Plan (essential/complete): ").strip() or "essential"
days  = input("Gültig für (Tage, Standard 365): ").strip()
days  = int(days) if days else 365
users = input("Max. Benutzer (Standard 5): ").strip()
users = int(users) if users else 5

key = generate_license(name, email, plan, days, users)

print("\n" + "=" * 50)
print(f"Lizenzschlüssel: {key}")
print("=" * 50)

# Validierung zur Kontrolle
result = validate_license(key)
print(f"\nValidierung: {'✓ Gültig' if result['valid'] else '✗ Fehler'}")
if result["valid"]:
    print(f"Plan:       {result['plan']}")
    print(f"Läuft ab:   {result['expires']}")
    print(f"Benutzer:   {result['max_users']}")
