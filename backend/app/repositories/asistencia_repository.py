from typing import List, Optional, Any
from datetime import date
from sqlalchemy.orm import Session, Query

from app.models.asistencia import Asistencia
from app.models.alumno import Alumno
from app.models.matricula import Matricula
from app.repositories.base import BaseRepository, QuerySpec
from app.schemas.asistencia import AsistenciaCreate, AsistenciaUpdate

class AsistenciaQuerySpec(QuerySpec):
    """
    Especificación de dominio para consultas granulares de asistencias.
    """
    fecha: Optional[date] = None
    alumno_id: Optional[int] = None
    grupo: Optional[str] = None
    turno: Optional[str] = None
    estado: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    periodo_id: Optional[int] = None


class AsistenciaRepository(BaseRepository[Asistencia, AsistenciaCreate, AsistenciaUpdate]):
    def __init__(self):
        super().__init__(Asistencia)

    def existe_registro(self, db: Session, alumno_id: int, fecha: date, turno: str) -> bool:
        """Verifica si existe el registro para evitar duplicados diarios en el mismo turno."""
        return db.query(self.model.id).filter(
            self.model.alumno_id == alumno_id,
            self.model.fecha == fecha,
            self.model.turno == turno
        ).first() is not None

    def build_query(self, db: Session, spec: AsistenciaQuerySpec, for_count: bool = False) -> Query:
        """Construye query de asistencias optimizada evitando cargas anidadas costosas e integrando N+1 dicts."""
        if for_count:
            query = db.query(self.model.id).join(Alumno, self.model.alumno_id == Alumno.id)
        else:
            # Seleccionamos campos exactos para el flat mapping sin overhead de ORM en obj completos.
            query = db.query(
                self.model.id,
                self.model.alumno_id,
                self.model.fecha,
                self.model.turno,
                self.model.estado,
                self.model.hora,
                self.model.alerta_turno,
                self.model.periodo_id,
                self.model.observacion,
                self.model.registrado_por,
                self.model.fecha_registro,
                Alumno.nombres.label("alumno_nombres"),
                Alumno.apell_paterno.label("alumno_apell_paterno"),
                Alumno.apell_materno.label("alumno_apell_materno"),
                Alumno.dni.label("alumno_dni"),
            ).join(Alumno, self.model.alumno_id == Alumno.id)

        if spec.fecha:
            query = query.filter(self.model.fecha == spec.fecha)
        elif spec.fecha_inicio or spec.fecha_fin:
            if spec.fecha_inicio:
                query = query.filter(self.model.fecha >= spec.fecha_inicio)
            if spec.fecha_fin:
                query = query.filter(self.model.fecha <= spec.fecha_fin)
                
        if spec.alumno_id:
            query = query.filter(self.model.alumno_id == spec.alumno_id)
        if spec.periodo_id:
            query = query.filter(self.model.periodo_id == spec.periodo_id)
            
        if spec.grupo:
            alumno_ids_subq = db.query(Matricula.alumno_id).filter(
                Matricula.grupo == spec.grupo,
                Matricula.estado == "activo"
            ).scalar_subquery()
            query = query.filter(self.model.alumno_id.in_(alumno_ids_subq))
            
        if spec.turno:
            query = query.filter(self.model.turno == spec.turno)
        if spec.estado:
            query = query.filter(self.model.estado == spec.estado)

        if not for_count:
            if spec.order_by:
                col = getattr(self.model, spec.order_by) if hasattr(self.model, spec.order_by) else self.model.fecha
                query = query.order_by(col.desc() if spec.descending else col)
            else:
                query = query.order_by(self.model.fecha.desc())
                
        return query

    def find_all(self, db: Session, spec: AsistenciaQuerySpec) -> List[Any]:
        """Ejecuta consulta armada. Retorna filas proxy nombradas."""
        return self.build_query(db, spec, for_count=False).offset(spec.skip).limit(spec.limit).all()

    def count_all(self, db: Session, spec: AsistenciaQuerySpec) -> int:
        return self.build_query(db, spec, for_count=True).order_by(None).count()


# Instancia Singleton Global
asistencia_repo = AsistenciaRepository()
