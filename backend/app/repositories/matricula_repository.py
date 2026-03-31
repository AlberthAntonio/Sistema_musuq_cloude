from typing import List, Optional
from sqlalchemy.orm import Session, Query

from app.models.matricula import Matricula
from app.repositories.base import BaseRepository, QuerySpec
from app.schemas.matricula import MatriculaCreate, MatriculaUpdate


class MatriculaQuerySpec(QuerySpec):
    """Filtros de búsqueda para matrículas."""
    periodo_id: Optional[int] = None
    alumno_id: Optional[int] = None
    grupo: Optional[str] = None
    estado: Optional[str] = "activo"


class MatriculaRepository(BaseRepository[Matricula, MatriculaCreate, MatriculaUpdate]):
    def __init__(self):
        super().__init__(Matricula)

    def build_query(self, db: Session, spec: MatriculaQuerySpec, for_count: bool = False) -> Query:
        query = db.query(self.model)

        if spec.periodo_id is not None:
            query = query.filter(self.model.periodo_id == spec.periodo_id)
        if spec.alumno_id is not None:
            query = query.filter(self.model.alumno_id == spec.alumno_id)
        if spec.grupo is not None:
            query = query.filter(self.model.grupo == spec.grupo)
        if spec.estado is not None:
            query = query.filter(self.model.estado == spec.estado)

        if not for_count:
            if spec.order_by:
                col = getattr(self.model, spec.order_by) if hasattr(self.model, spec.order_by) else self.model.fecha_registro
                query = query.order_by(col.desc() if spec.descending else col)
            else:
                query = query.order_by(self.model.fecha_registro.desc())
                
        return query

    def find_all(self, db: Session, spec: MatriculaQuerySpec) -> List[Matricula]:
        return self.build_query(db, spec, for_count=False).offset(spec.skip).limit(spec.limit).all()

    def count_all(self, db: Session, spec: MatriculaQuerySpec) -> int:
        return self.build_query(db, spec, for_count=True).order_by(None).count()

    def get_by_codigo(self, db: Session, codigo: str) -> Optional[Matricula]:
        """Obtener matrícula por código de matrícula exácto."""
        return db.query(self.model).filter(self.model.codigo_matricula == codigo).first()


# Instancia Singleton Global
matricula_repo = MatriculaRepository()
