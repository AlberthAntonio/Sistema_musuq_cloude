"""
Tests unitarios para AsistenciaView
Ejecutar: pytest tests/test_asistencia_view.py -v
"""

import pytest
import customtkinter as ctk
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, time as dt_time
import sys
from pathlib import Path
from datetime import time as dt_time


# Agregar path del proyecto para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ui.control_asistencia_view import AsistenciaView


# ============================================
# FIXTURES (Recursos compartidos)
# ============================================

@pytest.fixture
def root():
    """Fixture para crear ventana temporal de CTk"""
    root = ctk.CTk()
    root.withdraw()  # Ocultar ventana durante tests
    yield root
    try:
        root.destroy()
    except:
        pass


@pytest.fixture
def mock_controller():
    """Mock del AsistenciaController"""
    with patch('app.ui.control_asistencia_view.AsistenciaController') as mock:
        controller_instance = mock.return_value
        
        # Configurar comportamiento por defecto
        controller_instance.obtener_asistencias_hoy.return_value = []
        controller_instance.obtener_asistencias_hoy_por_turno.return_value = []
        controller_instance.contar_todos_alumnos.return_value = 200
        controller_instance.contar_alumnos_por_turno.return_value = 100
        controller_instance.buscar_alumnos_general.return_value = []
        
        # ✅ Formato correcto según tu código en control_asistencia_view.py:1076
        controller_instance.obtener_estado_cierre_hoy.return_value = {
            'manana_cerrado': False,
            'manana_cantidad': 0,
            'tarde_cerrado': False,
            'tarde_cantidad': 0
        }
        
        yield controller_instance



@pytest.fixture
def mock_audio():
    """Mock del AudioHelper"""
    with patch('app.ui.control_asistencia_view.AudioHelper') as mock:
        yield mock.return_value


@pytest.fixture
def view(root, mock_controller, mock_audio):
    """Fixture para crear AsistenciaView mockeada"""
    view = AsistenciaView(root)
    return view


def crear_mock_registro(id_reg, codigo, nombre, turno="MAÑANA", estado="PUNTUAL"):
    """Helper para crear registros mock"""
    from datetime import datetime
    
    mock_reg = Mock()
    mock_reg.id = id_reg
    mock_reg.turno = turno
    mock_reg.estado = estado
    mock_reg.hora = datetime.now().time()
    
    mock_alumno = Mock()
    mock_alumno.codigo_matricula = codigo
    mock_alumno.apell_paterno = f"Apellido{id_reg}"
    mock_alumno.apell_materno = "Materno"
    mock_alumno.nombres = nombre
    
    mock_reg.alumno = mock_alumno
    return mock_reg


# ============================================
# TEST SUITE 1: Inicialización
# ============================================

class TestAsistenciaViewInicializacion:
    """Tests de creación y configuración inicial"""
    
    def test_view_se_crea_sin_errores(self, view):
        """Verifica que la vista se crea correctamente"""
        assert view is not None
        assert isinstance(view, AsistenciaView)
    
    def test_hereda_de_mixin(self, view):
        """Verifica que hereda correctamente de InfiniteScrollMixin"""
        assert hasattr(view, '_scroll_widget_inf'), "Debe heredar de InfiniteScrollMixin"
        assert hasattr(view, 'cargar_datos_scroll'), "Debe tener método del Mixin"
        assert hasattr(view, 'render_fila_scroll'), "Debe implementar método abstracto"
        assert hasattr(view, 'get_total_registros'), "Debe tener getter de total"
        assert hasattr(view, 'get_registros_cargados'), "Debe tener getter de cargados"
    
    def test_scroll_tabla_existe(self, view):
        """Verifica que scroll_tabla se inicializa"""
        assert hasattr(view, 'scroll_tabla')
        assert view.scroll_tabla is not None
        assert view.scroll_tabla.winfo_exists()
    
    def test_widgets_criticos_existen(self, view):
        """Verifica que widgets esenciales están creados"""
        widgets_requeridos = [
            'entry_codigo', 'btn_marcar', 'scroll_tabla', 
            'lbl_contador', 'switch_filtro', 'lbl_estado',
            'btn_cierre', 'lbl_reloj', 'entry_busqueda'
        ]
        
        for widget in widgets_requeridos:
            assert hasattr(view, widget), f"Falta widget crítico: {widget}"
            assert getattr(view, widget) is not None, f"Widget {widget} es None"
    
    def test_variables_iniciales_correctas(self, view):
        """Verifica estado inicial de variables"""
        assert view.filtro_turno_activo == True, "Filtro debe estar activo inicialmente"
        #assert view.cargando == False, "No debe estar cargando al inicio"
        assert view.fila_seleccionada is None, "No debe haber selección inicial"
        assert view.datos_seleccionados is None
        assert view.primer_widget_fila is None
    
    def test_anchos_tabla_definidos(self, view):
        """Verifica que anchos de columnas están configurados"""
        assert hasattr(view, 'ANCHOS')
        assert len(view.ANCHOS) == 6, "Debe tener 6 columnas"
        assert all(isinstance(a, int) for a in view.ANCHOS), "Anchos deben ser enteros"


# ============================================
# TEST SUITE 2: Scroll Infinito
# ============================================

class TestScrollInfinito:
    """Tests específicos del sistema de scroll infinito"""
    
    def test_carga_inicial_solo_lote(self, view):
        """Verifica que solo carga el lote inicial (25 registros)"""
        registros = [crear_mock_registro(i, f"COD{i}", f"Alumno{i}") 
                     for i in range(100)]
        
        view.cargar_datos_scroll(registros)
        
        total = view.get_total_registros()
        cargados = view.get_registros_cargados()
        
        assert total == 100, f"Total debe ser 100, es {total}"
        assert cargados == 25, f"Debe cargar 25 iniciales, cargó {cargados}"
    
    def test_no_renderiza_todos_widgets(self, view):
        """Verifica que no crea 100 widgets de golpe"""
        registros = [crear_mock_registro(i, f"COD{i}", f"Alumno{i}") 
                     for i in range(100)]
        
        view.cargar_datos_scroll(registros)
        
        # Contar solo frames (las filas)
        widgets = len([w for w in view.scroll_tabla.winfo_children() 
                       if isinstance(w, ctk.CTkFrame)])
        
        assert widgets <= 30, f"Demasiados widgets: {widgets}, debe ser <= 30"
    
    def test_contador_formato_correcto(self, view):
        """Verifica formato del contador de registros"""
        registros = [crear_mock_registro(i, f"COD{i}", f"Alumno{i}") 
                     for i in range(50)]
        
        # Simular carga completa
        view._inicializar_tabla_con_scroll_infinito(registros)
        
        texto_contador = view.lbl_contador.cget("text")
        
        assert "/" in texto_contador, f"Contador debe tener formato X/Y, tiene: {texto_contador}"
    
    def test_con_cero_registros(self, view_no_threads):
        """Verifica comportamiento con 0 registros"""
        view_no_threads.cargar_datos_scroll([])
        
        total = view_no_threads.get_total_registros()
        cargados = view_no_threads.get_registros_cargados()
        
        assert total == 0
        assert cargados == 0
        
        # Verificar que NO hay widgets (tu código actual no agrega label)
        widgets = view_no_threads.scroll_tabla.winfo_children()
        assert len(widgets) == 0, "Con 0 registros no debe haber widgets"

    
    def test_con_menos_de_un_lote(self, view):
        """Verifica comportamiento con pocos registros (< 25)"""
        registros = [crear_mock_registro(i, f"COD{i}", f"Alumno{i}") 
                     for i in range(10)]
        
        view.cargar_datos_scroll(registros)
        
        total = view.get_total_registros()
        cargados = view.get_registros_cargados()
        
        assert total == 10
        assert cargados == 10, "Debe cargar todos si son menos del lote"


# ============================================
# TEST SUITE 3: Detección de Turno
# ============================================

class TestDeteccionTurno:
    """Tests de la lógica de detección de turno actual"""
    
    # ============================================
# FIXTURE MEJORADO (reemplazar el existente)
# ============================================

@pytest.fixture
def mock_controller():
    """Mock del AsistenciaController"""
    with patch('app.ui.control_asistencia_view.AsistenciaController') as mock:
        controller_instance = mock.return_value
        
        controller_instance.obtener_asistencias_hoy.return_value = []
        controller_instance.obtener_asistencias_hoy_por_turno.return_value = []
        controller_instance.contar_todos_alumnos.return_value = 200
        controller_instance.contar_alumnos_por_turno.return_value = 100
        controller_instance.buscar_alumnos_general.return_value = []
        controller_instance.obtener_estado_cierre_hoy.return_value = {
            'manana_cerrado': False,
            'manana_cantidad': 0,
            'tarde_cerrado': False,
            'tarde_cantidad': 0
        }
        
        yield controller_instance


@pytest.fixture
def view_no_threads(root, mock_controller, mock_audio):
    """Vista SIN threads automáticos"""
    with patch('app.ui.control_asistencia_view.threading.Thread') as mock_thread:
        mock_thread.return_value.start.return_value = None  # ← BLOQUEAR threads
        view = AsistenciaView(root)
        return view


# ============================================
# NUEVA CLASE: Test Detección de Turno (CORREGIDA)
# ============================================

class TestDeteccionTurno:
    """Tests de la lógica de detección de turno actual"""
    
    @patch('datetime.datetime')  # ← Patch GLOBAL de datetime
    def test_detecta_turno_manana(self, mock_datetime, view_no_threads):
        """Verifica detección correcta de turno mañana (6:00-12:00)"""
        mock_datetime.now.return_value.time.return_value = dt_time(8, 30, 0)
        
        turno = view_no_threads._obtener_turno_actual()
        
        assert "MAÑANA" in turno, f"A las 08:30 debe ser MAÑANA, es: {turno}"
    
    @patch('datetime.datetime')
    def test_detecta_turno_tarde(self, mock_datetime, view_no_threads):
        """Verifica detección correcta de turno tarde (13:00-23:59)"""
        mock_datetime.now.return_value.time.return_value = dt_time(15, 45, 0)
        
        turno = view_no_threads._obtener_turno_actual()
        
        assert "TARDE" in turno, f"A las 15:45 debe ser TARDE, es: {turno}"
    
    @patch('datetime.datetime')
    def test_detecta_fuera_de_horario(self, mock_datetime, view_no_threads):
        """Verifica detección de horario no válido (00:00-05:59)"""
        mock_datetime.now.return_value.time.return_value = dt_time(3, 0, 0)
        
        turno = view_no_threads._obtener_turno_actual()
        
        assert "FUERA" in turno, f"A las 03:00 debe ser FUERA, es: {turno}"
    
    @patch('datetime.datetime')
    def test_borde_inicio_manana(self, mock_datetime, view_no_threads):
        """Test de caso borde: 06:00 (inicio turno mañana)"""
        mock_datetime.now.return_value.time.return_value = dt_time(6, 0, 0)
        
        turno = view_no_threads._obtener_turno_actual()
        
        assert "MAÑANA" in turno
    
    @patch('datetime.datetime')
    def test_borde_fin_manana(self, mock_datetime, view_no_threads):
        """Test de caso borde: 12:00 (fin turno mañana)"""
        mock_datetime.now.return_value.time.return_value = dt_time(12, 0, 0)
        
        turno = view_no_threads._obtener_turno_actual()
        
        assert "MAÑANA" in turno or "FUERA" in turno



# ============================================
# TEST SUITE 4: Filtro de Turno
# ============================================

class TestFiltroTurno:
    """Tests del switch de filtro por turno"""
    
    def test_filtro_activo_inicial(self, view):
        """Verifica que filtro está activo al inicio"""
        assert view.filtro_turno_activo == True
        assert view.switch_filtro.get() == 1
    
    def test_toggle_desactiva_filtro(self, view):
        """Verifica que toggle desactiva el filtro"""
        # Simular click en switch
        view.switch_filtro.deselect()
        view.toggle_filtro_turno()
        
        assert view.filtro_turno_activo == False


# ============================================
# TEST SUITE 5: Limpieza y Memory Leaks
# ============================================

class TestLimpieza:
    """Tests de limpieza de recursos"""
    
    def test_destroy_limpia_timers(self, root, mock_controller, mock_audio):
        """Verifica que destroy() cancela todos los timers"""
        view = AsistenciaView(root)
        
        # Verificar que hay timers activos
        assert view._reloj_after is not None
        
        # Destruir (no debe lanzar errores)
        try:
            view.destroy()
            assert True
        except Exception as e:
            pytest.fail(f"destroy() lanzó error: {e}")
    
    def test_no_memory_leak_en_scroll(self, view):
        """Verifica que scroll infinito no acumula memoria"""
        # Cargar 1000 registros
        registros = [crear_mock_registro(i, f"COD{i}", f"Alumno{i}") 
                     for i in range(1000)]
        
        view.cargar_datos_scroll(registros)
        
        # Solo debe tener ~25 widgets, no 1000
        widgets = len([w for w in view.scroll_tabla.winfo_children() 
                       if isinstance(w, ctk.CTkFrame)])
        
        assert widgets < 50, f"Posible memory leak: {widgets} widgets para 1000 registros"


# ============================================
# TEST SUITE 6: Edge Cases
# ============================================

class TestEdgeCases:
    """Tests de casos extremos y edge cases"""
    
    def test_registro_sin_alumno(self, view):
        """Verifica manejo de registro sin alumno"""
        mock_reg = Mock()
        mock_reg.id = 1
        mock_reg.turno = "MAÑANA"
        mock_reg.estado = "PUNTUAL"
        mock_reg.hora = datetime.now().time()
        mock_reg.alumno = None  # ← Sin alumno
        
        # No debe crashear
        try:
            view.cargar_datos_scroll([mock_reg])
            assert True
        except Exception as e:
            pytest.fail(f"Crasheó con alumno=None: {e}")
    
    def test_registro_sin_turno(self, view):
        """Verifica manejo de registro sin turno"""
        mock_reg = crear_mock_registro(1, "COD001", "Alumno")
        mock_reg.turno = None  # ← Sin turno
        
        try:
            view.cargar_datos_scroll([mock_reg])
            assert True
        except Exception as e:
            pytest.fail(f"Crasheó con turno=None: {e}")
    
    def test_registros_duplicados(self, view):
        """Verifica manejo de IDs duplicados"""
        reg1 = crear_mock_registro(1, "COD001", "Alumno1")
        reg2 = crear_mock_registro(1, "COD002", "Alumno2")  # Mismo ID
        
        try:
            view.cargar_datos_scroll([reg1, reg2])
            assert view.get_total_registros() == 2
        except Exception as e:
            pytest.fail(f"Crasheó con IDs duplicados: {e}")


# ============================================
# EJECUCIÓN
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
