"""
Cliente HTTP para comunicación con el backend FastAPI
Sistema Musuq Cloud
"""

import httpx
from typing import Optional, Dict, Any, Tuple
from .config import Config


class APIClient:
    """Cliente base para llamadas a la API"""
    
    def __init__(self):
        self.base_url = Config.API_BASE_URL
        self.timeout = Config.API_TIMEOUT
        self.token: Optional[str] = None
        # Persistent client for connection pooling (reutiliza conexiones TCP)
        self._client = httpx.Client(timeout=self.timeout)
    
        try:
            # Importación local para evitar ciclos
            from .auth_manager import AuthManager 
            auth = AuthManager()
            if auth.load_session():
                self.token = auth.token
                # print(f"[DEBUG API] Token cargado automáticamente: {self.token[:10]}...") 
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
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Tuple[bool, Dict[str, Any]]:
        """Realizar petición HTTP"""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        try:
            response = self._client.request(
                method=method,
                url=url,
                headers=headers,
                **kwargs
            )
            
            if response.status_code == 200 or response.status_code == 201:
                return True, response.json()
            elif response.status_code == 204:
                return True, {}
            elif response.status_code == 401:
                return False, {"error": "No autorizado. Token inválido o expirado."}
            elif response.status_code == 422:
                return False, {"error": "Datos inválidos", "detail": response.json()}
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
    
    def obtener_todos(self, skip: int = 0, limit: int = 100) -> Tuple[bool, Dict]:
        """Obtener lista de alumnos"""
        return self.get("/alumnos/", params={"skip": skip, "limit": limit})
    
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
    
    def eliminar(self, asistencia_id: int) -> Tuple[bool, Dict]:
        """Eliminar un registro de asistencia"""
        return self.delete(f"/asistencia/{asistencia_id}")

    def justificar(self, asistencia_id: int, motivo: str) -> Tuple[bool, Dict]:
        """Justificar una asistencia (usa PUT genérico)"""
        return self.put(f"/asistencia/{asistencia_id}", data={"estado": "JUSTIFICADO", "observacion": motivo})


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
        return self.get("/horarios/", params={"grupo": grupo})


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
