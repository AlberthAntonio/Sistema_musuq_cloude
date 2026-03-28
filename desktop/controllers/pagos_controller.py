"""
Controlador de Pagos/Tesorería — adaptado al esquema refactorizado del backend.
Flujo: Alumno → Matrícula → ObligaciónPago → Pago
"""
from typing import List, Dict, Tuple, Optional
from datetime import date
from core.api_client import (
    PagosClient, AlumnoClient,
    MatriculasClient, ObligacionesClient, ReportesClient,
)


class PagosController:
    """
    Controlador para el módulo de Pagos (Tesorería).
    - obtener_estado_cuenta: datos personales de /alumnos/, financieros de /pagos/resumen/{matricula_id}
    - registrar_pago:        flujo Matrícula → Obligación → Pago
    - obtener_lista_deudores: usa endpoint consolidado /reportes/deudores
    """

    def __init__(self, auth_token: str):
        self.pagos_client      = PagosClient()
        self.alumno_client     = AlumnoClient()
        self.matricula_client  = MatriculasClient()
        self.obligacion_client = ObligacionesClient()
        self.reportes_client   = ReportesClient()

        for client in (self.pagos_client, self.alumno_client,
                       self.matricula_client, self.obligacion_client,
                       self.reportes_client):
            client.token = auth_token

    # ─────────────────────────────────────────────────────────────────
    # BÚSQUEDA
    # ─────────────────────────────────────────────────────────────────

    def buscar_alumno(self, criterio: str) -> List[Dict]:
        """Busca alumnos por DNI o Nombre (retorna AlumnoResumen)"""
        if not criterio or len(criterio) < 2:
            return []
        success, result = self.alumno_client.buscar(criterio)
        if success:
            return result if isinstance(result, list) else result.get("items", [])
        return []

    # ─────────────────────────────────────────────────────────────────
    # ESTADO DE CUENTA
    # ─────────────────────────────────────────────────────────────────

    def obtener_estado_cuenta(self, id_alumno: int) -> Dict:
        """
        Retorna estado de cuenta completo:
        - Datos personales: GET /alumnos/{id}
        - Datos académicos: GET /matriculas/?alumno_id=X
        - Financiero:       GET /pagos/resumen/{matricula_id}
        - Historial:        GET /pagos/?alumno_id=X
        """
        # 1. Datos personales
        success_a, alumno = self.alumno_client.obtener_por_id(id_alumno)
        if not success_a:
            return {}

        nombre = (
            f"{alumno.get('apell_paterno', '')} "
            f"{alumno.get('apell_materno', '')}, "
            f"{alumno.get('nombres', '')}"
        ).strip().rstrip(",").strip()

        # 2. Matrícula activa
        mat_ok, matricula = self.matricula_client.obtener_activa_por_alumno(id_alumno)
        matricula_id = matricula.get("id")   if mat_ok and matricula else None
        codigo       = matricula.get("codigo_matricula", "--") if mat_ok and matricula else "--"
        grupo        = matricula.get("grupo",   "--")          if mat_ok and matricula else "--"
        carrera      = matricula.get("carrera", "--")          if mat_ok and matricula else "--"

        # 3. Resumen financiero via /pagos/resumen/{matricula_id}
        costo_total = 0.0
        pagado      = 0.0
        deuda       = 0.0
        if matricula_id:
            res_ok, resumen = self.pagos_client.obtener_por_alumno(matricula_id)
            if res_ok and resumen:
                costo_total = float(resumen.get("total_obligaciones", 0))
                pagado      = float(resumen.get("total_pagado", 0))
                deuda       = float(resumen.get("saldo_pendiente", 0))

        # 4. Historial de pagos
        historial = []
        h_ok, h_data = self.pagos_client.listar_por_alumno(id_alumno)
        if h_ok:
            historial = h_data if isinstance(h_data, list) else h_data.get("items", [])

        return {
            "id":              id_alumno,
            "nombre_completo": nombre,
            "dni":             alumno.get("dni", ""),
            "codigo":          codigo,
            "grupo":           grupo,
            "carrera":         carrera,
            "costo":           costo_total,
            "pagado":          pagado,
            "deuda":           deuda,
            "historial":       historial,
        }

    # ─────────────────────────────────────────────────────────────────
    # REGISTRO DE PAGO
    # ─────────────────────────────────────────────────────────────────

    def registrar_pago(self, id_alumno: int, monto: float, concepto: str) -> Tuple[bool, str]:
        """
        Registra un pago.
        Flujo: Matrícula activa → primera Obligación pendiente/parcial → Pago.
        Si no existe obligación se crea una en el momento.
        """
        # 1. Matrícula activa del alumno
        mat_ok, matricula = self.matricula_client.obtener_activa_por_alumno(id_alumno)
        if not mat_ok or not matricula:
            return False, "El alumno no tiene matrícula activa para este periodo."

        matricula_id = matricula.get("id")

        # 2. Primera obligación pendiente o parcial
        obl_ok, obl_data = self.obligacion_client.listar(matricula_id=matricula_id, limit=50)
        obligaciones = obl_data if isinstance(obl_data, list) else []
        obligacion_id = None
        for obl in obligaciones:
            if obl.get("estado") in ("pendiente", "parcial"):
                obligacion_id = obl.get("id")
                break

        # 3. Si no hay obligación pendiente, crear una ad-hoc
        if not obligacion_id:
            nueva_obl = {
                "matricula_id":      matricula_id,
                "concepto":          concepto or "Pago",
                "monto_total":       monto,
                "fecha_vencimiento": date.today().isoformat(),
            }
            c_ok, c_res = self.obligacion_client.crear(nueva_obl)
            if not c_ok:
                return False, f"No se pudo crear la obligación: {c_res.get('error', '')}"
            obligacion_id = c_res.get("id")

        # 4. Registrar el pago contra la obligación
        pago_data = {
            "obligacion_id": obligacion_id,
            "monto":         monto,
            "fecha":         date.today().isoformat(),
            "concepto":      concepto or "Pago",
        }
        p_ok, p_res = self.pagos_client.crear(pago_data)
        if p_ok:
            return True, "Pago registrado correctamente"
        return False, p_res.get("error", "Error al registrar pago")

    # ─────────────────────────────────────────────────────────────────
    # REPORTE DE DEUDORES
    # ─────────────────────────────────────────────────────────────────

    def obtener_filtros_disponibles(self) -> Tuple[List[str], List[str]]:
        """Grupos y modalidades disponibles desde matrículas activas"""
        success, result = self.matricula_client.listar(estado="activo", limit=1000)
        grupos      = set()
        modalidades = set()
        if success:
            items = result if isinstance(result, list) else []
            for m in items:
                if m.get("grupo"):
                    grupos.add(m["grupo"])
                if m.get("modalidad"):
                    modalidades.add(m["modalidad"])
        return sorted(grupos), sorted(modalidades)

    def obtener_lista_deudores(
        self,
        grupo:      Optional[str] = None,
        modalidad:  Optional[str] = None,
        periodo_id: Optional[int] = None,
    ) -> List[Dict]:
        """
        Lista de deudores usando GET /reportes/deudores (una sola consulta SQL).
        Reemplaza el loop N×requests anterior.
        """
        success, result = self.reportes_client.deudores(
            periodo_id=periodo_id,
            grupo=grupo,
            modalidad=modalidad,
        )
        if not success:
            print(f"[ERROR PagosController] deudores: {result.get('error', '')}")
            return []

        raw = result if isinstance(result, list) else result.get("items", [])
        registros = []
        for item in raw:
            costo  = float(item.get("total_obligaciones", 0))
            pagado = float(item.get("total_pagado", 0))
            deuda  = float(item.get("saldo_pendiente", 0))

            if deuda <= 0.5:
                continue

            pct_deuda = (deuda / costo * 100) if costo else 0.0
            icono, desc, tag = self._clasificar_deuda(pct_deuda)

            registros.append({
                "id":          item.get("alumno_id"),
                "icono":       icono,
                "nombre":      item.get("alumno_nombre", ""),
                "modalidad":   item.get("modalidad")  or "Sin Modalidad",
                "contacto":    item.get("contacto")   or "-",
                "costo":       costo,
                "pagado":      pagado,
                "deuda":       deuda,
                "estado_desc": desc,
                "tag":         tag,
                "pct_raw":     pct_deuda,
            })

        registros.sort(key=lambda x: x["pct_raw"], reverse=True)
        return registros

    @staticmethod
    def _clasificar_deuda(porcentaje: float) -> Tuple[str, str, str]:
        if porcentaje >= 70:
            return "🔴", f"Debe {porcentaje:.0f}% (>70%)",    "CRITICO"
        if porcentaje >= 40:
            return "🟠", f"Debe {porcentaje:.0f}% (40-69%)", "MEDIO"
        return   "🟡", f"Debe {porcentaje:.0f}% (<40%)",     "BAJO"
