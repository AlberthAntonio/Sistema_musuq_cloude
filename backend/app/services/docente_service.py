"""Servicio de Docentes - Lógica de negocio y validaciones."""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.docente import Docente
from app.models.docente_curso import DocenteCurso
from app.models.curso import Curso
from app.schemas.docente import DocenteCreate, DocenteUpdate


class DocenteService:
    """Servicio para operaciones de docentes."""
    
    # ==================== VALIDACIONES ====================
    
    def validar_dni_unico(self, db: Session, dni: str, docente_id: Optional[int] = None) -> bool:
        """Verifica si el DNI ya existe."""
        if not dni:
            return True  # DNI es opcional
        query = db.query(Docente).filter(Docente.dni == dni)
        if docente_id:
            query = query.filter(Docente.id != docente_id)
        return query.first() is None
    
    # ==================== OPERACIONES CRUD ====================
    
    def listar(self, db: Session, activo: Optional[bool] = True) -> List[Docente]:
        """Listar docentes."""
        query = db.query(Docente)
        if activo is not None:
            query = query.filter(Docente.activo == activo)
        return query.order_by(Docente.apellidos, Docente.nombres).all()
    
    def crear(self, db: Session, datos: DocenteCreate) -> Docente:
        """Crear nuevo docente."""
        if datos.dni and not self.validar_dni_unico(db, datos.dni):
            raise ValueError("El DNI ya está registrado")
        
        docente = Docente(**datos.model_dump())
        db.add(docente)
        db.commit()
        db.refresh(docente)
        return docente
    
    def obtener_por_id(self, db: Session, docente_id: int) -> Optional[Docente]:
        """Obtener docente por ID."""
        return db.query(Docente).filter(Docente.id == docente_id).first()
    
    def buscar(self, db: Session, termino: str, limite: int = 20) -> List[Docente]:
        """Buscar docentes por nombre, apellido o DNI."""
        return db.query(Docente).filter(
            or_(
                Docente.nombres.ilike(f"%{termino}%"),
                Docente.apellidos.ilike(f"%{termino}%"),
                Docente.dni.ilike(f"%{termino}%")
            ),
            Docente.activo == True
        ).limit(limite).all()
    
    def actualizar(self, db: Session, docente_id: int, datos: DocenteUpdate) -> Docente:
        """Actualizar docente."""
        docente = self.obtener_por_id(db, docente_id)
        if not docente:
            raise ValueError("Docente no encontrado")
        
        # Validar DNI único si se cambia
        if datos.dni and datos.dni != docente.dni:
            if not self.validar_dni_unico(db, datos.dni, docente_id):
                raise ValueError("El DNI ya está registrado")
        
        update_data = datos.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(docente, field, value)
        
        db.commit()
        db.refresh(docente)
        return docente
    
    def eliminar(self, db: Session, docente_id: int) -> bool:
        """Eliminar docente."""
        docente = self.obtener_por_id(db, docente_id)
        if not docente:
            raise ValueError("Docente no encontrado")
        
        db.delete(docente)
        db.commit()
        return True
    
    def desactivar(self, db: Session, docente_id: int) -> Docente:
        """Desactivar docente (soft delete)."""
        docente = self.obtener_por_id(db, docente_id)
        if not docente:
            raise ValueError("Docente no encontrado")
        
        docente.activo = False
        db.commit()
        db.refresh(docente)
        return docente

    # ==================== CURSOS ASIGNADOS ====================

    def obtener_cursos(self, db: Session, docente_id: int) -> List[Curso]:
        """Obtener cursos asignados a un docente."""
        docente = self.obtener_por_id(db, docente_id)
        if not docente:
            raise ValueError("Docente no encontrado")

        query = (
            db.query(Curso)
            .join(DocenteCurso, DocenteCurso.curso_id == Curso.id)
            .filter(DocenteCurso.docente_id == docente_id, DocenteCurso.activo == True)
        )
        return query.order_by(Curso.nombre).all()

    def actualizar_cursos(self, db: Session, docente_id: int, curso_ids: List[int]) -> Docente:
        """Reemplazar los cursos asignados a un docente por la lista dada."""
        docente = self.obtener_por_id(db, docente_id)
        if not docente:
            raise ValueError("Docente no encontrado")

        # Limpiar todas las asignaciones actuales
        db.query(DocenteCurso).filter(DocenteCurso.docente_id == docente_id).delete()

        # Insertar nuevas asignaciones (evitar duplicados)
        for curso_id in sorted(set(curso_ids or [])):
            assoc = DocenteCurso(docente_id=docente_id, curso_id=curso_id, activo=True)
            db.add(assoc)

        db.commit()
        db.refresh(docente)
        return docente

    def quitar_curso(self, db: Session, docente_id: int, curso_id: int) -> bool:
        """Quitar una asignación específica docente-curso."""
        docente = self.obtener_por_id(db, docente_id)
        if not docente:
            raise ValueError("Docente no encontrado")

        asignacion = db.query(DocenteCurso).filter(
            DocenteCurso.docente_id == docente_id,
            DocenteCurso.curso_id == curso_id,
        ).first()
        if not asignacion:
            raise ValueError("La asignación docente-curso no existe")

        db.delete(asignacion)
        db.commit()
        return True

    def listar_por_curso(self, db: Session, curso_id: int) -> List[Docente]:
        """Listar docentes que dictan un curso específico."""
        query = (
            db.query(Docente)
            .join(DocenteCurso, DocenteCurso.docente_id == Docente.id)
            .filter(
                DocenteCurso.curso_id == curso_id,
                DocenteCurso.activo == True,
                Docente.activo == True,
            )
            .order_by(Docente.apellidos, Docente.nombres)
        )
        return query.all()


# Instancia global del servicio
docente_service = DocenteService()
