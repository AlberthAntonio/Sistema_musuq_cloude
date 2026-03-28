"""
Servicio de Reportes Consolidados.
Genera estadísticas y resúmenes que el desktop antes calculaba en cliente.
Evita el patrón N×2 requests y mejora el rendimiento considerablemente.
"""
from typing import List, Dict, Any, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case

from app.models.alumno import Alumno
from app.models.matricula import Matricula
from app.models.obligacion import ObligacionPago
from app.models.pago import Pago
from app.models.asistencia import Asistencia
from app.models.periodo import PeriodoAcademico


class ReporteService:
    """Servicio de reportes consolidados del sistema."""

    # ================================================================
    # REPORTE DE DEUDORES
    # ================================================================

    def reporte_deudores(
        self,
        db: Session,
        periodo_id: Optional[int] = None,
        grupo: Optional[str] = None,
        modalidad: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Lista alumnos con saldo pendiente > 0.
        Una sola consulta SQL en lugar de N×2 requests desde el cliente.
        """
        query = (
            db.query(
                Alumno.id.label("alumno_id"),
                Alumno.dni,
                Alumno.nombres,
                Alumno.apell_paterno,
                Alumno.apell_materno,
                Matricula.id.label("matricula_id"),
                Matricula.codigo_matricula,
                Matricula.grupo,
                Matricula.modalidad,
                Matricula.horario,
                func.sum(ObligacionPago.monto_total).label("total_obligaciones"),
                func.sum(ObligacionPago.monto_pagado).label("total_pagado"),
                (
                    func.sum(ObligacionPago.monto_total) - func.sum(ObligacionPago.monto_pagado)
                ).label("saldo_pendiente"),
            )
            .join(Matricula, Matricula.alumno_id == Alumno.id)
            .join(ObligacionPago, ObligacionPago.matricula_id == Matricula.id)
            .filter(
                Matricula.estado == "activo",
                Alumno.activo == True,
            )
        )

        if periodo_id:
            query = query.filter(Matricula.periodo_id == periodo_id)
        if grupo:
            query = query.filter(Matricula.grupo == grupo)
        if modalidad:
            query = query.filter(Matricula.modalidad == modalidad)

        query = (
            query
            .group_by(
                Alumno.id, Alumno.dni, Alumno.nombres,
                Alumno.apell_paterno, Alumno.apell_materno,
                Matricula.id, Matricula.codigo_matricula,
                Matricula.grupo, Matricula.modalidad, Matricula.horario,
            )
            .having(
                (func.sum(ObligacionPago.monto_total) - func.sum(ObligacionPago.monto_pagado)) > 0
            )
            .order_by(Alumno.apell_paterno, Alumno.apell_materno)
        )

        resultados = query.all()
        return [
            {
                "alumno_id": r.alumno_id,
                "dni": r.dni,
                "nombre_completo": f"{r.apell_paterno} {r.apell_materno}, {r.nombres}",
                "matricula_id": r.matricula_id,
                "codigo_matricula": r.codigo_matricula,
                "grupo": r.grupo,
                "modalidad": r.modalidad,
                "horario": r.horario,
                "total_obligaciones": round(r.total_obligaciones or 0, 2),
                "total_pagado": round(r.total_pagado or 0, 2),
                "saldo_pendiente": round(r.saldo_pendiente or 0, 2),
            }
            for r in resultados
        ]

    # ================================================================
    # REPORTE DE ASISTENCIA CONSOLIDADO
    # ================================================================

    def reporte_asistencia_resumen(
        self,
        db: Session,
        periodo_id: Optional[int] = None,
        grupo: Optional[str] = None,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """
        Resumen de asistencia por alumno: conteos de puntual/tardanza/falta y porcentaje.
        """
        puntual_expr = func.sum(case((Asistencia.estado == "PUNTUAL", 1), else_=0))
        tardanza_expr = func.sum(case((Asistencia.estado == "TARDANZA", 1), else_=0))
        falta_expr = func.sum(case((Asistencia.estado == "INASISTENCIA", 1), else_=0))

        query = (
            db.query(
                Alumno.id.label("alumno_id"),
                Alumno.dni,
                Alumno.nombres,
                Alumno.apell_paterno,
                Alumno.apell_materno,
                Matricula.codigo_matricula,
                Matricula.grupo,
                func.count(Asistencia.id).label("total"),
                puntual_expr.label("puntual"),
                tardanza_expr.label("tardanza"),
                falta_expr.label("falta"),
            )
            .join(Asistencia, Asistencia.alumno_id == Alumno.id)
            .join(Matricula, and_(Matricula.alumno_id == Alumno.id, Matricula.estado == "activo"))
            .filter(Alumno.activo == True)
        )

        if periodo_id:
            query = query.filter(
                Asistencia.periodo_id == periodo_id,
                Matricula.periodo_id == periodo_id,
            )
        if grupo:
            query = query.filter(Matricula.grupo == grupo)
        if fecha_inicio:
            query = query.filter(Asistencia.fecha >= fecha_inicio)
        if fecha_fin:
            query = query.filter(Asistencia.fecha <= fecha_fin)

        query = query.group_by(
            Alumno.id, Alumno.dni, Alumno.nombres,
            Alumno.apell_paterno, Alumno.apell_materno,
            Matricula.codigo_matricula, Matricula.grupo,
        ).order_by(Alumno.apell_paterno, Alumno.apell_materno)

        resultados = query.all()
        resultado_final = []
        for r in resultados:
            total = r.total or 0
            puntual = r.puntual or 0
            tardanza = r.tardanza or 0
            falta = r.falta or 0
            porcentaje = round((puntual + tardanza) / total * 100, 1) if total > 0 else 0.0
            resultado_final.append({
                "alumno_id": r.alumno_id,
                "dni": r.dni,
                "nombre_completo": f"{r.apell_paterno} {r.apell_materno}, {r.nombres}",
                "codigo_matricula": r.codigo_matricula,
                "grupo": r.grupo,
                "total_registros": total,
                "puntual": puntual,
                "tardanza": tardanza,
                "falta": falta,
                "porcentaje_asistencia": porcentaje,
            })
        return resultado_final

    # ================================================================
    # REPORTE DE TARDANZAS
    # ================================================================

    def reporte_tardanzas(
        self,
        db: Session,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        grupo: Optional[str] = None,
        turno: Optional[str] = None,
        periodo_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Lista todos los registros de TARDANZA en el rango dado.
        Reemplaza el loop de 500-en-500 del cliente desktop.
        """
        query = (
            db.query(
                Asistencia.id,
                Asistencia.fecha,
                Asistencia.hora,
                Asistencia.turno,
                Asistencia.observacion,
                Alumno.id.label("alumno_id"),
                Alumno.dni,
                Alumno.nombres,
                Alumno.apell_paterno,
                Alumno.apell_materno,
                Alumno.celular_padre_1,
                Matricula.codigo_matricula,
                Matricula.grupo,
                Matricula.modalidad,
            )
            .join(Alumno, Asistencia.alumno_id == Alumno.id)
            .outerjoin(
                Matricula,
                and_(
                    Matricula.alumno_id == Alumno.id,
                    Matricula.estado == "activo",
                ),
            )
            .filter(Asistencia.estado == "TARDANZA")
        )

        if fecha_inicio:
            query = query.filter(Asistencia.fecha >= fecha_inicio)
        if fecha_fin:
            query = query.filter(Asistencia.fecha <= fecha_fin)
        if grupo:
            query = query.filter(Matricula.grupo == grupo)
        if turno:
            query = query.filter(Asistencia.turno == turno)
        if periodo_id:
            query = query.filter(Asistencia.periodo_id == periodo_id)

        query = query.order_by(Asistencia.fecha.desc(), Alumno.apell_paterno)
        resultados = query.all()

        return [
            {
                "asistencia_id": r.id,
                "fecha": r.fecha,
                "hora": str(r.hora) if r.hora else None,
                "turno": r.turno,
                "observacion": r.observacion,
                "alumno_id": r.alumno_id,
                "dni": r.dni,
                "nombre_completo": f"{r.apell_paterno} {r.apell_materno}, {r.nombres}",
                "celular_padre": r.celular_padre_1,
                "codigo_matricula": r.codigo_matricula,
                "grupo": r.grupo,
                "modalidad": r.modalidad,
            }
            for r in resultados
        ]

    # ================================================================
    # ESTADÍSTICAS GENERALES DEL PERIODO
    # ================================================================

    def estadisticas_periodo(self, db: Session, periodo_id: int) -> Dict[str, Any]:
        """
        Resumen estadístico de un periodo académico:
        total alumnos, pagos, deuda pendiente, asistencia promedio.
        """
        periodo = db.query(PeriodoAcademico).filter(PeriodoAcademico.id == periodo_id).first()
        if not periodo:
            raise ValueError("Período académico no encontrado")

        # Total matriculados activos
        total_matriculados = (
            db.query(func.count(Matricula.id))
            .filter(Matricula.periodo_id == periodo_id, Matricula.estado == "activo")
            .scalar()
        ) or 0

        # Totales financieros
        financiero = (
            db.query(
                func.sum(ObligacionPago.monto_total).label("total_obligado"),
                func.sum(ObligacionPago.monto_pagado).label("total_pagado"),
            )
            .join(Matricula, ObligacionPago.matricula_id == Matricula.id)
            .filter(Matricula.periodo_id == periodo_id)
            .first()
        )
        total_obligado = round(financiero.total_obligado or 0, 2)
        total_pagado = round(financiero.total_pagado or 0, 2)

        # Conteo asistencias del periodo
        conteo_asist = (
            db.query(
                func.count(Asistencia.id).label("total"),
                func.sum(case((Asistencia.estado == "PUNTUAL", 1), else_=0)).label("puntual"),
                func.sum(case((Asistencia.estado == "TARDANZA", 1), else_=0)).label("tardanza"),
                func.sum(case((Asistencia.estado == "INASISTENCIA", 1), else_=0)).label("falta"),
            )
            .filter(Asistencia.periodo_id == periodo_id)
            .first()
        )
        total_asist = conteo_asist.total or 0
        puntual_val = conteo_asist.puntual or 0
        tardanza_val = conteo_asist.tardanza or 0
        falta_val = conteo_asist.falta or 0
        porcentaje_asistencia = (
            round((puntual_val + tardanza_val) / total_asist * 100, 1)
            if total_asist > 0 else 0.0
        )

        return {
            "periodo_id": periodo_id,
            "periodo_nombre": periodo.nombre,
            "periodo_estado": periodo.estado,
            "total_matriculados": total_matriculados,
            "total_obligado": total_obligado,
            "total_pagado": total_pagado,
            "saldo_pendiente": round(total_obligado - total_pagado, 2),
            "total_asistencias_registradas": total_asist,
            "porcentaje_asistencia_global": porcentaje_asistencia,
            "puntual": puntual_val,
            "tardanza": tardanza_val,
            "falta": falta_val,
        }


reporte_service = ReporteService()
