#!/usr/bin/env python3
"""
Script para verificar todas las conexiones de la API.
Ejecutar: python verificar_conexiones.py
"""

import sys
import os
from pathlib import Path

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

def verificar_imports():
    """Verificar que todos los módulos principales se pueden importar"""
    print("🔍 Verificando imports de módulos principales...")
    
    try:
        from app.core.config import settings
        print("✅ app.core.config - OK")
    except Exception as e:
        print(f"❌ app.core.config - ERROR: {e}")
        return False
    
    try:
        from app.db.database import engine, SessionLocal, Base
        print("✅ app.db.database - OK")
    except Exception as e:
        print(f"❌ app.db.database - ERROR: {e}")
        return False
    
    try:
        from app.models import (
            Usuario, Alumno, Asistencia, Curso, MallaCurricular,
            Docente, Horario, EventoCalendario, ListaGuardada,
            SesionExamen, Nota, Pago
        )
        print("✅ app.models - OK")
    except Exception as e:
        print(f"❌ app.models - ERROR: {e}")
        return False
    
    try:
        from app.schemas import (
            alumno, asistencia, auth, curso, docente,
            evento, horario, lista, nota, pago, sesion
        )
        print("✅ app.schemas - OK")
    except Exception as e:
        print(f"❌ app.schemas - ERROR: {e}")
        return False
    
    try:
        from app.services import (
            alumno_service, asistencia_service, auth_service,
            curso_service, docente_service, evento_service,
            horario_service, lista_service, nota_service,
            pago_service, sesion_service, usuario_service
        )
        print("✅ app.services - OK")
    except Exception as e:
        print(f"❌ app.services - ERROR: {e}")
        return False
    
    try:
        from app.api.routes import (
            auth, usuarios, alumnos, asistencia, health,
            cursos, docentes, horarios, eventos, listas, notas, pagos, sesiones
        )
        print("✅ app.api.routes - OK")
    except Exception as e:
        print(f"❌ app.api.routes - ERROR: {e}")
        return False
    
    return True


def verificar_fastapi():
    """Verificar que FastAPI se puede inicializar"""
    print("\n🔍 Verificando inicialización de FastAPI...")
    
    try:
        from main import app
        print("✅ main.app - OK")
        print(f"   - Rutas registradas: {len(app.routes)}")
        return True
    except Exception as e:
        print(f"❌ main.app - ERROR: {e}")
        return False


def verificar_db():
    """Verificar conexión a la base de datos"""
    print("\n🔍 Verificando conexión a la base de datos...")
    
    try:
        from app.db.database import SessionLocal
        db = SessionLocal()
        
        # Intentar consulta simple
        result = db.execute("SELECT 1")
        db.close()
        
        print("✅ Conexión a BD - OK")
        return True
    except Exception as e:
        print(f"❌ Conexión a BD - ERROR: {e}")
        return False


def main():
    """Función principal"""
    print("=" * 60)
    print("  VERIFICACIÓN DE CONEXIONES - Sistema Musuq Cloud")
    print("=" * 60)
    
    # Paso 1: Verificar imports
    if not verificar_imports():
        print("\n❌ Fallo en imports. No se puede continuar.")
        sys.exit(1)
    
    # Paso 2: Verificar FastAPI
    if not verificar_fastapi():
        print("\n❌ Fallo en FastAPI. Verifica la configuración.")
        sys.exit(1)
    
    # Paso 3: Verificar DB
    if not verificar_db():
        print("\n⚠️  Conexión a BD falló. Verifica la configuración.")
    
    print("\n" + "=" * 60)
    print("✅ VERIFICACIÓN COMPLETADA CON ÉXITO")
    print("=" * 60)
    print("\n📌 Para iniciar el servidor:")
    print("   uvicorn main:app --reload --port 8000")
    print("\n📌 API disponible en:")
    print("   Swagger UI: http://localhost:8000/docs")
    print("   ReDoc: http://localhost:8000/redoc")


if __name__ == "__main__":
    main()
