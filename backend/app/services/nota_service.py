"""
Servicio de Notas - Lógica de calificaciones.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.nota import Nota
from app.models.alumno import Alumno
from app.models.sesion import SesionExamen
from app.schemas.nota import NotaCreate, NotaUpdate


class NotaService:
    """Servicio para operaciones de notas."""
    
    def listar_por_sesion(self, db: Session, sesion_id: int) -> List[Dict[str, Any]]:
        """Listar notas de una sesión con info del alumno."""
        notas = db.query(Nota).filter(Nota.sesion_id == sesion_id).all()
        resultado = []
        for nota in notas:
            alumno = db.query(Alumno).filter(Alumno.id == nota.alumno_id).first()
            resultado.append({
                "id": nota.id,
                "alumno_id": nota.alumno_id,
                "alumno_nombre": f"{alumno.nombres} {alumno.apell_paterno}" if alumno else None,
                "curso_nombre": nota.curso_nombre,
                "valor": nota.valor
            })
        return resultado
    
    def listar_por_alumno(self, db: Session, alumno_id: int) -> List[Dict[str, Any]]:
        """Listar notas de un alumno con info de sesión."""
        notas = db.query(Nota).filter(Nota.alumno_id == alumno_id).all()
        resultado = []
        for nota in notas:
            sesion = db.query(SesionExamen).filter(SesionExamen.id == nota.sesion_id).first()
            resultado.append({
                "id": nota.id,
                "sesion_id": nota.sesion_id,
                "sesion_nombre": sesion.nombre if sesion else None,
                "curso_nombre": nota.curso_nombre,
                "valor": nota.valor
            })
        return resultado
    
    def crear(self, db: Session, datos: NotaCreate) -> Nota:
        """Crear nueva nota."""
        # Validar alumno existe
        alumno = db.query(Alumno).filter(Alumno.id == datos.alumno_id).first()
        if not alumno:
            raise ValueError("Alumno no encontrado")
        
        # Validar sesión existe
        sesion = db.query(SesionExamen).filter(SesionExamen.id == datos.sesion_id).first()
        if not sesion:
            raise ValueError("Sesión no encontrada")
        
        nota = Nota(**datos.model_dump())
        db.add(nota)
        db.commit()
        db.refresh(nota)
        return nota
    
    def crear_masivo(self, db: Session, sesion_id: int, notas_data: List[dict]) -> List[Nota]:
        """Crear notas masivamente para una sesión."""
        notas_creadas = []
        for data in notas_data:
            nota = Nota(
                sesion_id=sesion_id,
                alumno_id=data["alumno_id"],
                curso_nombre=data["curso_nombre"],
                valor=data["valor"]
            )
            db.add(nota)
            notas_creadas.append(nota)
        
        db.commit()
        return notas_creadas
    
    def obtener_por_id(self, db: Session, nota_id: int) -> Optional[Nota]:
        """Obtener nota por ID."""
        return db.query(Nota).filter(Nota.id == nota_id).first()
    
    def actualizar(self, db: Session, nota_id: int, datos: NotaUpdate) -> Nota:
        """Actualizar nota."""
        nota = self.obtener_por_id(db, nota_id)
        if not nota:
            raise ValueError("Nota no encontrada")
        
        for field, value in datos.model_dump(exclude_unset=True).items():
            setattr(nota, field, value)
        
        db.commit()
        db.refresh(nota)
        return nota
    
    def eliminar(self, db: Session, nota_id: int) -> bool:
        """Eliminar nota."""
        nota = self.obtener_por_id(db, nota_id)
        if not nota:
            raise ValueError("Nota no encontrada")
        
        db.delete(nota)
        db.commit()
        return True


nota_service = NotaService()
