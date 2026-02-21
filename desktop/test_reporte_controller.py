import sys
import os
from pathlib import Path

# Add desktop to path
desktop_path = Path(__file__).parent
sys.path.insert(0, str(desktop_path))

try:
    from controllers.reporte_controller import ReporteController
    print("✅ Import successful")
    
    ctrl = ReporteController()
    print("✅ Controller instantiated")
    
    # Test filters (might fail if API down, but we want to test code execution)
    try:
        filtros = ctrl.obtener_filtros_disponibles()
        print(f"✅ Filters obtained: {filtros}")
    except Exception as e:
        print(f"⚠️ API error (expected if no backend): {e}")

    # Test local storage
    try:
        listas = ctrl.obtener_listas_guardadas()
        print(f"✅ Lists loaded: {len(listas)}")
        
        # Guardar lista dummy
        success, msg = ctrl.guardar_lista_personalizada("Lista Test", [1, 2, 3])
        print(f"✅ Save list result: {success}, {msg}")
        
        # Eliminar si se guardó
        if success:
            listas = ctrl.obtener_listas_guardadas()
            target_id = listas[-1].id
            ctrl.eliminar_lista(target_id)
            print("✅ List deleted")
            
    except Exception as e:
        print(f"❌ Local storage error: {e}")

except Exception as e:
    print(f"❌ Critical error: {e}")
    import traceback
    traceback.print_exc()
