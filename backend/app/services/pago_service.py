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
    
    def listar(
        self,
        db: Session,
        obligacion_id: Optional[int] = None,
        periodo_id: Optional[int] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        alumno_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Listar pagos con filtros. Usa eager loading para evitar N+1 queries."""
        query = db.query(Pago).options(
            joinedload(Pago.obligacion).joinedload(ObligacionPago.matricula).joinedload(Matricula.alumno)
        )

        if obligacion_id:
            query = query.filter(Pago.obligacion_id == obligacion_id)

        # Filtro por alumno o periodo requiere joins hasta Matricula
        if alumno_id or periodo_id:
            query = query\
                .join(ObligacionPago, Pago.obligacion_id == ObligacionPago.id)\
                .join(Matricula, ObligacionPago.matricula_id == Matricula.id)
            if periodo_id:
                query = query.filter(Matricula.periodo_id == periodo_id)
            if alumno_id:
                query = query.filter(Matricula.alumno_id == alumno_id)
        
        if fecha_desde:
            query = query.filter(Pago.fecha >= fecha_desde)
        if fecha_hasta:
            query = query.filter(Pago.fecha <= fecha_hasta)
        
        pagos = query.order_by(Pago.fecha.desc()).all()
        
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
        """Obtener resumen de pagos de una matrícula."""
        # Obtener la matrícula
        matricula = db.query(Matricula).filter(Matricula.id == matricula_id).first()
        if not matricula:
            raise ValueError("Matrícula no encontrada")
        
        # Obtener todas las obligaciones de esta matrícula
        obligaciones = db.query(ObligacionPago).filter(
            ObligacionPago.matricula_id == matricula_id
        ).all()
        
        total_obligaciones = sum(o.monto_total for o in obligaciones)
        total_pagado = sum(o.monto_pagado for o in obligaciones)
        
        # Obtener último pago
        ultimo_pago_fecha = None
        for obligacion in obligaciones:
            pagos = db.query(Pago).filter(Pago.obligacion_id == obligacion.id).all()
            for p in pagos:
                if ultimo_pago_fecha is None or p.fecha > ultimo_pago_fecha:
                    ultimo_pago_fecha = p.fecha
        
        # Contar pagos totales
        obligacion_ids = [o.id for o in obligaciones]
        cantidad_pagos = db.query(Pago).filter(
            Pago.obligacion_id.in_(obligacion_ids)
        ).count() if obligacion_ids else 0
        
        return {
            "matricula_id": matricula_id,
            "codigo_matricula": matricula.codigo_matricula,
            "total_obligaciones": total_obligaciones,
            "total_pagado": total_pagado,
            "saldo_pendiente": total_obligaciones - total_pagado,
            "cantidad_pagos": cantidad_pagos,
            "ultimo_pago": ultimo_pago_fecha
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
