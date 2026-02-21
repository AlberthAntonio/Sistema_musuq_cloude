"""
Servicio de Cursos - Lógica de negocio y validaciones.
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.curso import Curso, MallaCurricular
from app.schemas.curso import CursoCreate, CursoUpdate, MallaCurricularCreate


class CursoService:
    """Servicio para operaciones de cursos."""
    
    # ==================== VALIDACIONES ====================
    
    def validar_nombre_unico(self, db: Session, nombre: str, curso_id: Optional[int] = None) -> bool:
        """Verifica si el nombre del curso es único."""
        query = db.query(Curso).filter(Curso.nombre == nombre)
        if curso_id:
            query = query.filter(Curso.id != curso_id)
        return query.first() is None
    
    def validar_malla_unica(self, db: Session, grupo: str, curso_id: int) -> bool:
        """Verifica si la asignación de curso a grupo es única."""
        return db.query(MallaCurricular).filter(
            MallaCurricular.grupo == grupo,
            MallaCurricular.curso_id == curso_id
        ).first() is None
    
    # ==================== OPERACIONES CRUD - CURSO ====================
    
    def listar_cursos(self, db: Session) -> List[Curso]:
        """Listar todos los cursos."""
        return db.query(Curso).order_by(Curso.nombre).all()
    
    def crear_curso(self, db: Session, datos: CursoCreate) -> Curso:
        """Crear nuevo curso."""
        if not self.validar_nombre_unico(db, datos.nombre):
            raise ValueError("Ya existe un curso con ese nombre")
        
        curso = Curso(**datos.model_dump())
        db.add(curso)
        db.commit()
        db.refresh(curso)
        return curso
    
    def obtener_curso(self, db: Session, curso_id: int) -> Optional[Curso]:
        """Obtener curso por ID."""
        return db.query(Curso).filter(Curso.id == curso_id).first()
    
    def actualizar_curso(self, db: Session, curso_id: int, datos: CursoUpdate) -> Curso:
        """Actualizar curso."""
        curso = self.obtener_curso(db, curso_id)
        if not curso:
            raise ValueError("Curso no encontrado")
        
        # Validar nombre único si se cambia
        if datos.nombre and datos.nombre != curso.nombre:
            if not self.validar_nombre_unico(db, datos.nombre, curso_id):
                raise ValueError("Ya existe un curso con ese nombre")
        
        update_data = datos.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(curso, field, value)
        
        db.commit()
        db.refresh(curso)
        return curso
    
    def eliminar_curso(self, db: Session, curso_id: int) -> bool:
        """Eliminar curso."""
        curso = self.obtener_curso(db, curso_id)
        if not curso:
            raise ValueError("Curso no encontrado")
        
        db.delete(curso)
        db.commit()
        return True
    
    # ==================== OPERACIONES - MALLA CURRICULAR ====================
    
    def listar_malla(self, db: Session, grupo: Optional[str] = None) -> List[MallaCurricular]:
        """Listar asignaciones de malla curricular."""
        query = db.query(MallaCurricular)
        if grupo:
            query = query.filter(MallaCurricular.grupo == grupo)
        return query.all()
    
    def asignar_curso_a_grupo(self, db: Session, datos: MallaCurricularCreate) -> MallaCurricular:
        """Asignar un curso a un grupo."""
        # Validar curso existe
        if not self.obtener_curso(db, datos.curso_id):
            raise ValueError("Curso no encontrado")
        
        # Validar asignación única
        if not self.validar_malla_unica(db, datos.grupo, datos.curso_id):
            raise ValueError("Este curso ya está asignado a este grupo")
        
        malla = MallaCurricular(**datos.model_dump())
        db.add(malla)
        db.commit()
        db.refresh(malla)
        return malla
    
    def quitar_curso_de_grupo(self, db: Session, malla_id: int) -> bool:
        """Quitar asignación de curso de grupo."""
        malla = db.query(MallaCurricular).filter(MallaCurricular.id == malla_id).first()
        if not malla:
            raise ValueError("Asignación no encontrada")
        
        db.delete(malla)
        db.commit()
        return True
    
    def cursos_por_grupo(self, db: Session, grupo: str) -> List[Curso]:
        """Obtener cursos asignados a un grupo."""
        mallas = db.query(MallaCurricular).filter(MallaCurricular.grupo == grupo).all()
        return [m.curso for m in mallas if m.curso]


# Instancia global del servicio
curso_service = CursoService()
