"""Cliente HTTP para comunicación con el backend FastAPI
Sistema Musuq Cloud
"""

import httpx
from typing import Optional, Dict, Any, Tuple, List
from .config import Config


class APIClient:
    """Cliente base para llamadas a la API"""
    
    def __init__(self):
        self.base_url = Config.API_BASE_URL
        self.timeout = Config.API_TIMEOUT
        self.token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        # Persistent client for connection pooling (reutiliza conexiones TCP)
        self._client = httpx.Client(timeout=self.timeout)
    
        try:
            # Importación local para evitar ciclos
            from .auth_manager import AuthManager 
            auth = AuthManager()
            if auth.load_session():
                self.token = auth.token
                self.refresh_token = auth.refresh_token
        except Exception as e:
            print(f"[WARN] No se pudo cargar sesión automática: {e}")


    def __del__(self):
        """Cerrar cliente HTTP al destruir la instancia"""
        try:
            if hasattr(self, '_client'):
                self._client.close()
        except:
            pass
    
    def _get_headers(self) -> Dict[str, str]:
        """Obtener headers con autenticación"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def _do_refresh(self) -> bool:
        """Renovar tokens usando refresh_token. Retorna True si lo logra."""
        if not self.refresh_token:
            return False
        try:
            response = self._client.post(
                f"{self.base_url}/auth/refresh",
                json={"refresh_token": self.refresh_token},
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.refresh_token = data.get("refresh_token", self.refresh_token)
                # Persistir en session.json
                try:
                    from .auth_manager import AuthManager
                    auth = AuthManager()
                    auth.load_session()
                    auth.save_session(
                        self.token, auth.user_data or {},
                        remember=True, refresh_token=self.refresh_token
                    )
                except Exception:
                    pass
                return True
        except Exception as e:
            print(f"[WARN] Auto-refresh falló: {e}")
        return False

    def _request(self, method: str, endpoint: str, **kwargs) -> Tuple[bool, Dict[str, Any]]:
        """Realizar petición HTTP con auto-refresh en 401"""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        try:
            response = self._client.request(
                method=method,
                url=url,
                headers=headers,
                **kwargs
            )
            
            if response.status_code in (200, 201):
                return True, response.json()
            elif response.status_code == 204:
                return True, {}
            elif response.status_code == 401:
                # Intentar renovar tokens una sola vez
                if self.refresh_token and self._do_refresh():
                    headers2 = self._get_headers()
                    response2 = self._client.request(
                        method=method, url=url, headers=headers2, **kwargs
                    )
                    if response2.status_code in (200, 201):
                        return True, response2.json()
                    elif response2.status_code == 204:
                        return True, {}
                return False, {"error": "No autorizado. Token inválido o expirado."}
            elif response.status_code == 422:
                try:
                    detail = response.json()
                except Exception:
                    detail = {}
                return False, {"error": "Datos inválidos", "detail": detail}
            else:
                try:
                    error_data = response.json()
                    return False, {"error": error_data.get("detail", "Error desconocido")}
                except:
                    return False, {"error": f"Error HTTP {response.status_code}"}
                    
        except httpx.ConnectError:
            return False, {"error": "No se puede conectar al servidor. ¿Está corriendo el backend?"}
        except httpx.TimeoutException:
            return False, {"error": "Tiempo de espera agotado"}
        except Exception as e:
            return False, {"error": str(e)}
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Tuple[bool, Dict]:
        """Petición GET"""
        return self._request("GET", endpoint, params=params)
    
    def post(self, endpoint: str, data: Optional[Dict] = None) -> Tuple[bool, Dict]:
        """Petición POST"""
        return self._request("POST", endpoint, json=data)
    
    def put(self, endpoint: str, data: Optional[Dict] = None) -> Tuple[bool, Dict]:
        """Petición PUT"""
        return self._request("PUT", endpoint, json=data)
    
    def delete(self, endpoint: str) -> Tuple[bool, Dict]:
        """Petición DELETE"""
        return self._request("DELETE", endpoint)


class AuthClient(APIClient):
    """Cliente para autenticación"""
    
    def login(self, username: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Iniciar sesión
        Returns: (success, message, user_data)
        """
        # El backend espera form data para OAuth2
        try:
            response = self._client.post(
                f"{self.base_url}/auth/login",
                data={"username": username, "password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
                
                # Obtener datos del usuario
                user_success, user_data = self.get_current_user()
                if user_success:
                    return True, "Login exitoso", user_data
                else:
                    return True, "Login exitoso", {"username": username}
            else:
                try:
                    error = response.json().get("detail", "Credenciales incorrectas")
                except:
                    error = "Error de autenticación"
                return False, error, None
                
        except httpx.ConnectError:
            return False, "No se puede conectar al servidor", None
        except Exception as e:
            return False, str(e), None
    
    def get_current_user(self) -> Tuple[bool, Optional[Dict]]:
        """Obtener datos del usuario actual"""
        return self.get("/auth/me")
    
    def verify_token(self) -> bool:
        """Verificar si el token actual es válido"""
        if not self.token:
            return False
        success, _ = self.get("/auth/me")
        return success


class AlumnoClient(APIClient):
    """Cliente para gestión de alumnos"""
    
    def obtener_todos(self, skip: int = 0, limit: int = 100, **kwargs) -> Tuple[bool, Dict]:
        """Obtener lista de alumnos con filtros opcionales"""
        params = {"skip": skip, "limit": limit}
        params.update(kwargs)  # Añade grupo u otros filtros
        return self.get("/alumnos/", params=params)
    
    def obtener_por_id(self, alumno_id: int) -> Tuple[bool, Dict]:
        """Obtener alumno por ID"""
        return self.get(f"/alumnos/{alumno_id}")
    
    def crear(self, data: Dict) -> Tuple[bool, Dict]:
        """Crear nuevo alumno"""
        return self.post("/alumnos/", data=data)
    
    def actualizar(self, alumno_id: int, data: Dict) -> Tuple[bool, Dict]:
        """Actualizar alumno"""
        return self.put(f"/alumnos/{alumno_id}", data=data)
    
    def eliminar(self, alumno_id: int) -> Tuple[bool, Dict]:
        """Eliminar alumno"""
        return self.delete(f"/alumnos/{alumno_id}")
    
    #def buscar(self, query: str) -> Tuple[bool, Dict]:
    #    """Buscar alumnos por nombre o código"""
    #    return self.get("/alumnos/buscar", params={"q": query})

    
    def buscar(self, query: str) -> Tuple[bool, Dict]:
        """Buscar alumnos por nombre o código"""
        print(f"[DEBUG API] Buscando: '{query}'")
        print(f"[DEBUG API] URL completa: {self.base_url}/alumnos/buscar?q={query}")
        success, result = self.get("/alumnos/buscar", params={"q": query})
        print(f"[DEBUG API] Success: {success}, Tipo resultado: {type(result)}")
        if success:
            print(f"[DEBUG API] Contenido: {result}")
        else:
            print(f"[DEBUG API] Error: {result}")
        return success, result



class DashboardClient(APIClient):
    """Cliente para datos del dashboard"""
    
    def get_stats(self) -> Tuple[bool, Dict]:
        """Obtener estadísticas generales usando datos reales del backend"""
        # Obtener conteo de alumnos
        success_a, data_a = self.get("/alumnos/", params={"limit": 1000})
        if not success_a:
            return False, data_a

        alumnos = data_a.get("items", []) if isinstance(data_a, dict) else data_a
        total = len(alumnos) if isinstance(alumnos, list) else 0
        activos = len([a for a in alumnos if a.get("activo", True)]) if isinstance(alumnos, list) else 0
        grupos = len(set([a.get("grupo") for a in alumnos if a.get("grupo")])) if isinstance(alumnos, list) else 0

        # Obtener asistencias de hoy para calcular porcentaje real
        asistencia_hoy_str = "—"
        try:
            success_h, data_h = self.get("/asistencia/hoy")
            if success_h:
                registros_hoy = data_h if isinstance(data_h, list) else data_h.get("items", [])
                puntuales = sum(1 for r in registros_hoy if r.get("estado") in ("Puntual", "PUNTUAL"))
                tardanzas = sum(1 for r in registros_hoy if r.get("estado") in ("Tarde", "TARDANZA"))
                total_hoy = len(registros_hoy)
                if total_hoy > 0:
                    pct = round((puntuales + tardanzas) / total_hoy * 100)
                    asistencia_hoy_str = f"{pct}%"
        except Exception:
            pass

        return True, {
            "total_alumnos": total,
            "alumnos_activos": activos,
            "grupos": grupos,
            "asistencia_hoy": asistencia_hoy_str
        }


class AsistenciaClient(APIClient):
    """Cliente para gestión de asistencia"""
    
    def registrar(self, data: Dict) -> Tuple[bool, Dict]:
        """Registrar una asistencia"""
        return self.post("/asistencia/", data=data)
    
    def registrar_masivo(self, data: Dict) -> Tuple[bool, Dict]:
        """Registrar asistencia masiva"""
        return self.post("/asistencia/masivo", data=data)
    
    def obtener_hoy(self, grupo: Optional[str] = None, turno: Optional[str] = None) -> Tuple[bool, Dict]:
        """Obtener asistencias de hoy"""
        params = {}
        if grupo: params["grupo"] = grupo
        if turno: params["turno"] = turno
        return self.get("/asistencia/hoy", params=params)
    
    def reporte_fecha(self, fecha: str, grupo: Optional[str] = None) -> Tuple[bool, Dict]:
        """Obtener reporte por fecha"""
        params = {}
        if grupo: params["grupo"] = grupo
        return self.get(f"/asistencia/reporte/fecha/{fecha}", params=params)

    def listar(
        self,
        fecha: Optional[str] = None,
        alumno_id: Optional[int] = None,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
        skip: Optional[int] = None,
        limit: Optional[int] = None
    ) -> Tuple[bool, Dict]:
        """Listar asistencias con filtros"""
        params = {}
        if fecha: params["fecha"] = fecha
        if alumno_id: params["alumno_id"] = alumno_id
        if fecha_inicio: params["fecha_inicio"] = fecha_inicio
        if fecha_fin: params["fecha_fin"] = fecha_fin
        if skip is not None: params["skip"] = skip
        if limit is not None: params["limit"] = limit
        return self.get("/asistencia/", params=params)
    
    def actualizar(self, asistencia_id: int, data: Dict) -> Tuple[bool, Dict]:
        """Actualizar un registro de asistencia (estado, observacion, etc.)"""
        return self.put(f"/asistencia/{asistencia_id}", data=data)

    def eliminar(self, asistencia_id: int) -> Tuple[bool, Dict]:
        """Eliminar un registro de asistencia"""
        return self.delete(f"/asistencia/{asistencia_id}")

    def justificar(self, asistencia_id: int, motivo: str) -> Tuple[bool, Dict]:
        """Justificar una asistencia (usa PUT genérico)"""
        return self.actualizar(asistencia_id, {"estado": "JUSTIFICADO", "observacion": motivo})


class UsuariosClient(APIClient):
    """Cliente para gestión de usuarios"""
    
    def obtener_todos(self, skip: int = 0, limit: int = 100) -> Tuple[bool, Dict]:
        """Obtener lista de usuarios"""
        return self.get("/usuarios/", params={"skip": skip, "limit": limit})
    
    def obtener_por_id(self, usuario_id: int) -> Tuple[bool, Dict]:
        """Obtener usuario por ID"""
        return self.get(f"/usuarios/{usuario_id}")
    
    def crear(self, data: Dict) -> Tuple[bool, Dict]:
        """Crear nuevo usuario"""
        return self.post("/usuarios/", data=data)
    
    def actualizar(self, usuario_id: int, data: Dict) -> Tuple[bool, Dict]:
        """Actualizar usuario"""
        return self.put(f"/usuarios/{usuario_id}", data=data)
    
    def eliminar(self, usuario_id: int) -> Tuple[bool, Dict]:
        """Eliminar usuario"""
        return self.delete(f"/usuarios/{usuario_id}")


class CursosClient(APIClient):
    """Cliente para gestión de cursos"""
    
    def obtener_todos(self, skip: int = 0, limit: int = 100) -> Tuple[bool, Dict]:
        """Obtener lista de cursos"""
        return self.get("/cursos/", params={"skip": skip, "limit": limit})
    
    def obtener_por_id(self, curso_id: int) -> Tuple[bool, Dict]:
        """Obtener curso por ID"""
        return self.get(f"/cursos/{curso_id}")
    
    def crear(self, data: Dict) -> Tuple[bool, Dict]:
        """Crear nuevo curso"""
        return self.post("/cursos/", data=data)
    
    def actualizar(self, curso_id: int, data: Dict) -> Tuple[bool, Dict]:
        """Actualizar curso"""
        return self.put(f"/cursos/{curso_id}", data=data)
    
    def eliminar(self, curso_id: int) -> Tuple[bool, Dict]:
        """Eliminar curso"""
        return self.delete(f"/cursos/{curso_id}")
    
    def obtener_malla_curricular(self, curso_id: int) -> Tuple[bool, Dict]:
        """Obtener detalle de un curso por ID"""
        return self.get(f"/cursos/{curso_id}")
    
    def obtener_malla_por_grupo(self, grupo: str) -> Tuple[bool, Dict]:
        """Obtener cursos asignados a un grupo desde la malla curricular"""
        return self.get(f"/cursos/por-grupo/{grupo}")

    def obtener_asignaciones_malla(self, grupo: str) -> Tuple[bool, Dict]:
        """Obtener asignaciones de malla por grupo (incluye id de malla)."""
        return self.get("/cursos/malla/", params={"grupo": grupo})
    
    def crear_asignacion_malla(self, grupo: str, curso_id: int) -> Tuple[bool, Dict]:
        """Asignar un curso a un grupo en la malla curricular"""
        return self.post("/cursos/malla/", data={"grupo": grupo, "curso_id": curso_id})
    
    def eliminar_asignacion_malla(self, malla_id: int) -> Tuple[bool, Dict]:
        """Quitar asignación de curso de la malla curricular"""
        return self.delete(f"/cursos/malla/{malla_id}")
    
    def obtener_por_grupo(self, grupo: str) -> Tuple[bool, Dict]:
        """Obtener cursos de un grupo"""
        return self.get(f"/cursos/por-grupo/{grupo}")


class DocentesClient(APIClient):
    """Cliente para gestión de docentes"""
    
    def obtener_todos(self, skip: int = 0, limit: int = 100) -> Tuple[bool, Dict]:
        """Obtener lista de docentes (todos, sin filtro de estado)"""
        return self.get("/docentes/", params={"limit": limit})
    
    def obtener_por_id(self, docente_id: int) -> Tuple[bool, Dict]:
        """Obtener docente por ID"""
        return self.get(f"/docentes/{docente_id}")
    
    def crear(self, data: Dict) -> Tuple[bool, Dict]:
        """Crear nuevo docente"""
        return self.post("/docentes/", data=data)
    
    def actualizar(self, docente_id: int, data: Dict) -> Tuple[bool, Dict]:
        """Actualizar docente"""
        return self.put(f"/docentes/{docente_id}", data=data)
    
    def eliminar(self, docente_id: int) -> Tuple[bool, Dict]:
        """Eliminar docente"""
        return self.delete(f"/docentes/{docente_id}")
    
    def buscar(self, query: str) -> Tuple[bool, Dict]:
        """Buscar docentes por nombre o DNI"""
        return self.get("/docentes/buscar", params={"q": query})

    def obtener_por_curso(self, curso_id: int) -> Tuple[bool, Dict]:
        """Obtener docentes que dictan un curso específico."""
        return self.get(f"/docentes/por-curso/{curso_id}")

    def obtener_cursos_docente(self, docente_id: int) -> Tuple[bool, Dict]:
        """Obtener cursos asignados a un docente."""
        return self.get(f"/docentes/{docente_id}/cursos")

    def asignar_cursos(self, docente_id: int, curso_ids: List[int]) -> Tuple[bool, Dict]:
        """Asignar (reemplazar) los cursos de un docente."""
        data = {"curso_ids": curso_ids}
        return self.post(f"/docentes/{docente_id}/cursos", data=data)


class HorariosClient(APIClient):
    """Cliente para gestión de horarios"""
    
    def obtener_todos(self, skip: int = 0, limit: int = 100) -> Tuple[bool, Dict]:
        """Obtener lista de horarios"""
        return self.get("/horarios/", params={"skip": skip, "limit": limit})
    
    def obtener_por_id(self, horario_id: int) -> Tuple[bool, Dict]:
        """Obtener horario por ID"""
        return self.get(f"/horarios/{horario_id}")
    
    def crear(self, data: Dict) -> Tuple[bool, Dict]:
        """Crear nuevo horario"""
        return self.post("/horarios/", data=data)
    
    def actualizar(self, horario_id: int, data: Dict) -> Tuple[bool, Dict]:
        """Actualizar horario"""
        return self.put(f"/horarios/{horario_id}", data=data)
    
    def eliminar(self, horario_id: int) -> Tuple[bool, Dict]:
        """Eliminar horario"""
        return self.delete(f"/horarios/{horario_id}")
    
    def obtener_por_grupo(self, grupo: str) -> Tuple[bool, Dict]:
        """Obtener horarios de un grupo"""
        return self.get("/horarios/por-grupo/{}".format(grupo))

    def obtener_por_aula(self, aula_id: int, periodo: Optional[str] = None) -> Tuple[bool, Dict]:
        """GET /aulas/{id}/horarios — horarios de un aula específica"""
        params: Dict[str, Any] = {}
        if periodo:
            params["periodo"] = periodo
        return self.get(f"/aulas/{aula_id}/horarios", params=params)


class EventosClient(APIClient):
    """Cliente para gestión de eventos del calendario"""
    
    def obtener_todos(self, skip: int = 0, limit: int = 100) -> Tuple[bool, Dict]:
        """Obtener lista de eventos"""
        return self.get("/eventos/", params={"skip": skip, "limit": limit})
    
    def obtener_por_id(self, evento_id: int) -> Tuple[bool, Dict]:
        """Obtener evento por ID"""
        return self.get(f"/eventos/{evento_id}")
    
    def crear(self, data: Dict) -> Tuple[bool, Dict]:
        """Crear nuevo evento"""
        return self.post("/eventos/", data=data)
    
    def actualizar(self, evento_id: int, data: Dict) -> Tuple[bool, Dict]:
        """Actualizar evento"""
        return self.put(f"/eventos/{evento_id}", data=data)
    
    def eliminar(self, evento_id: int) -> Tuple[bool, Dict]:
        """Eliminar evento"""
        return self.delete(f"/eventos/{evento_id}")
    
    def obtener_por_fecha(self, fecha: str) -> Tuple[bool, Dict]:
        """Obtener eventos de una fecha específica"""
        return self.get("/eventos/", params={"fecha": fecha})


class ListasClient(APIClient):
    """Cliente para gestión de listas de alumnos"""
    
    def obtener_todas(self, skip: int = 0, limit: int = 100) -> Tuple[bool, Dict]:
        """Obtener lista de listas"""
        return self.get("/listas/", params={"skip": skip, "limit": limit})
    
    def obtener_por_id(self, lista_id: int) -> Tuple[bool, Dict]:
        """Obtener lista por ID"""
        return self.get(f"/listas/{lista_id}")
    
    def crear(self, data: Dict) -> Tuple[bool, Dict]:
        """Crear nueva lista"""
        return self.post("/listas/", data=data)
    
    def actualizar(self, lista_id: int, data: Dict) -> Tuple[bool, Dict]:
        """Actualizar lista"""
        return self.put(f"/listas/{lista_id}", data=data)
    
    def eliminar(self, lista_id: int) -> Tuple[bool, Dict]:
        """Eliminar lista"""
        return self.delete(f"/listas/{lista_id}")
    
    def agregar_alumnos(self, lista_id: int, alumno_ids: list) -> Tuple[bool, Dict]:
        """Agregar alumnos a una lista existente (POST /listas/{id}/alumnos)"""
        return self.post(f"/listas/{lista_id}/alumnos", data={"alumno_ids": alumno_ids})


class NotasClient(APIClient):
    """Cliente para gestión de notas/calificaciones"""
    
    def obtener_todas(self, skip: int = 0, limit: int = 100) -> Tuple[bool, Dict]:
        """Obtener lista de notas"""
        return self.get("/notas/", params={"skip": skip, "limit": limit})
    
    def obtener_por_id(self, nota_id: int) -> Tuple[bool, Dict]:
        """Obtener nota por ID"""
        return self.get(f"/notas/{nota_id}")
    
    def crear(self, data: Dict) -> Tuple[bool, Dict]:
        """Crear nueva nota"""
        return self.post("/notas/", data=data)
    
    def actualizar(self, nota_id: int, data: Dict) -> Tuple[bool, Dict]:
        """Actualizar nota"""
        return self.put(f"/notas/{nota_id}", data=data)
    
    def eliminar(self, nota_id: int) -> Tuple[bool, Dict]:
        """Eliminar nota"""
        return self.delete(f"/notas/{nota_id}")
    
    def obtener_por_alumno(self, alumno_id: int) -> Tuple[bool, Dict]:
        """Obtener notas de un alumno"""
        return self.get(f"/notas/alumno/{alumno_id}")
    
    def crear_masivo(self, sesion_id: int, notas: list) -> Tuple[bool, Dict]:
        """Crear notas masivamente para una sesión (POST /notas/masivo)"""
        return self.post("/notas/masivo", data={"sesion_id": sesion_id, "notas": notas})


class PagosClient(APIClient):
    """Cliente para gestión de pagos"""
    
    def obtener_todos(self, skip: int = 0, limit: int = 100) -> Tuple[bool, Dict]:
        """Obtener lista de pagos"""
        return self.get("/pagos/", params={"skip": skip, "limit": limit})
    
    def obtener_por_id(self, pago_id: int) -> Tuple[bool, Dict]:
        """Obtener pago por ID"""
        return self.get(f"/pagos/{pago_id}")
    
    def crear(self, data: Dict) -> Tuple[bool, Dict]:
        """Crear nuevo pago"""
        return self.post("/pagos/", data=data)
    
    def actualizar(self, pago_id: int, data: Dict) -> Tuple[bool, Dict]:
        """Actualizar pago"""
        return self.put(f"/pagos/{pago_id}", data=data)
    
    def eliminar(self, pago_id: int) -> Tuple[bool, Dict]:
        """Eliminar pago"""
        return self.delete(f"/pagos/{pago_id}")
    
    def obtener_por_alumno(self, alumno_id: int) -> Tuple[bool, Dict]:
        """Obtener resumen de pagos de un alumno (usa /pagos/resumen/{id})"""
        return self.get(f"/pagos/resumen/{alumno_id}")
    
    def listar_por_alumno(self, alumno_id: int, limit: int = 500) -> Tuple[bool, Dict]:
        """Obtener lista de pagos de un alumno (GET /pagos/?alumno_id=X)"""
        return self.get("/pagos/", params={"alumno_id": alumno_id, "limit": limit})


class SesionesClient(APIClient):
    """Cliente para gestión de sesiones de examen"""
    
    def obtener_todas(self, skip: int = 0, limit: int = 100) -> Tuple[bool, Dict]:
        """Obtener lista de sesiones"""
        return self.get("/sesiones/", params={"skip": skip, "limit": limit})
    
    def obtener_por_id(self, sesion_id: int) -> Tuple[bool, Dict]:
        """Obtener sesión por ID"""
        return self.get(f"/sesiones/{sesion_id}")
    
    def crear(self, data: Dict) -> Tuple[bool, Dict]:
        """Crear nueva sesión"""
        return self.post("/sesiones/", data=data)
    
    def actualizar(self, sesion_id: int, data: Dict) -> Tuple[bool, Dict]:
        """Actualizar sesión"""
        return self.put(f"/sesiones/{sesion_id}", data=data)
    
    def eliminar(self, sesion_id: int) -> Tuple[bool, Dict]:
        """Eliminar sesión"""
        return self.delete(f"/sesiones/{sesion_id}")


class AulasClient(APIClient):
    """Cliente para gestión de aulas"""

    def listar(self, modalidad: Optional[str] = None, activo: Optional[bool] = True) -> Tuple[bool, Dict]:
        """GET /aulas/ — lista de aulas con filtros opcionales"""
        params: Dict[str, Any] = {}
        if modalidad:
            params["modalidad"] = modalidad
        if activo is not None:
            params["activo"] = activo
        return self.get("/aulas/", params=params)

    def obtener_por_id(self, aula_id: int) -> Tuple[bool, Dict]:
        """GET /aulas/{id}"""
        return self.get(f"/aulas/{aula_id}")

    def crear(self, data: Dict) -> Tuple[bool, Dict]:
        """POST /aulas/ — crea aula (solo admin)"""
        return self.post("/aulas/", data=data)

    def actualizar(self, aula_id: int, data: Dict) -> Tuple[bool, Dict]:
        """PUT /aulas/{id} — actualiza aula (solo admin)"""
        return self.put(f"/aulas/{aula_id}", data=data)

    def eliminar(self, aula_id: int) -> Tuple[bool, Dict]:
        """DELETE /aulas/{id} — elimina aula (solo admin)"""
        return self.delete(f"/aulas/{aula_id}")

    def obtener_horarios(self, aula_id: int, periodo: Optional[str] = None) -> Tuple[bool, Dict]:
        """GET /aulas/{id}/horarios"""
        params: Dict[str, Any] = {}
        if periodo:
            params["periodo"] = periodo
        return self.get(f"/aulas/{aula_id}/horarios", params=params)


class MatriculasClient(APIClient):
    """Cliente para gestión de matrículas (POST-refactorización)"""

    def listar(
        self,
        periodo_id: Optional[int] = None,
        alumno_id: Optional[int] = None,
        grupo: Optional[str] = None,
        estado: Optional[str] = "activo",
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[bool, Dict]:
        """GET /matriculas/ con filtros opcionales"""
        params: Dict[str, Any] = {"skip": skip, "limit": limit}
        if periodo_id is not None:
            params["periodo_id"] = periodo_id
        if alumno_id is not None:
            params["alumno_id"] = alumno_id
        if grupo:
            params["grupo"] = grupo
        if estado:
            params["estado"] = estado
        return self.get("/matriculas/", params=params)

    def obtener_activa_por_alumno(self, alumno_id: int, periodo_id: Optional[int] = None) -> Tuple[bool, Optional[Dict]]:
        """Retorna la matrícula activa de un alumno (primero de la lista o None)"""
        params: Dict[str, Any] = {"alumno_id": alumno_id, "estado": "activo", "limit": 1}
        if periodo_id:
            params["periodo_id"] = periodo_id
        success, result = self.get("/matriculas/", params=params)
        if success:
            items = result if isinstance(result, list) else []
            return (True, items[0]) if items else (False, None)
        return False, None

    def obtener_por_id(self, matricula_id: int) -> Tuple[bool, Dict]:
        return self.get(f"/matriculas/{matricula_id}")

    def obtener_por_codigo(self, codigo: str) -> Tuple[bool, Dict]:
        return self.get(f"/matriculas/codigo/{codigo}")

    def crear(self, data: Dict) -> Tuple[bool, Dict]:
        """POST /matriculas/"""
        return self.post("/matriculas/", data=data)

    def actualizar(self, matricula_id: int, data: Dict) -> Tuple[bool, Dict]:
        return self.put(f"/matriculas/{matricula_id}", data=data)

    def retirar(self, matricula_id: int) -> Tuple[bool, Dict]:
        return self.post(f"/matriculas/{matricula_id}/retirar", data={})

    def eliminar(self, matricula_id: int) -> Tuple[bool, Dict]:
        return self.delete(f"/matriculas/{matricula_id}")


class PeriodosClient(APIClient):
    """Cliente para gestión de periodos académicos"""

    def listar(self) -> Tuple[bool, Dict]:
        """GET /periodos/"""
        return self.get("/periodos/")

    def obtener_activo(self) -> Tuple[bool, Dict]:
        """GET /periodos/activo — retorna el periodo activo actual"""
        return self.get("/periodos/activo")

    def obtener_por_id(self, periodo_id: int) -> Tuple[bool, Dict]:
        return self.get(f"/periodos/{periodo_id}")

    def crear(self, data: Dict) -> Tuple[bool, Dict]:
        return self.post("/periodos/", data=data)

    def actualizar(self, periodo_id: int, data: Dict) -> Tuple[bool, Dict]:
        return self.put(f"/periodos/{periodo_id}", data=data)

    def cerrar(self, periodo_id: int) -> Tuple[bool, Dict]:
        return self.post(f"/periodos/{periodo_id}/cerrar", data={})


class ObligacionesClient(APIClient):
    """Cliente para gestión de obligaciones de pago (POST-refactorización)"""

    def listar(
        self,
        matricula_id: Optional[int] = None,
        periodo_id: Optional[int] = None,
        estado: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[bool, Dict]:
        """GET /obligaciones/"""
        params: Dict[str, Any] = {"skip": skip, "limit": limit}
        if matricula_id is not None:
            params["matricula_id"] = matricula_id
        if periodo_id is not None:
            params["periodo_id"] = periodo_id
        if estado:
            params["estado"] = estado
        return self.get("/obligaciones/", params=params)

    def obtener_por_id(self, obligacion_id: int) -> Tuple[bool, Dict]:
        return self.get(f"/obligaciones/{obligacion_id}")

    def crear(self, data: Dict) -> Tuple[bool, Dict]:
        """POST /obligaciones/"""
        return self.post("/obligaciones/", data=data)

    def actualizar(self, obligacion_id: int, data: Dict) -> Tuple[bool, Dict]:
        return self.put(f"/obligaciones/{obligacion_id}", data=data)

    def eliminar(self, obligacion_id: int) -> Tuple[bool, Dict]:
        return self.delete(f"/obligaciones/{obligacion_id}")


class ReportesClient(APIClient):
    """
    Cliente para endpoints de reportes consolidados.
    Reemplaza patrones N×requests con consultas SQL únicas en el backend.
    """

    def deudores(
        self,
        periodo_id: Optional[int] = None,
        grupo: Optional[str] = None,
        modalidad: Optional[str] = None,
    ) -> Tuple[bool, Dict]:
        """
        GET /reportes/deudores — lista alumnos con saldo pendiente.
        Reemplaza el loop alumno-por-alumno en PagosController.
        """
        params: Dict[str, Any] = {}
        if periodo_id is not None:
            params["periodo_id"] = periodo_id
        if grupo and grupo not in ("Todos", "Todas"):
            params["grupo"] = grupo
        if modalidad and modalidad not in ("Todos", "Todas"):
            params["modalidad"] = modalidad
        return self.get("/reportes/deudores", params=params)

    def tardanzas(
        self,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
        grupo: Optional[str] = None,
        turno: Optional[str] = None,
        periodo_id: Optional[int] = None,
    ) -> Tuple[bool, Dict]:
        """
        GET /reportes/tardanzas — lista registros de estado Tarde en el rango.
        Reemplaza la paginación manual de 500-en-500 en ReporteTardanzaController.
        """
        params: Dict[str, Any] = {}
        if fecha_inicio:
            params["fecha_inicio"] = fecha_inicio
        if fecha_fin:
            params["fecha_fin"] = fecha_fin
        if grupo and grupo not in ("Todos",):
            params["grupo"] = grupo
        if turno and turno not in ("Todos",):
            params["turno"] = turno
        if periodo_id is not None:
            params["periodo_id"] = periodo_id
        return self.get("/reportes/tardanzas", params=params)

    def asistencia_resumen(
        self,
        periodo_id: Optional[int] = None,
        grupo: Optional[str] = None,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
    ) -> Tuple[bool, Dict]:
        """GET /reportes/asistencia — resumen por alumno con GROUP BY."""
        params: Dict[str, Any] = {}
        if periodo_id is not None:
            params["periodo_id"] = periodo_id
        if grupo and grupo not in ("Todos",):
            params["grupo"] = grupo
        if fecha_inicio:
            params["fecha_inicio"] = fecha_inicio
        if fecha_fin:
            params["fecha_fin"] = fecha_fin
        return self.get("/reportes/asistencia", params=params)

    def estadisticas_periodo(self, periodo_id: int) -> Tuple[bool, Dict]:
        """GET /reportes/estadisticas/{periodo_id} — resumen completo del periodo."""
        return self.get(f"/reportes/estadisticas/{periodo_id}")
