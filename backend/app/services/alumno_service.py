"""
Servicio de Alumnos - Lógica de negocio con filtro por periodo.
"""
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.models.alumno import Alumno
from app.models.matricula import Matricula
from app.schemas.alumno import AlumnoCreate, AlumnoUpdate


class AlumnoService:
    """Servicio para operaciones de alumnos."""
    
    # ==================== VALIDACIONES ====================
    
    def validar_dni_unico(self, db: Session, dni: str, alumno_id: Optional[int] = None) -> bool:
        """Verifica si el DNI ya existe. Retorna True si está disponible."""
        query = db.query(Alumno).filter(Alumno.dni == dni)
        if alumno_id:
            query = query.filter(Alumno.id != alumno_id)
        return query.first() is None
    
    # ==================== OPERACIONES CRUD ====================
    
    def __init__(self, repo=None):
        from app.repositories.alumno_repository import alumno_repo
        self.repo = repo or alumno_repo

    def listar(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        activo: Optional[bool] = True,
        periodo_id: Optional[int] = None,
        grupo: Optional[str] = None,
        modalidad: Optional[str] = None,
        buscar: Optional[str] = None,
    ) -> List[Alumno]:
        """
        Listar alumnos con filtros opcionales derivados al Repositorio.
        """
        from app.repositories.alumno_repository import AlumnoQuerySpec
        spec = AlumnoQuerySpec(
            activo=activo,
            periodo_id=periodo_id,
            grupo=grupo,
            modalidad=modalidad,
            skip=skip,
            limit=limit,
            buscar=buscar,
        )
        return self.repo.find_all(db, spec)

    def contar(
        self,
        db: Session,
        activo: Optional[bool] = True,
        periodo_id: Optional[int] = None,
        grupo: Optional[str] = None,
        modalidad: Optional[str] = None,
        buscar: Optional[str] = None,
    ) -> int:
        """Cuenta total de alumnos delegando al Repositorio."""
        from app.repositories.alumno_repository import AlumnoQuerySpec
        spec = AlumnoQuerySpec(
            activo=activo,
            periodo_id=periodo_id,
            grupo=grupo,
            modalidad=modalidad,
            buscar=buscar,
        )
        return self.repo.count_all(db, spec)
    
    def crear(self, db: Session, datos: AlumnoCreate, usuario_actual_id: Optional[int] = None) -> Alumno:
        """Crear nuevo alumno usando repositorio."""
        if not self.validar_dni_unico(db, datos.dni):
            raise ValueError("El DNI ya está registrado")
        
        return self.repo.create(db, obj_in=datos, creado_por=usuario_actual_id)
    
    def obtener_por_id(self, db: Session, alumno_id: int) -> Optional[Alumno]:
        """Obtener alumno por ID usando repo."""
        return self.repo.get(db, alumno_id)
    
    def obtener_por_dni(self, db: Session, dni: str) -> Optional[Alumno]:
        """Obtener alumno por DNI usando repo."""
        return self.repo.get_by_dni(db, dni)
    
    def buscar(
        self, 
        db: Session, 
        termino: str, 
        limite: int = 20,
        periodo_id: Optional[int] = None
    ) -> List[Alumno]:
        """
        Buscar alumnos por nombre, apellido o DNI usando especificacion.
        """
        return self.listar(db, skip=0, limit=limite, buscar=termino, periodo_id=periodo_id)
    
    def actualizar(self, db: Session, alumno_id: int, datos: AlumnoUpdate) -> Alumno:
        """Actualizar datos personales del alumno."""
        alumno = self.obtener_por_id(db, alumno_id)
        if not alumno:
            raise ValueError("Alumno no encontrado")
        
        update_data = datos.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(alumno, field, value)
        
        db.commit()
        db.refresh(alumno)
        return alumno
    
    def eliminar(self, db: Session, alumno_id: int) -> bool:
        """Eliminar alumno permanentemente."""
        alumno = self.obtener_por_id(db, alumno_id)
        if not alumno:
            raise ValueError("Alumno no encontrado")
        
        db.delete(alumno)
        db.commit()
        return True
    
    def desactivar(self, db: Session, alumno_id: int) -> Alumno:
        """Desactivar alumno (soft delete)."""
        alumno = self.obtener_por_id(db, alumno_id)
        if not alumno:
            raise ValueError("Alumno no encontrado")
        
        alumno.activo = False
        db.commit()
        db.refresh(alumno)
        return alumno

    def actualizar_foto(self, db: Session, alumno_id: int, foto_data: bytes, mime_type: str) -> Alumno:
        """Guardar o reemplazar foto del alumno en la base de datos."""
        alumno = self.obtener_por_id(db, alumno_id)
        if not alumno:
            raise ValueError("Alumno no encontrado")

        alumno.foto_data = foto_data
        alumno.foto_mime_type = mime_type
        db.commit()
        db.refresh(alumno)
        return alumno

    def eliminar_foto(self, db: Session, alumno_id: int) -> Alumno:
        """Eliminar foto del alumno."""
        alumno = self.obtener_por_id(db, alumno_id)
        if not alumno:
            raise ValueError("Alumno no encontrado")

        alumno.foto_data = None
        alumno.foto_mime_type = None
        db.commit()
        db.refresh(alumno)
        return alumno

    def obtener_foto(self, db: Session, alumno_id: int) -> Tuple[Optional[bytes], Optional[str]]:
        """Obtener bytes y MIME de la foto del alumno."""
        alumno = self.obtener_por_id(db, alumno_id)
        if not alumno:
            raise ValueError("Alumno no encontrado")
        return alumno.foto_data, alumno.foto_mime_type


# Instancia global del servicio
alumno_service = AlumnoService()
