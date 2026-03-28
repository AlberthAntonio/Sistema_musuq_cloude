"""
Servicio de Periodos Académicos - CRUD y lógica de negocio.
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.periodo import PeriodoAcademico
from app.schemas.periodo import PeriodoCreate, PeriodoUpdate


class PeriodoService:
    """Servicio para operaciones de periodos académicos."""
    
    def listar(self, db: Session) -> List[PeriodoAcademico]:
        """Listar todos los periodos académicos."""
        return db.query(PeriodoAcademico).order_by(
            PeriodoAcademico.fecha_inicio.desc()
        ).all()
    
    def crear(self, db: Session, datos: PeriodoCreate, usuario_actual_id: Optional[int] = None) -> PeriodoAcademico:
        """Crear nuevo periodo académico."""
        # Validar nombre único
        existente = db.query(PeriodoAcademico).filter(
            PeriodoAcademico.nombre == datos.nombre
        ).first()
        if existente:
            raise ValueError(f"Ya existe un periodo con el nombre '{datos.nombre}'")
        
        # Validar fechas
        if datos.fecha_fin <= datos.fecha_inicio:
            raise ValueError("La fecha de fin debe ser posterior a la fecha de inicio")
        
        periodo = PeriodoAcademico(**datos.model_dump())
        if usuario_actual_id:
            periodo.creado_por = usuario_actual_id
        db.add(periodo)
        db.commit()
        db.refresh(periodo)
        return periodo
    
    def obtener_por_id(self, db: Session, periodo_id: int) -> Optional[PeriodoAcademico]:
        """Obtener periodo por ID."""
        return db.query(PeriodoAcademico).filter(
            PeriodoAcademico.id == periodo_id
        ).first()
    
    def obtener_activo(self, db: Session) -> Optional[PeriodoAcademico]:
        """Obtener el periodo activo actual."""
        return db.query(PeriodoAcademico).filter(
            PeriodoAcademico.estado == "activo"
        ).first()
    
    def actualizar(self, db: Session, periodo_id: int, datos: PeriodoUpdate) -> PeriodoAcademico:
        """Actualizar periodo académico."""
        periodo = self.obtener_por_id(db, periodo_id)
        if not periodo:
            raise ValueError("Periodo no encontrado")
        
        for field, value in datos.model_dump(exclude_unset=True).items():
            setattr(periodo, field, value)
        
        db.commit()
        db.refresh(periodo)
        return periodo
    
    def cerrar(self, db: Session, periodo_id: int) -> PeriodoAcademico:
        """Cerrar un periodo académico."""
        periodo = self.obtener_por_id(db, periodo_id)
        if not periodo:
            raise ValueError("Periodo no encontrado")
        
        periodo.estado = "cerrado"
        db.commit()
        db.refresh(periodo)
        return periodo
    
    def eliminar(self, db: Session, periodo_id: int) -> bool:
        """Eliminar periodo académico."""
        periodo = self.obtener_por_id(db, periodo_id)
        if not periodo:
            raise ValueError("Periodo no encontrado")
        
        db.delete(periodo)
        db.commit()
        return True


periodo_service = PeriodoService()
