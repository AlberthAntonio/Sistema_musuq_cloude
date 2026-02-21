#!/usr/bin/env python3
"""
Script para verificar todas las conexiones de los clientes API del desktop.
Ejecutar: python verificar_api_clients.py
"""

import sys
from pathlib import Path

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))


def verificar_api_clients():
    """Verificar que todos los clientes API se pueden importar"""
    print("🔍 Verificando importación de clientes API...")
    
    clientes = [
        ("APIClient", "app.core.api_client"),
        ("AuthClient", "app.core.api_client"),
        ("AlumnoClient", "app.core.api_client"),
        ("DashboardClient", "app.core.api_client"),
        ("AsistenciaClient", "app.core.api_client"),
        ("UsuariosClient", "app.core.api_client"),
        ("CursosClient", "app.core.api_client"),
        ("DocentesClient", "app.core.api_client"),
        ("HorariosClient", "app.core.api_client"),
        ("EventosClient", "app.core.api_client"),
        ("ListasClient", "app.core.api_client"),
        ("NotasClient", "app.core.api_client"),
        ("PagosClient", "app.core.api_client"),
        ("SesionesClient", "app.core.api_client"),
    ]
    
    todos_ok = True
    for clase, modulo in clientes:
        try:
            exec(f"from {modulo} import {clase}")
            print(f"✅ {clase:25} - OK")
        except Exception as e:
            print(f"❌ {clase:25} - ERROR: {str(e)[:40]}")
            todos_ok = False
    
    return todos_ok


def verificar_controllers():
    """Verificar que todos los controladores se pueden importar"""
    print("\n🔍 Verificando importación de controladores...")
    
    controladores = [
        ("AlumnoController", "controllers.alumno_controller"),
        ("AsistenciaController", "controllers.asistencia_controller"),
        ("DocentesController", "controllers.docentes_controller"),
        ("ReporteController", "controllers.reporte_controller"),
        ("PagosController", "controllers.pagos_controller"),
        ("AcademicoController", "controllers.academico_controller"),
        ("CarnetController", "controllers.carnet_controller"),
        ("ConstanciaController", "controllers.constancia_controller"),
    ]
    
    todos_ok = True
    for clase, modulo in controladores:
        try:
            exec(f"from {modulo} import {clase}")
            print(f"✅ {clase:30} - OK")
        except Exception as e:
            print(f"❌ {clase:30} - ERROR: {str(e)[:40]}")
            todos_ok = False
    
    return todos_ok


def verificar_config():
    """Verificar configuración del cliente"""
    print("\n🔍 Verificando configuración...")
    
    try:
        from core.config import Config
        Config.load()
        print(f"✅ Configuración cargada:")
        print(f"   - App: {Config.APP_NAME}")
        print(f"   - API Backend: {Config.API_BASE_URL}")
        print(f"   - Versión: {Config.APP_VERSION}")
        print(f"   - Tamaño ventana: {Config.MAIN_SIZE}")
        return True
    except Exception as e:
        print(f"❌ Configuración - ERROR: {e}")
        return False


def main():
    """Función principal"""
    print("=" * 70)
    print("  VERIFICACIÓN DE CONEXIONES API - Cliente Desktop")
    print("=" * 70)
    
    # Paso 1: Verificar clientes API
    if not verificar_api_clients():
        print("\n❌ Fallo en clientes API.")
    
    # Paso 2: Verificar controladores
    if not verificar_controllers():
        print("\n❌ Fallo en controladores.")
    
    # Paso 3: Verificar configuración
    if not verificar_config():
        print("\n❌ Fallo en configuración.")
    
    print("\n" + "=" * 70)
    print("✅ VERIFICACIÓN COMPLETADA")
    print("=" * 70)
    print("\n📌 Para iniciar la aplicación desktop:")
    print("   python main.py")
    print("\n⚠️  Asegúrate de que el backend está corriendo:")
    print("   uvicorn main:app --reload --port 8000")


if __name__ == "__main__":
    main()
