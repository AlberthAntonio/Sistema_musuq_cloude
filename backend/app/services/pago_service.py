"""
Servicio de Pagos - Pagos vinculados a obligaciones.
"""
from typing import List, Optional, Dict, Any
from datetime import date
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models.pago import Pago
from app.models.obligacion import ObligacionPago
from app.models.matricula import Matricula
from app.models.alumno import Alumno
from app.schemas.pago import PagoCreate, PagoUpdate


class PagoService:
    """Servicio para operaciones de pagos."""

    def __init__(self, repo=None):
        from app.repositories.pago_repository import pago_repo
        self.repo = repo or pago_repo
    
    def listar(
        self,
        db: Session,
        obligacion_id: Optional[int] = None,
        periodo_id: Optional[int] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        alumno_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Listar pagos con filtros. Delega a repository."""
        from app.repositories.pago_repository import PagoQuerySpec
        spec = PagoQuerySpec(
            obligacion_id=obligacion_id,
            periodo_id=periodo_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            alumno_id=alumno_id,
            with_eager=True,
            skip=skip,
            limit=limit,
        )
        pagos = self.repo.find_all(db, spec)
        
        resultado = []
        for pago in pagos:
            obligacion = pago.obligacion
            matricula = obligacion.matricula if obligacion else None
            alumno = matricula.alumno if matricula else None
            
            resultado.append({
                "id": pago.id,
                "obligacion_id": pago.obligacion_id,
                "obligacion_concepto": obligacion.concepto if obligacion else None,
                "alumno_nombre": f"{alumno.nombres} {alumno.apell_paterno}" if alumno else None,
                "alumno_dni": alumno.dni if alumno else None,
                "monto": pago.monto,
                "fecha": pago.fecha,
                "concepto": pago.concepto,
                "fecha_registro": pago.fecha_registro,
                "creado_por": pago.creado_por
            })
        return resultado

    def contar(
        self,
        db: Session,
        obligacion_id: Optional[int] = None,
        periodo_id: Optional[int] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        alumno_id: Optional[int] = None,
    ) -> int:
        """Cuenta total de pagos filtrados para paginación delegando a repositorio."""
        from app.repositories.pago_repository import PagoQuerySpec
        spec = PagoQuerySpec(
            obligacion_id=obligacion_id,
            periodo_id=periodo_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            alumno_id=alumno_id,
            with_eager=False,
        )
        return self.repo.count_all(db, spec)
    
    def crear(self, db: Session, datos: PagoCreate, usuario_actual_id: Optional[int] = None) -> Pago:
        """
        Registrar nuevo pago.
        Actualiza automáticamente monto_pagado y estado en la obligación.
        """
        # Validar que la obligación existe
        obligacion = db.query(ObligacionPago).filter(
            ObligacionPago.id == datos.obligacion_id
        ).first()
        if not obligacion:
            raise ValueError("Obligación de pago no encontrada")
        
        # Validar que el monto no exceda el saldo pendiente
        saldo = obligacion.monto_total - obligacion.monto_pagado
        if datos.monto > saldo:
            raise ValueError(
                f"El monto ({datos.monto}) excede el saldo pendiente ({saldo:.2f})"
            )
        
        # Crear el pago
        pago = Pago(**datos.model_dump())
        if usuario_actual_id:
            pago.creado_por = usuario_actual_id
        db.add(pago)
        
        # Actualizar la obligación
        obligacion.monto_pagado += datos.monto
        obligacion.actualizar_estado()
        
        db.commit()
        db.refresh(pago)
        return pago
    
    def obtener_por_id(self, db: Session, pago_id: int) -> Optional[Pago]:
        """Obtener pago por ID."""
        return db.query(Pago).filter(Pago.id == pago_id).first()
    
    def resumen_por_matricula(self, db: Session, matricula_id: int) -> Dict[str, Any]:
        """Obtener resumen de pagos de una matrícula. Optimizado: 1 query en vez de N+1."""
        # Obtener la matrícula
        matricula = db.query(Matricula.id, Matricula.codigo_matricula).filter(
            Matricula.id == matricula_id
        ).first()
        if not matricula:
            raise ValueError("Matrícula no encontrada")
        
        # Una sola query con aggregation para todo
        result = db.query(
            func.sum(ObligacionPago.monto_total).label("total_obligaciones"),
            func.sum(ObligacionPago.monto_pagado).label("total_pagado"),
        ).filter(
            ObligacionPago.matricula_id == matricula_id
        ).first()
        
        total_obligaciones = round(result.total_obligaciones or 0, 2)
        total_pagado = round(result.total_pagado or 0, 2)
        
        # Contar pagos y obtener último pago en una sola query
        pago_stats = db.query(
            func.count(Pago.id).label("cantidad"),
            func.max(Pago.fecha).label("ultimo_pago"),
        ).join(
            ObligacionPago, Pago.obligacion_id == ObligacionPago.id
        ).filter(
            ObligacionPago.matricula_id == matricula_id
        ).first()
        
        return {
            "matricula_id": matricula_id,
            "codigo_matricula": matricula.codigo_matricula,
            "total_obligaciones": total_obligaciones,
            "total_pagado": total_pagado,
            "saldo_pendiente": round(total_obligaciones - total_pagado, 2),
            "cantidad_pagos": pago_stats.cantidad or 0,
            "ultimo_pago": pago_stats.ultimo_pago
        }
    
    def actualizar(self, db: Session, pago_id: int, datos: PagoUpdate) -> Pago:
        """Actualizar pago (solo campos editables, no recalcula obligación)."""
        pago = self.obtener_por_id(db, pago_id)
        if not pago:
            raise ValueError("Pago no encontrado")
        
        for field, value in datos.model_dump(exclude_unset=True).items():
            setattr(pago, field, value)
        
        db.commit()
        db.refresh(pago)
        return pago
    
    def eliminar(self, db: Session, pago_id: int) -> bool:
        """
        Eliminar pago y revertir el monto en la obligación.
        """
        pago = self.obtener_por_id(db, pago_id)
        if not pago:
            raise ValueError("Pago no encontrado")
        
        # Revertir monto en la obligación
        obligacion = db.query(ObligacionPago).filter(
            ObligacionPago.id == pago.obligacion_id
        ).first()
        if obligacion:
            obligacion.monto_pagado = max(0.0, obligacion.monto_pagado - pago.monto)
            obligacion.actualizar_estado()
        
        db.delete(pago)
        db.commit()
        return True


pago_service = PagoService()
