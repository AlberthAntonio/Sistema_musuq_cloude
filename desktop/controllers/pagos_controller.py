"""
Controlador de Pagos/Tesorería — adaptado al esquema refactorizado del backend.
Flujo: Alumno → Matrícula → ObligaciónPago → Pago
"""
from typing import List, Dict, Tuple, Optional
from datetime import date
from core.api_client import (
    PagosClient, AlumnoClient,
    MatriculasClient, ObligacionesClient, ReportesClient, PeriodosClient,
)


class PagosController:
    """
    Controlador para el módulo de Pagos (Tesorería).
    - obtener_estado_cuenta: datos personales de /alumnos/, financieros de /pagos/resumen/matricula/{matricula_id}
    - registrar_pago:        flujo Matrícula → Obligación → Pago
    - obtener_lista_deudores: usa endpoint consolidado /reportes/deudores
    """

    def __init__(self, auth_token: str):
        self.pagos_client      = PagosClient(load_cached_session=False)
        self.alumno_client     = AlumnoClient(load_cached_session=False)
        self.matricula_client  = MatriculasClient(load_cached_session=False)
        self.obligacion_client = ObligacionesClient(load_cached_session=False)
        self.reportes_client   = ReportesClient(load_cached_session=False)
        self.periodos_client   = PeriodosClient(load_cached_session=False)

        for client in (self.pagos_client, self.alumno_client,
                       self.matricula_client, self.obligacion_client,
                   self.reportes_client, self.periodos_client):
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
        - Financiero:       GET /pagos/resumen/matricula/{matricula_id}
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

        # 3. Resumen financiero via /pagos/resumen/matricula/{matricula_id}
        costo_total = 0.0
        pagado      = 0.0
        deuda       = 0.0
        if matricula_id:
            res_ok, resumen = self.pagos_client.obtener_por_matricula(matricula_id)
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
            "matricula_id":    matricula_id,
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

    def obtener_finanzas_historial(self, id_alumno: int, matricula_id: Optional[int] = None) -> Dict:
        """
        Retorna solo datos financieros e historial para refrescos rápidos de UI.
        Evita pedir nuevamente datos personales del alumno cuando no cambiaron.
        """
        matricula_id_local = matricula_id
        if not matricula_id_local:
            mat_ok, matricula = self.matricula_client.obtener_activa_por_alumno(id_alumno)
            if mat_ok and matricula:
                matricula_id_local = matricula.get("id")

        costo_total = 0.0
        pagado = 0.0
        deuda = 0.0
        if matricula_id_local:
            res_ok, resumen = self.pagos_client.obtener_por_matricula(matricula_id_local)
            if res_ok and resumen:
                costo_total = float(resumen.get("total_obligaciones", 0))
                pagado = float(resumen.get("total_pagado", 0))
                deuda = float(resumen.get("saldo_pendiente", 0))

        historial = []
        h_ok, h_data = self.pagos_client.listar_por_alumno(id_alumno)
        if h_ok:
            historial = h_data if isinstance(h_data, list) else h_data.get("items", [])

        return {
            "matricula_id": matricula_id_local,
            "costo": costo_total,
            "pagado": pagado,
            "deuda": deuda,
            "historial": historial,
        }

    # ─────────────────────────────────────────────────────────────────
    # REGISTRO DE PAGO
    # ─────────────────────────────────────────────────────────────────

    def registrar_pago(
        self,
        id_alumno: int,
        monto: float,
        concepto: str,
        matricula_id: Optional[int] = None,
    ) -> Tuple[bool, str]:
        """
        Registra un pago.
        Flujo: Matrícula activa → primera Obligación pendiente/parcial → Pago.
        Si no existe obligación se crea una en el momento.
        """
        # 1. Matrícula activa del alumno (opcionalmente reutiliza matrícula ya resuelta por la UI)
        matricula_id_local = matricula_id
        if not matricula_id_local:
            mat_ok, matricula = self.matricula_client.obtener_activa_por_alumno(id_alumno)
            if not mat_ok or not matricula:
                return False, "El alumno no tiene matrícula activa para este periodo."
            matricula_id_local = matricula.get("id")

        if not matricula_id_local:
            return False, "No se pudo resolver la matrícula activa del alumno."

        # 2. Primera obligación pendiente o parcial
        obl_ok, obl_data = self.obligacion_client.listar(matricula_id=matricula_id_local, limit=50)
        obligaciones = obl_data if isinstance(obl_data, list) else []
        obligacion_id = None
        for obl in obligaciones:
            if obl.get("estado") in ("pendiente", "parcial"):
                obligacion_id = obl.get("id")
                break

        # 3. Si no hay obligación pendiente, crear una ad-hoc
        if not obligacion_id:
            nueva_obl = {
                "matricula_id":      matricula_id_local,
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
        success, result = self.matricula_client.listar(estado="activo", limit=200)
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
        # Normalizar placeholders de UI.
        grupo_norm = None if grupo in (None, "", "Todos", "Todas") else grupo
        modalidad_norm = None if modalidad in (None, "", "Todos", "Todas") else modalidad

        # Si no hay filtros específicos, usar periodo activo para cumplir
        # la regla de backend de consultas no amplias.
        if periodo_id is None and grupo_norm is None and modalidad_norm is None:
            ok_periodo, data_periodo = self.periodos_client.obtener_activo()
            if ok_periodo and isinstance(data_periodo, dict):
                periodo_id = data_periodo.get("id")
            else:
                ok_lista, data_lista = self.periodos_client.listar()
                if ok_lista and isinstance(data_lista, list) and data_lista:
                    periodo_id = data_lista[0].get("id")

        success, result = self.reportes_client.deudores(
            periodo_id=periodo_id,
            grupo=grupo_norm,
            modalidad=modalidad_norm,
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

            # Compatibilidad de claves: backend actual usa "nombre_completo".
            nombre = (
                item.get("alumno_nombre")
                or item.get("nombre_completo")
                or item.get("nombre")
                or "SIN NOMBRE"
            )

            if deuda <= 0.5:
                continue

            pct_deuda = (deuda / costo * 100) if costo else 0.0
            icono, desc, tag = self._clasificar_deuda(pct_deuda)

            registros.append({
                "id":          item.get("alumno_id"),
                "icono":       icono,
                "nombre":      nombre,
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
