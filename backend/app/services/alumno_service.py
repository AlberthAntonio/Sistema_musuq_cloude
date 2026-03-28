"""
Servicio de Alumnos - Lógica de negocio con filtro por periodo.
"""
from typing import List, Optional
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
    
    def listar(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        activo: Optional[bool] = True,
        periodo_id: Optional[int] = None,
        grupo: Optional[str] = None,
        modalidad: Optional[str] = None,
    ) -> List[Alumno]:
        """
        Listar alumnos con filtros opcionales.
        Si se provee periodo_id, retorna SOLO los alumnos matriculados en ese periodo.
        Los filtros grupo/modalidad requieren join con Matricula.
        """
        query = db.query(Alumno).options(joinedload(Alumno.matriculas))

        # Determinar si necesitamos join con Matricula
        necesita_join = bool(periodo_id or grupo or modalidad)
        if necesita_join:
            query = query.join(Matricula, Matricula.alumno_id == Alumno.id)
            if periodo_id:
                query = query.filter(
                    Matricula.periodo_id == periodo_id,
                    Matricula.estado == "activo",
                )
            if grupo:
                query = query.filter(Matricula.grupo == grupo)
            if modalidad:
                query = query.filter(Matricula.modalidad == modalidad)

        if activo is not None:
            query = query.filter(Alumno.activo == activo)

        return query.distinct().order_by(
            Alumno.apell_paterno, Alumno.apell_materno
        ).offset(skip).limit(limit).all()
    
    def crear(self, db: Session, datos: AlumnoCreate, usuario_actual_id: Optional[int] = None) -> Alumno:
        """Crear nuevo alumno (solo datos personales)."""
        # Validar DNI único
        if not self.validar_dni_unico(db, datos.dni):
            raise ValueError("El DNI ya está registrado")
        
        alumno = Alumno(**datos.model_dump())
        if usuario_actual_id:
            alumno.creado_por = usuario_actual_id
        db.add(alumno)
        db.commit()
        db.refresh(alumno)
        return alumno
    
    def obtener_por_id(self, db: Session, alumno_id: int) -> Optional[Alumno]:
        """Obtener alumno por ID."""
        return db.query(Alumno).filter(Alumno.id == alumno_id).first()
    
    def obtener_por_dni(self, db: Session, dni: str) -> Optional[Alumno]:
        """Obtener alumno por DNI."""
        return db.query(Alumno).filter(Alumno.dni == dni).first()
    
    def buscar(
        self, 
        db: Session, 
        termino: str, 
        limite: int = 20,
        periodo_id: Optional[int] = None
    ) -> List[Alumno]:
        """
        Buscar alumnos por nombre, apellido o DNI.
        Si se provee periodo_id, busca solo entre alumnos del periodo.
        """
        query = db.query(Alumno).options(joinedload(Alumno.matriculas))

        # Si busca por código de matrícula exacto o parcial, incluir JOIN
        # Siempre hacemos outerjoin para poder filtrar también por codigo_matricula
        query = query.outerjoin(Matricula, Matricula.alumno_id == Alumno.id)

        # Filtro multi-tenant
        if periodo_id:
            query = query.filter(
                Matricula.periodo_id == periodo_id,
                Matricula.estado == "activo"
            )

        query = query.filter(
            or_(
                Alumno.nombres.ilike(f"%{termino}%"),
                Alumno.apell_paterno.ilike(f"%{termino}%"),
                Alumno.apell_materno.ilike(f"%{termino}%"),
                Alumno.dni.ilike(f"%{termino}%"),
                Matricula.codigo_matricula.ilike(f"%{termino}%"),
            ),
            Alumno.activo == True
        )

        return query.distinct().limit(limite).all()
    
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


# Instancia global del servicio
alumno_service = AlumnoService()
