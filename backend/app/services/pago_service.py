"""
Servicio de Pagos - Lógica de pagos de alumnos.
"""
from typing import List, Optional, Dict, Any
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.pago import Pago
from app.models.alumno import Alumno
from app.schemas.pago import PagoCreate, PagoUpdate


class PagoService:
    """Servicio para operaciones de pagos."""
    
    def listar(
        self, 
        db: Session,
        alumno_id: Optional[int] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """Listar pagos con filtros."""
        query = db.query(Pago)
        
        if alumno_id:
            query = query.filter(Pago.alumno_id == alumno_id)
        if fecha_desde:
            query = query.filter(Pago.fecha >= fecha_desde)
        if fecha_hasta:
            query = query.filter(Pago.fecha <= fecha_hasta)
        
        pagos = query.order_by(Pago.fecha.desc()).all()
        
        resultado = []
        for pago in pagos:
            alumno = db.query(Alumno).filter(Alumno.id == pago.alumno_id).first()
            resultado.append({
                "id": pago.id,
                "alumno_id": pago.alumno_id,
                "alumno_nombre": f"{alumno.nombres} {alumno.apell_paterno}" if alumno else None,
                "alumno_codigo": alumno.codigo_matricula if alumno else None,
                "monto": pago.monto,
                "fecha": pago.fecha,
                "concepto": pago.concepto,
                "fecha_registro": pago.fecha_registro
            })
        return resultado
    
    def crear(self, db: Session, datos: PagoCreate) -> Pago:
        """Registrar nuevo pago."""
        # Validar alumno existe
        alumno = db.query(Alumno).filter(Alumno.id == datos.alumno_id).first()
        if not alumno:
            raise ValueError("Alumno no encontrado")
        
        pago = Pago(**datos.model_dump())
        db.add(pago)
        db.commit()
        db.refresh(pago)
        return pago
    
    def obtener_por_id(self, db: Session, pago_id: int) -> Optional[Pago]:
        """Obtener pago por ID."""
        return db.query(Pago).filter(Pago.id == pago_id).first()
    
    def resumen_por_alumno(self, db: Session, alumno_id: int) -> Dict[str, Any]:
        """Obtener resumen de pagos de un alumno."""
        pagos = db.query(Pago).filter(Pago.alumno_id == alumno_id).all()
        
        total = sum(p.monto for p in pagos)
        ultimo = max((p.fecha for p in pagos), default=None) if pagos else None
        
        return {
            "alumno_id": alumno_id,
            "total_pagado": total,
            "cantidad_pagos": len(pagos),
            "ultimo_pago": ultimo
        }
    
    def actualizar(self, db: Session, pago_id: int, datos: PagoUpdate) -> Pago:
        """Actualizar pago."""
        pago = self.obtener_por_id(db, pago_id)
        if not pago:
            raise ValueError("Pago no encontrado")
        
        for field, value in datos.model_dump(exclude_unset=True).items():
            setattr(pago, field, value)
        
        db.commit()
        db.refresh(pago)
        return pago
    
    def eliminar(self, db: Session, pago_id: int) -> bool:
        """Eliminar pago."""
        pago = self.obtener_por_id(db, pago_id)
        if not pago:
            raise ValueError("Pago no encontrado")
        
        db.delete(pago)
        db.commit()
        return True


pago_service = PagoService()
