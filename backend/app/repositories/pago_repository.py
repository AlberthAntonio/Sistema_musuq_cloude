from typing import List, Optional, Any
from datetime import date
from sqlalchemy.orm import Session, Query, joinedload

from app.models.pago import Pago
from app.models.obligacion import ObligacionPago
from app.models.matricula import Matricula
from app.repositories.base import BaseRepository, QuerySpec
from app.schemas.pago import PagoCreate, PagoUpdate


class PagoQuerySpec(QuerySpec):
    """Filtros para listar/contar pagos."""
    obligacion_id: Optional[int] = None
    periodo_id: Optional[int] = None
    alumno_id: Optional[int] = None
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None
    with_eager: bool = True


class PagoRepository(BaseRepository[Pago, PagoCreate, PagoUpdate]):
    def __init__(self):
        super().__init__(Pago)

    def build_query(self, db: Session, spec: PagoQuerySpec, for_count: bool = False) -> Query:
        query = db.query(self.model)

        # Si no contamos y piden eager, cargamos full graph.
        if not for_count and spec.with_eager:
            query = query.options(
                joinedload(self.model.obligacion).joinedload(ObligacionPago.matricula).joinedload(Matricula.alumno)
            )

        if spec.obligacion_id:
            query = query.filter(self.model.obligacion_id == spec.obligacion_id)

        # Joins requeridos si filtramos por alumno o periodo
        if spec.alumno_id or spec.periodo_id:
            query = query \
                .join(ObligacionPago, self.model.obligacion_id == ObligacionPago.id) \
                .join(Matricula, ObligacionPago.matricula_id == Matricula.id)
            if spec.periodo_id:
                query = query.filter(Matricula.periodo_id == spec.periodo_id)
            if spec.alumno_id:
                query = query.filter(Matricula.alumno_id == spec.alumno_id)

        if spec.fecha_desde:
            query = query.filter(self.model.fecha >= spec.fecha_desde)
        if spec.fecha_hasta:
            query = query.filter(self.model.fecha <= spec.fecha_hasta)

        if not for_count:
            if spec.order_by:
                col = getattr(self.model, spec.order_by) if hasattr(self.model, spec.order_by) else self.model.fecha
                query = query.order_by(col.desc() if spec.descending else col)
            else:
                query = query.order_by(self.model.fecha.desc())
                
        return query

    def find_all(self, db: Session, spec: PagoQuerySpec) -> List[Any]:
        return self.build_query(db, spec, for_count=False).offset(spec.skip).limit(spec.limit).all()

    def count_all(self, db: Session, spec: PagoQuerySpec) -> int:
        return self.build_query(db, spec, for_count=True).order_by(None).count()


# Instancia Singleton Global
pago_repo = PagoRepository()
