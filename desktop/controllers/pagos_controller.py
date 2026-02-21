from typing import List, Dict, Tuple, Any, Optional
from datetime import datetime, date
from core.api_client import PagosClient, AlumnoClient

class PagosController:
    """
    Controlador para el módulo de Pagos (Tesorería).
    Conectado con la API del backend.
    """
    
    def __init__(self, auth_token: str):
        self.pagos_client = PagosClient()
        self.alumno_client = AlumnoClient()
        self.pagos_client.token = auth_token
        self.alumno_client.token = auth_token

    def buscar_alumno(self, criterio: str) -> List[Dict]:
        """Busca alumnos por DNI o Nombre"""
        if not criterio or len(criterio) < 2:
            return []
        
        success, result = self.alumno_client.buscar(criterio)
        if success:
            return result if isinstance(result, list) else result.get("items", [])
        return []

    def obtener_estado_cuenta(self, id_alumno: int) -> Dict:
        """Obtiene estado de cuenta de un alumno"""
        # Obtener datos del alumno
        success_alumno, alumno_data = self.alumno_client.obtener_por_id(id_alumno)
        if not success_alumno:
            return {}
        
        # Obtener historial de pagos (lista) y resumen de totales
        success_pagos, pagos_data = self.pagos_client.listar_por_alumno(id_alumno)
        pagos = pagos_data if isinstance(pagos_data, list) else pagos_data.get("items", []) if success_pagos else []
        
        # Calcular totales a partir de la lista
        pagado = sum(p.get("monto", 0) for p in pagos)
        costo_total = alumno_data.get("costo_matricula", 0)
        deuda = max(0, costo_total - pagado)
        
        return {
            "id": id_alumno,
            "nombre_completo": f"{alumno_data.get('apell_paterno', '')} {alumno_data.get('apell_materno', '')} {alumno_data.get('nombres', '')}",
            "dni": alumno_data.get("dni", ""),
            "codigo": alumno_data.get("codigo_matricula", ""),
            "grupo": alumno_data.get("grupo", ""),
            "carrera": alumno_data.get("carrera", ""),
            "costo": costo_total,
            "pagado": pagado,
            "deuda": deuda,
            "historial": pagos
        }

    def registrar_pago(self, id_alumno: int, monto: float, concepto: str) -> Tuple[bool, str]:
        """Registra un nuevo pago"""
        data = {
            "alumno_id": id_alumno,
            "monto": monto,
            "concepto": concepto,
            "fecha": date.today().isoformat()
        }
        success, result = self.pagos_client.crear(data)
        if success:
            return True, "Pago registrado correctamente"
        else:
            return False, result.get("error", "Error al registrar pago")

    # --- Métodos para Reporte de Deudores ---

    def obtener_filtros_disponibles(self) -> Tuple[List[str], List[str]]:
        """Retorna listas de grupos y modalidades disponibles"""
        # Obtener alumnos para extraer grupos y modalidades únicas
        success, result = self.alumno_client.obtener_todos(limit=1000)
        
        grupos = set()
        modalidades = set()
        
        if success:
            items = result if isinstance(result, list) else result.get("items", [])
            for item in items:
                if item.get("grupo"):
                    grupos.add(item.get("grupo"))
                if item.get("modalidad"):
                    modalidades.add(item.get("modalidad"))
        
        return sorted(list(grupos)), sorted(list(modalidades))

    def obtener_lista_deudores(self, grupo: Optional[str] = None, modalidad: Optional[str] = None) -> List[Dict]:
        """Genera lista de deudores con información enriquecida para la UI"""
        success, result = self.alumno_client.obtener_todos(limit=1000)
        if not success:
            return []

        alumnos = result if isinstance(result, list) else result.get("items", [])

        # Filtrar por grupo y modalidad (ignorando valores "Todos/Todas")
        if grupo and grupo not in ("Todos", "Todas"):
            alumnos = [a for a in alumnos if a.get("grupo") == grupo]
        if modalidad and modalidad not in ("Todos", "Todas"):
            alumnos = [a for a in alumnos if a.get("modalidad") == modalidad]

        registros = []
        for alumno in alumnos:
            estado = self.obtener_estado_cuenta(alumno.get("id"))

            costo = estado.get("costo") or alumno.get("costo_matricula") or 0.0
            pagado = estado.get("pagado", 0.0)
            deuda = estado.get("deuda")
            deuda = deuda if deuda is not None else max(0.0, costo - pagado)

            if costo <= 0:
                continue  # Ignorar becados
            if deuda <= 0.5:
                continue  # Considerar margen por redondeo

            pct_deuda = (deuda / costo * 100) if costo else 0.0
            icono, desc, tag = self._clasificar_deuda(pct_deuda)

            registros.append({
                "id": alumno.get("id"),
                "icono": icono,
                "nombre": f"{alumno.get('apell_paterno', '')} {alumno.get('apell_materno', '')}, {alumno.get('nombres', '')}".strip(),
                "modalidad": alumno.get("modalidad") or "Sin Modalidad",
                "contacto": alumno.get("telefono_apoderado") or alumno.get("celular_padre_1") or alumno.get("celular") or "-",
                "costo": costo,
                "pagado": pagado,
                "deuda": deuda,
                "estado_desc": desc,
                "tag": tag,
                "pct_raw": pct_deuda
            })

        registros.sort(key=lambda x: x.get("pct_raw", 0.0), reverse=True)
        return registros

    @staticmethod
    def _clasificar_deuda(porcentaje: float) -> Tuple[str, str, str]:
        """Determina icono, descripción y tag según el porcentaje de deuda"""
        if porcentaje >= 70:
            return "🔴", f"Debe {porcentaje:.0f}% (>70%)", "CRITICO"
        if porcentaje >= 40:
            return "🟠", f"Debe {porcentaje:.0f}% (40-69%)", "MEDIO"
        return "🟡", f"Debe {porcentaje:.0f}% (<40%)", "BAJO"
