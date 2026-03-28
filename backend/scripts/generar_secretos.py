"""
Genera claves secretas criptográficamente seguras para el .env de producción.
Ejecutar: python scripts/generar_secretos.py
"""
import secrets

print("=" * 60)
print("  Claves secretas para producción (copiar al .env)")
print("=" * 60)
print()
print(f"SECRET_KEY={secrets.token_hex(32)}")
print(f"REFRESH_SECRET_KEY={secrets.token_hex(32)}")
print()
print("IMPORTANTE: Usar claves DIFERENTES para cada variable.")
print("Guardar en un lugar seguro. NO compartir ni subir al repo.")
print("=" * 60)
