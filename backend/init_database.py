"""
Script para inicializar la base de datos y crear usuario admin.
Ejecutar: python init_database.py
"""
import sys
sys.path.insert(0, '.')

from app.db.database import init_db, SessionLocal
from app.models.usuario import Usuario
from app.core.security import get_password_hash


def crear_usuario_admin():
    """Crea el usuario administrador inicial."""
    db = SessionLocal()
    
    try:
        # Verificar si ya existe
        admin = db.query(Usuario).filter(Usuario.username == "admin").first()
        
        if admin:
            print("⚠️  Usuario admin ya existe")
            return
        
        # Crear usuario admin
        admin = Usuario(
            username="admin",
            email="admin@musuq.local",
            nombre_completo="Administrador",
            rol="admin",
            hashed_password=get_password_hash("admin123"),
            activo=True
        )
        
        db.add(admin)
        db.commit()
        
        print("✅ Usuario admin creado exitosamente")
        print("   Username: admin")
        print("   Password: admin123")
        print("   ⚠️  Cambiar contraseña en producción!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    print("=" * 50)
    print("🚀 Inicializando Base de Datos - Musuq Cloud")
    print("=" * 50)
    
    # Crear tablas
    print("\n📦 Creando tablas...")
    init_db()
    print("✅ Tablas creadas exitosamente")
    
    # Crear usuario admin
    print("\n👤 Creando usuario admin...")
    crear_usuario_admin()
    
    print("\n" + "=" * 50)
    print("✅ Inicialización completada!")
    print("=" * 50)
    print("\nPróximos pasos:")
    print("1. Ejecutar: uvicorn main:app --reload")
    print("2. Abrir: http://localhost:8000/docs")
    print("3. Login con admin/admin123")


if __name__ == "__main__":
    main()
