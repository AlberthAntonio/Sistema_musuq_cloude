from typing import List, Optional
from sqlalchemy.orm import Session, joinedload, Query
from sqlalchemy import or_

from app.models.alumno import Alumno
from app.models.matricula import Matricula
from app.repositories.base import BaseRepository, QuerySpec
from app.schemas.alumno import AlumnoCreate, AlumnoUpdate


class AlumnoQuerySpec(QuerySpec):
    """
    Extiende QuerySpec para incluir filtros específicos de dominio (multi-tenant, activos y grupos).
    """
    periodo_id: Optional[int] = None
    grupo: Optional[str] = None
    modalidad: Optional[str] = None
    activo: Optional[bool] = True
    buscar: Optional[str] = None


class AlumnoRepository(BaseRepository[Alumno, AlumnoCreate, AlumnoUpdate]):
    def __init__(self):
        super().__init__(Alumno)

    def get_by_dni(self, db: Session, dni: str) -> Optional[Alumno]:
        return db.query(self.model).filter(self.model.dni == dni).first()

    def build_query(self, db: Session, spec: AlumnoQuerySpec, for_count: bool = False) -> Query:
        """
        Sobrescribe build_query para aplicar reglas de negocio complejas como JOINs
        dependientes del periodo o búsuqedas textuales.
        """
        necesita_join = bool(spec.periodo_id or spec.grupo or spec.modalidad or spec.buscar)

        query = db.query(self.model)

        if necesita_join:
            if not for_count:
                query = query.options(joinedload(self.model.matriculas))
            # Usar outerjoin si es búsqueda de texto libre para incluir alumnos no matriculados
            # De lo contrario usar join estricto
            if spec.buscar and not spec.periodo_id:
                query = query.outerjoin(Matricula, Matricula.alumno_id == self.model.id)
            else:
                query = query.join(Matricula, Matricula.alumno_id == self.model.id)

            if spec.periodo_id:
                query = query.filter(
                    Matricula.periodo_id == spec.periodo_id,
                    Matricula.estado == "activo",
                )
            if spec.grupo:
                query = query.filter(Matricula.grupo == spec.grupo)
            if spec.modalidad:
                query = query.filter(Matricula.modalidad == spec.modalidad)

        else:
            if not for_count:
                query = query.options(joinedload(self.model.matriculas))

        if spec.activo is not None:
            query = query.filter(self.model.activo == spec.activo)

        # Filtro textual (DNI, nombres, apellidos o código matrícula)
        if spec.buscar:
            query = query.filter(
                or_(
                    self.model.nombres.ilike(f"%{spec.buscar}%"),
                    self.model.apell_paterno.ilike(f"%{spec.buscar}%"),
                    self.model.apell_materno.ilike(f"%{spec.buscar}%"),
                    self.model.dni.ilike(f"%{spec.buscar}%"),
                    Matricula.codigo_matricula.ilike(f"%{spec.buscar}%") if necesita_join else False
                )
            )

        if not for_count:
            if spec.order_by == "nombre_completo" or not spec.order_by:
                query = query.order_by(self.model.apell_paterno, self.model.apell_materno)
            else:
                # Usa order_by base heredado
                col = getattr(self.model, spec.order_by) if hasattr(self.model, spec.order_by) else self.model.id
                if spec.descending:
                    col = col.desc()
                query = query.order_by(col)

        return query.distinct()

    def find_all(self, db: Session, spec: AlumnoQuerySpec) -> List[Alumno]:
        return self.build_query(db, spec, for_count=False).offset(spec.skip).limit(spec.limit).all()

    def count_all(self, db: Session, spec: AlumnoQuerySpec) -> int:
        return self.build_query(db, spec, for_count=True).order_by(None).count()


# Instancia singleton para uso en Depends o inyección directa.
alumno_repo = AlumnoRepository()
