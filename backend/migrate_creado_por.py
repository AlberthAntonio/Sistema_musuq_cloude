"""
Migración: agregar columna 'creado_por' a tablas existentes.
Ejecutar una vez: python migrate_creado_por.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.db.database import engine


# Tablas que necesitan la columna 'creado_por'
TABLAS = [
    "alumnos",
    "periodos_academicos",
    "matriculas",
    "obligaciones_pago",
    "pagos",
]


def columna_existe(conn, tabla: str, columna: str) -> bool:
    """Verificar si una columna ya existe en la tabla (SQLite)."""
    result = conn.execute(text(f"PRAGMA table_info({tabla})"))
    columnas = [row[1] for row in result.fetchall()]
    return columna in columnas


def migrar():
    print("\n" + "=" * 50)
    print("   MIGRACIÓN: Agregar 'creado_por'")
    print("=" * 50 + "\n")

    with engine.connect() as conn:
        for tabla in TABLAS:
            if columna_existe(conn, tabla, "creado_por"):
                print(f"  ℹ️  {tabla}.creado_por ya existe, omitiendo.")
            else:
                conn.execute(text(
                    f"ALTER TABLE {tabla} ADD COLUMN creado_por INTEGER REFERENCES usuarios(id)"
                ))
                print(f"  ✅ {tabla}.creado_por agregada.")
        
        conn.commit()

    print("\n" + "=" * 50)
    print("   ✅ MIGRACIÓN COMPLETA")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    migrar()
