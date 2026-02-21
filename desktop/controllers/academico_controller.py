from typing import List, Dict, Any, Tuple, Optional
from core.api_client import CursosClient, HorariosClient, SesionesClient, AlumnoClient, NotasClient
import random

class AcademicoController:
    """
    Controlador para el módulo Académico (Cursos, Mallas).
    Conectado con la API del backend.
    """
    
    def __init__(self, auth_token: str):
        self.cursos_client = CursosClient()
        self.horarios_client = HorariosClient()
        self.sesiones_client = SesionesClient()
        self.alumno_client = AlumnoClient()
        self.notas_client = NotasClient()
        
        self.cursos_client.token = auth_token
        self.horarios_client.token = auth_token
        self.sesiones_client.token = auth_token
        self.alumno_client.token = auth_token
        self.notas_client.token = auth_token

    def obtener_catalogo(self, filtro: str = "") -> List[Dict]:
        """Obtener catálogo de cursos desde la API"""
        success, result = self.cursos_client.obtener_todos(limit=1000)
        if not success:
            return []
        
        cursos = result if isinstance(result, list) else result.get("items", [])
        
        if filtro:
            cursos = [c for c in cursos if filtro.lower() in c.get("nombre", "").lower()]
        
        return cursos

    def crear_curso(self, nombre: str, descripcion: str = "") -> Tuple[bool, str]:
        """Crear nuevo curso en el catálogo"""
        data = {
            "nombre": nombre,
            "descripcion": descripcion
        }
        success, result = self.cursos_client.crear(data)
        if success:
            return True, "Curso creado exitosamente"
        else:
            return False, result.get("error", "Error al crear curso")

    def obtener_malla_grupo(self, grupo: str) -> List[Dict]:
        """Obtener cursos asignados a un grupo desde la malla curricular"""
        success, result = self.cursos_client.obtener_por_grupo(grupo)
        if not success:
            return []
        return result if isinstance(result, list) else result.get("items", [])

    def agregar_curso_a_grupo(self, grupo: str, curso_id: int) -> Tuple[bool, str]:
        """Asignar curso a grupo en la malla curricular (POST /cursos/malla/)"""
        success, result = self.cursos_client.crear_asignacion_malla(grupo, curso_id)
        if success:
            return True, "Curso asignado al grupo correctamente"
        else:
            return False, result.get("error", "Error al asignar curso")

    def quitar_curso_de_grupo(self, malla_id: int) -> Tuple[bool, str]:
        """Quitar asignación de curso de la malla curricular (DELETE /cursos/malla/{malla_id})"""
        success, result = self.cursos_client.eliminar_asignacion_malla(malla_id)
        if success:
            return True, "Curso removido de la malla"
        else:
            return False, result.get("error", "Error al remover curso")

    # ==================== HORARIOS ====================
    
    def obtener_slots_horarios(self, turno: str) -> List[Tuple[str, str]]:
        """Retorna slots (hora_inicio, hora_fin) predefinidos"""
        if turno == 'MAÑANA':
            return [
                ('08:00', '08:45'), ('08:45', '09:30'), ('09:30', '10:15'),
                ('10:15', '11:00'), ('11:00', '11:30'),  # Recreo
                ('11:30', '12:15'), ('12:15', '13:00')
            ]
        else:
            return [
                ('14:00', '14:45'), ('14:45', '15:30'), ('15:30', '16:15'),
                ('16:15', '17:00'), ('17:00', '17:30'),  # Recreo
                ('17:30', '18:15'), ('18:15', '19:00')
            ]

    def obtener_horario_grupo(self, grupo: str, periodo: str = "") -> Tuple[bool, str, Dict]:
        """Obtener horario de un grupo desde la API"""
        success, result = self.horarios_client.obtener_por_grupo(grupo)
        
        if not success:
            return False, "No se pudo obtener el horario", {}
        
        horarios = result if isinstance(result, list) else result.get("items", [])
        
        # Organizar por día
        horario_por_dia = {}
        for h in horarios:
            dia = h.get("dia", 1)
            slot = f"{h.get('hora_inicio', '')}-{h.get('hora_fin', '')}"
            
            if dia not in horario_por_dia:
                horario_por_dia[dia] = {}
            
            horario_por_dia[dia][slot] = {
                "id": h.get("id"),
                "nombre_curso": h.get("curso", ""),
                "nombre_docente": h.get("docente", ""),
                "aula": h.get("aula", ""),
                "dia": dia,
                "hora_inicio": h.get("hora_inicio", ""),
                "hora_fin": h.get("hora_fin", "")
            }
        
        return True, "Horario obtenido", horario_por_dia

    def agregar_bloque_horario(self, grupo: str, dia: int, hora_inicio: str, 
                               hora_fin: str, curso_id: int, docente_id: int, 
                               aula: str) -> Tuple[bool, str, Optional[int]]:
        """Agregar bloque de horario"""
        data = {
            "grupo": grupo,
            "dia": dia,
            "hora_inicio": hora_inicio,
            "hora_fin": hora_fin,
            "curso_id": curso_id,
            "docente_id": docente_id,
            "aula": aula
        }
        success, result = self.horarios_client.crear(data)
        if success:
            return True, "Bloque agregado", result.get("id")
        else:
            return False, result.get("error", "Error al agregar bloque"), None

    def eliminar_bloque_horario(self, horario_id: int) -> Tuple[bool, str]:
        """Eliminar bloque de horario"""
        success, result = self.horarios_client.eliminar(horario_id)
        if success:
            return True, "Bloque eliminado"
        else:
            return False, result.get("error", "Error al eliminar bloque")

    # ==================== SESIONES DE EXAMEN ====================
    
    def obtener_sesiones_examen(self, limit: int = 100) -> List[Dict]:
        """Obtener lista de sesiones de examen"""
        success, result = self.sesiones_client.obtener_todas(limit=limit)
        
        if not success:
            return []
        
        return result if isinstance(result, list) else result.get("items", [])

    def crear_sesion_examen(self, titulo: str, fecha: str, estado: str = "ABIERTO") -> Tuple[bool, str]:
        """Crear nueva sesión de examen"""
        data = {
            "titulo": titulo,
            "fecha": fecha,
            "estado": estado
        }
        success, result = self.sesiones_client.crear(data)
        if success:
            return True, "Examen creado"
        else:
            return False, result.get("error", "Error al crear examen")
    def buscar_alumnos_notas(self, grupo: str, modalidad: str, busqueda: str) -> List[Any]:
        """Busca alumnos para el registro de notas usando la API real"""
        params: Dict[str, Any] = {"limit": 1000}
        if grupo and grupo != "Todos":
            params["grupo"] = grupo
        if modalidad and modalidad != "Todos":
            params["modalidad"] = modalidad

        success, result = self.alumno_client.obtener_todos(**params)
        if not success:
            return []

        items = result if isinstance(result, list) else result.get("items", [])

        if busqueda:
            b = busqueda.lower()
            items = [
                a for a in items
                if b in a.get("nombres", "").lower()
                or b in a.get("apell_paterno", "").lower()
                or b in a.get("apell_materno", "").lower()
                or b in a.get("dni", "").lower()
            ]

        # Convertir a objetos con atributos
        class AlumnoObj:
            def __init__(self, d):
                self.id = d.get("id")
                self.nombres = d.get("nombres", "")
                self.apell_paterno = d.get("apell_paterno", "")
                self.apell_materno = d.get("apell_materno", "")
                self.codigo_matricula = d.get("codigo_matricula", "")
                self.grupo = d.get("grupo", "")

        return [AlumnoObj(a) for a in items]

    def obtener_notas_alumno(self, sesion_id: int, alumno_id: int) -> Dict[str, float]:
        """Retorna notas de un alumno en una sesión desde la API"""
        success, result = self.notas_client.obtener_todas(limit=1000)
        if not success:
            return {}
        notas = result if isinstance(result, list) else result.get("items", [])
        # Retorna { 'nombre_curso': nota } para las notas que coincidan con sesion_id y alumno_id
        return {
            str(n.get("curso_nombre", n.get("concepto", f"Nota {n.get('id', '')}"))):
            float(n.get("calificacion", n.get("nota", 0)))
            for n in notas
            if n.get("alumno_id") == alumno_id and n.get("sesion_id") == sesion_id
        }

    def guardar_notas_lote(self, sesion_id: int, datos_notas: List[Dict]) -> Tuple[bool, str]:
        """Guardar notas en lote usando la API real (POST /notas/masivo)"""
        if not datos_notas:
            return False, "No hay notas para guardar"
        success, result = self.notas_client.crear_masivo(sesion_id, datos_notas)
        if success:
            return True, "Notas guardadas correctamente"
        return False, result.get("error", "Error al guardar notas")

    # ==================== BOLETAS ====================
    def buscar_alumno_boleta(self, texto: str, grupo: str) -> List[Any]:
        """Busca alumnos para boletas usando la API real"""
        params: Dict[str, Any] = {"limit": 1000}
        if grupo and grupo != "Todos":
            params["grupo"] = grupo

        success, result = self.alumno_client.obtener_todos(**params)
        if not success:
            return []

        items = result if isinstance(result, list) else result.get("items", [])
        if texto:
            t = texto.lower()
            items = [
                a for a in items
                if t in a.get("nombres", "").lower()
                or t in a.get("apell_paterno", "").lower()
                or t in a.get("dni", "").lower()
                or t in (a.get("codigo_matricula") or "").lower()
            ]

        class AlumnoBoletaObj:
            def __init__(self, d):
                self.id = d.get("id")
                self.nombres = d.get("nombres", "")
                self.apell_paterno = d.get("apell_paterno", "")
                self.apell_materno = d.get("apell_materno", "")
                self.codigo_matricula = d.get("codigo_matricula", "")
                self.grupo = d.get("grupo", "")
                self.activo = d.get("activo", True)

        return [AlumnoBoletaObj(a) for a in items]

    def obtener_data_boleta(self, alumno_id):
        """[MOCK] Data completa para boleta"""
        cursos = ["Matemática I", "Comunicación I", "Ciencias Sociales", "Física", "Química"]
        sesiones = ["Mensual Abril", "Bimestral I"]
        
        notas = {} # { curso: { sesion: nota } }
        for c in cursos:
            notas[c] = { s: round(random.uniform(10, 20), 1) for s in sesiones }
            
        promedio_gral = sum( sum(n.values())/len(n) for n in notas.values() ) / len(notas)
        
        asistencia = { "total": 20, "puntual": 18, "tarde": 1, "falta": 1 }
        
        return {
            "cursos": cursos,
            "sesiones": sesiones,
            "notas": notas,
            "promedio_gral": promedio_gral,
            "puesto": 5,
            "total_alumnos": 30,
            "asistencia": asistencia
        }

    def obtener_grupos_disponibles(self) -> List[str]:
        """Retorna lista de grupos disponibles"""
        return ['A', 'B', 'C', 'D', 'E', 'F']

    # Helpers Combobox
    def obtener_nombres_para_combobox(self) -> List[str]:
        catalogo = self.obtener_catalogo()
        return [c['nombre'] for c in catalogo]

    def buscar_por_nombre(self, nombre) -> Dict:
        catalogo = self.obtener_catalogo()
        for c in catalogo:
            if c['nombre'] == nombre:
                return c
        return None
