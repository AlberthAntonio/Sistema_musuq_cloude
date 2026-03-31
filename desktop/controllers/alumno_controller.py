from typing import Dict, Tuple, List, Optional
from datetime import date
from core.api_client import AlumnoClient, MatriculasClient, PeriodosClient, ObligacionesClient, PagosClient

class AlumnoController:
    """Controlador para la gestión de alumnos (Lógica de Negocio)"""
    
    def __init__(self, auth_token: str):
        self.alumno_client = AlumnoClient(load_cached_session=False)
        self.matricula_client = MatriculasClient(load_cached_session=False)
        self.periodos_client = PeriodosClient(load_cached_session=False)
        self.obligaciones_client = ObligacionesClient(load_cached_session=False)
        self.pagos_client = PagosClient(load_cached_session=False)

        for client in (self.alumno_client, self.matricula_client,
                       self.periodos_client, self.obligaciones_client,
                       self.pagos_client):
            client.token = auth_token
        
        # Carreras por grupo (Business Logic)
        self.CARRERAS_POR_GRUPO = {
            "A": ["MEDICINA", "ENFERMERÍA", "ODONTOLOGÍA", "FARMACIA", "OBSTETRICIA"],
            "B": ["DERECHO", "ADMINISTRACIÓN", "CONTABILIDAD", "ECONOMÍA", "TURISMO"],
            "C": ["INGENIERÍA CIVIL", "ARQUITECTURA", "ING. SISTEMAS", "ING. INDUSTRIAL", "ING. AMBIENTAL"],
            "D": ["EDUCACIÓN INICIAL", "EDUCACIÓN PRIMARIA", "PSICOLOGÍA", "CIENCIAS COMUNICACIÓN", "TRABAJO SOCIAL"]
        }
    
    def get_carreras_por_grupo(self, grupo: str) -> List[str]:
        """Obtener lista de carreras para un grupo"""
        return self.CARRERAS_POR_GRUPO.get(grupo, [])
        
    def calcular_deuda(self, costo: float, a_cuenta: float) -> float:
        """Calcular deuda"""
        return max(0.0, costo - a_cuenta)
        
    def create_student(self, data: Dict) -> Tuple[bool, Dict]:
        """
        Crear nuevo alumno junto con su matrícula y obligación de pago.
        El backend separó Alumno (datos personales) de Matrícula (datos académicos).
        Flujo: POST /alumnos/ → POST /matriculas/ → POST /obligaciones/
        """
        # ─── 0. Verificar periodo activo ANTES de crear alumno ─────────────
        periodo_id = None
        success_p, periodo = self.periodos_client.obtener_activo()
        if success_p and periodo:
            periodo_id = periodo.get("id")
        
        if not periodo_id:
            return False, {"error": "No hay un periodo académico activo. Crea uno antes de registrar alumnos."}

        # ─── 1. Datos personales del alumno ────────────────────────────────
        alumno_data = {
            "dni":                   data.get("dni"),
            "nombres":               data.get("nombres"),
            "apell_paterno":         data.get("apell_paterno"),
            "apell_materno":         data.get("apell_materno"),
            "fecha_nacimiento":      data.get("fecha_nacimiento"),
            "nombre_padre_completo": data.get("nombre_padre_completo"),
            "celular_padre_1":       data.get("celular_padre_1"),
            "celular_padre_2":       data.get("celular_padre_2"),
            "descripcion":           data.get("descripcion"),
        }
        success_a, result_a = self.alumno_client.crear(alumno_data)
        if not success_a:
            return False, result_a

        alumno_id = result_a.get("id")
        advertencias = []

        foto_bytes = data.get("foto_bytes")
        if foto_bytes and alumno_id:
            ok_foto, result_foto = self.alumno_client.subir_foto(
                alumno_id=alumno_id,
                foto_bytes=foto_bytes,
                filename=data.get("foto_filename") or f"alumno_{alumno_id}.jpg",
                mime_type=data.get("foto_mime_type") or "image/jpeg",
            )
            if not ok_foto:
                detalle = result_foto.get("error", "No especificado") if isinstance(result_foto, dict) else str(result_foto)
                advertencias.append(f"No se pudo guardar la foto del alumno: {detalle}")

        # ─── 2. Matrícula ───────────────────────────────────────────────────
        matricula_data = {
            "alumno_id":  alumno_id,
            "periodo_id": periodo_id,
            "grupo":      data.get("grupo"),
            "carrera":    data.get("carrera"),
            "modalidad":  data.get("modalidad"),
            "horario":    data.get("horario"),
            "nivel":      data.get("nivel"),
            "grado":      data.get("grado"),
        }
        # Limpiar campos vacíos / None opcionales (pero mantener los requeridos)
        matricula_data = {k: v for k, v in matricula_data.items() if v is not None}

        success_m, result_m = self.matricula_client.crear(matricula_data)
        if not success_m:
            # Alumno creado exitosamente pero matrícula falló — se informa pero no se revierte
            result_a["_advertencia"] = f"Alumno creado (id={alumno_id}) pero falta la matrícula: {result_m.get('error', '')}"
            return True, result_a

        matricula_id = result_m.get("id")

        # ─── 3. Obligación de pago (si el costo > 0) ───────────────────────
        costo = float(data.get("costo_matricula") or 0)
        a_cuenta = float(data.get("a_cuenta") or 0)
        fecha_cancelacion = data.get("fecha_cancelacion")

        if costo > 0 and matricula_id:
            obligacion_data = {
                "matricula_id":      matricula_id,
                "concepto":          "Matrícula",
                "monto_total":       costo,
                "fecha_vencimiento": fecha_cancelacion or date.today().isoformat(),
            }

            # Si falla la obligación no abortamos — el alumno y matrícula ya están creados
            ok_obl, obligacion = self.obligaciones_client.crear(obligacion_data)
            if not ok_obl:
                advertencias.append("No se pudo crear la obligación de pago inicial.")

            # Registrar abono inicial como pago real para reflejar deuda correcta desde el alta.
            if ok_obl and obligacion and a_cuenta > 0:
                ok_pago, _ = self.pagos_client.crear({
                    "obligacion_id": obligacion.get("id"),
                    "monto": a_cuenta,
                    "fecha": date.today().isoformat(),
                    "concepto": "A cuenta matrícula",
                })
                if not ok_pago:
                    advertencias.append("La matrícula se creó, pero el abono inicial no se pudo registrar automáticamente.")

        # Enriquecer la respuesta con datos de matrícula para la UI
        result_a["matricula"] = result_m
        if advertencias:
            result_a["_advertencia"] = " ".join(advertencias)
        return True, result_a
        
    def get_recent_students(self, limit: int = 5) -> Tuple[bool, object]:
        """Obtener últimos alumnos registrados"""
        return self.alumno_client.obtener_todos(limit=limit)

    def validate_student_data(self, data: Dict) -> Tuple[bool, str, Optional[str]]:
        """
        Validar datos del alumno antes de enviar.
        Retorna: (EsValido, MensajeError, CampoError)
        """
        # DNI
        dni = (data.get("dni") or "").strip()
        if not dni or len(dni) != 8 or not dni.isdigit():
            return False, "El DNI debe tener 8 dígitos", "dni"
        
        # Nombres
        if not data.get("nombres"):
            return False, "Falta el nombre", "nombres"
            
        if not data.get("apell_paterno"):
            return False, "Falta apellido paterno", "apellido_paterno"
            
        # Grupo
        if not data.get("grupo") or data.get("grupo") == "--Seleccione":
            return False, "Debe seleccionar un Grupo", "grupo"
            
        # Carrera
        if not data.get("carrera") or data.get("carrera") == "--Seleccione":
            return False, "Debe seleccionar una Carrera", "carrera"
            
        # Modalidad COLEGIO requiere nivel y grado
        if data.get("modalidad") == "COLEGIO":
            if not data.get("nivel") or data.get("nivel") == "--Seleccione":
                return False, "Debe seleccionar el Nivel (Primaria o Secundaria)", "nivel"
            if not data.get("grado") or data.get("grado") == "--Seleccione":
                return False, "Debe seleccionar el Grado", "grado"

        # Costo
        try:
            c = float(data.get("costo_matricula", 0) or 0)
            if c < 0:
                return False, "El costo no puede ser negativo", "costo"
        except:
            return False, "Costo inválido", "costo"

        # A cuenta (abono inicial)
        try:
            a_cuenta = float(data.get("a_cuenta", 0) or 0)
            if a_cuenta < 0:
                return False, "El monto de A Cuenta no puede ser negativo", "a_cuenta"
            if a_cuenta > c:
                return False, "A Cuenta no puede ser mayor que el Costo Total", "a_cuenta"
        except:
            return False, "Monto de A Cuenta inválido", "a_cuenta"
            
        return True, "OK", None
