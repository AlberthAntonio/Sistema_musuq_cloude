"""
Servicio de Obligaciones de Pago - CRUD y lógica de estados.
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.obligacion import ObligacionPago
from app.models.matricula import Matricula
from app.schemas.obligacion import ObligacionCreate, ObligacionUpdate


class ObligacionService:
    """Servicio para operaciones de obligaciones de pago."""
    
    def listar(
        self,
        db: Session,
        matricula_id: Optional[int] = None,
        periodo_id: Optional[int] = None,
        estado: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ObligacionPago]:
        """Listar obligaciones con filtros opcionales."""
        query = db.query(ObligacionPago)
        
        if matricula_id:
            query = query.filter(ObligacionPago.matricula_id == matricula_id)
        if periodo_id:
            query = query.join(Matricula).filter(Matricula.periodo_id == periodo_id)
        if estado:
            query = query.filter(ObligacionPago.estado == estado)
        
        return query.order_by(ObligacionPago.fecha_vencimiento).offset(skip).limit(limit).all()
    
    def crear(self, db: Session, datos: ObligacionCreate, usuario_actual_id: Optional[int] = None) -> ObligacionPago:
        """Crear nueva obligación de pago."""
        # Validar que la matrícula existe
        matricula = db.query(Matricula).filter(
            Matricula.id == datos.matricula_id
        ).first()
        if not matricula:
            raise ValueError("Matrícula no encontrada")
        
        obligacion = ObligacionPago(**datos.model_dump())
        if usuario_actual_id:
            obligacion.creado_por = usuario_actual_id
        db.add(obligacion)
        db.commit()
        db.refresh(obligacion)
        return obligacion
    
    def obtener_por_id(self, db: Session, obligacion_id: int) -> Optional[ObligacionPago]:
        """Obtener obligación por ID."""
        return db.query(ObligacionPago).filter(
            ObligacionPago.id == obligacion_id
        ).first()
    
    def actualizar(self, db: Session, obligacion_id: int, datos: ObligacionUpdate) -> ObligacionPago:
        """Actualizar obligación de pago."""
        obligacion = self.obtener_por_id(db, obligacion_id)
        if not obligacion:
            raise ValueError("Obligación no encontrada")
        
        for field, value in datos.model_dump(exclude_unset=True).items():
            setattr(obligacion, field, value)
        
        db.commit()
        db.refresh(obligacion)
        return obligacion
    
    def eliminar(self, db: Session, obligacion_id: int) -> bool:
        """Eliminar obligación de pago."""
        obligacion = self.obtener_por_id(db, obligacion_id)
        if not obligacion:
            raise ValueError("Obligación no encontrada")
        
        db.delete(obligacion)
        db.commit()
        return True


obligacion_service = ObligacionService()
