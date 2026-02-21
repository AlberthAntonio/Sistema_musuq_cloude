"""
Servicio de Sesiones de Examen - Lógica de sesiones y notas.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.sesion import SesionExamen
from app.models.nota import Nota
from app.schemas.sesion import SesionCreate, SesionUpdate


class SesionService:
    """Servicio para operaciones de sesiones de examen."""
    
    def listar(self, db: Session, estado: Optional[str] = None) -> List[SesionExamen]:
        """Listar sesiones con filtro opcional por estado."""
        query = db.query(SesionExamen)
        if estado:
            query = query.filter(SesionExamen.estado == estado)
        return query.order_by(SesionExamen.fecha.desc()).all()
    
    def crear(self, db: Session, datos: SesionCreate) -> SesionExamen:
        """Crear nueva sesión."""
        sesion = SesionExamen(**datos.model_dump())
        db.add(sesion)
        db.commit()
        db.refresh(sesion)
        return sesion
    
    def obtener_por_id(self, db: Session, sesion_id: int) -> Optional[SesionExamen]:
        """Obtener sesión por ID."""
        return db.query(SesionExamen).filter(SesionExamen.id == sesion_id).first()
    
    def obtener_con_notas(self, db: Session, sesion_id: int) -> Optional[Dict[str, Any]]:
        """Obtener sesión con sus notas."""
        sesion = self.obtener_por_id(db, sesion_id)
        if not sesion:
            return None
        
        notas = db.query(Nota).filter(Nota.sesion_id == sesion_id).all()
        
        return {
            "id": sesion.id,
            "fecha": sesion.fecha,
            "nombre": sesion.nombre,
            "estado": sesion.estado,
            "fecha_creacion": sesion.fecha_creacion,
            "notas": [{"id": n.id, "alumno_id": n.alumno_id, "curso_nombre": n.curso_nombre, "valor": n.valor} for n in notas]
        }
    
    def actualizar(self, db: Session, sesion_id: int, datos: SesionUpdate) -> SesionExamen:
        """Actualizar sesión."""
        sesion = self.obtener_por_id(db, sesion_id)
        if not sesion:
            raise ValueError("Sesión no encontrada")
        
        for field, value in datos.model_dump(exclude_unset=True).items():
            setattr(sesion, field, value)
        
        db.commit()
        db.refresh(sesion)
        return sesion
    
    def cerrar_sesion(self, db: Session, sesion_id: int) -> SesionExamen:
        """Cerrar una sesión de examen."""
        sesion = self.obtener_por_id(db, sesion_id)
        if not sesion:
            raise ValueError("Sesión no encontrada")
        
        sesion.estado = "Cerrado"
        db.commit()
        db.refresh(sesion)
        return sesion
    
    def eliminar(self, db: Session, sesion_id: int) -> bool:
        """Eliminar sesión."""
        sesion = self.obtener_por_id(db, sesion_id)
        if not sesion:
            raise ValueError("Sesión no encontrada")
        
        db.delete(sesion)
        db.commit()
        return True


sesion_service = SesionService()
