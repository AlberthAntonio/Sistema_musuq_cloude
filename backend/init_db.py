"""
Script para inicializar la base de datos y crear usuario admin.
Ejecutar una vez: python init_db.py
"""
import sys
import os
from datetime import date

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import Base, engine, SessionLocal
import app.models  # importa y registra todos los modelos, incluido DocenteCurso
from app.models.usuario import Usuario
from app.models.alumno import Alumno
from app.models.asistencia import Asistencia
from app.models.periodo import PeriodoAcademico
from app.core.security import get_password_hash


def init_database():
    """Crea todas las tablas en la base de datos."""
    print("🔧 Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas correctamente.")


def create_admin_user():
    """Crea el usuario administrador por defecto."""
    db = SessionLocal()
    
    try:
        # Verificar si ya existe
        admin = db.query(Usuario).filter(Usuario.username == "admin").first()
        
        if admin:
            print("ℹ️  El usuario admin ya existe.")
            return
        
        # Crear admin
        admin = Usuario(
            username="admin",
            email="admin@musuq.local",
            nombre_completo="Administrador del Sistema",
            rol="admin",
            hashed_password=get_password_hash("admin123"),
            activo=True
        )
        
        db.add(admin)
        db.commit()
        
        print("✅ Usuario admin creado.")
        print("   Usuario: admin")
        print("   Contraseña: admin123")
        print("   ⚠️  ¡Cambia la contraseña en producción!")
        
    finally:
        db.close()


def create_default_periodo():
    """Crea el periodo académico activo por defecto."""
    db = SessionLocal()
    
    try:
        # Verificar si ya existe un periodo activo
        periodo = db.query(PeriodoAcademico).filter(
            PeriodoAcademico.estado == "activo"
        ).first()
        
        if periodo:
            print(f"ℹ️  Ya existe un periodo activo: {periodo.nombre}")
            return
        
        # Crear periodo por defecto (4 meses)
        periodo = PeriodoAcademico(
            nombre="2026-I",
            tipo="semestral",
            fecha_inicio=date(2026, 3, 1),
            fecha_fin=date(2026, 6, 30),
            estado="activo"
        )
        
        db.add(periodo)
        db.commit()
        
        print(f"✅ Periodo académico creado: {periodo.nombre} (activo)")
        
    finally:
        db.close()


def main():
    print("\n" + "="*50)
    print("   SISTEMA MUSUQ CLOUD - INICIALIZACIÓN")
    print("="*50 + "\n")
    
    init_database()
    create_admin_user()
    create_default_periodo()
    
    print("\n" + "="*50)
    print("   ✅ INICIALIZACIÓN COMPLETA")
    print("="*50)
    print("\nPuedes iniciar el servidor con:")
    print("   uvicorn main:app --reload\n")


if __name__ == "__main__":
    main()

