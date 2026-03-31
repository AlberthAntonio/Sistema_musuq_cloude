"""
Patrón Repositorio Base.
Estandariza operaciones de lectura/escritura y el transporte de atributos de búsqueda (QuerySpec).
"""
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from sqlalchemy.orm import Session, Query, joinedload

from app.db.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class QuerySpec(BaseModel):
    """
    Especificación de consulta unificada.
    Transporta los filtros, paginación y proyecciones desde la UI hacia la DB de forma limpia.
    """
    # Filtros exactos o custom gestionados por cada repositorio.
    filters: Dict[str, Any] = {}
    
    # Lista de relaciones de SQLAlchemy a invocar (e.g. joinedload('matriculas'))
    # en formato plano para que el repositorio resuelva el eager loading.
    include_relations: List[str] = []
    
    # Campo para aplicar 'Order_By'
    order_by: Optional[str] = None
    descending: bool = True
    
    # Paginación
    skip: int = 0
    limit: int = 100


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Clase abstracta de repositorio con operaciones genéricas C-R-U-D.
    Inyecta `self.db` (Session) en el momento de instanciarse si se usa Dependency Injection,
    o se pasa `db` en los métodos. Para máxima escalabilidad en FastAPI usaremos Inyección en el ciclo de vida.
    """
    
    def __init__(self, model: Type[ModelType]):
        """
        Inicializa repositorio.
        :param model: The SQLAlchemy model class.
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """Busca un registro por su clave primaria."""
        return db.query(self.model).filter(self.model.id == id).first()

    def create(self, db: Session, *, obj_in: CreateSchemaType, creado_por: Optional[int] = None) -> ModelType:
        """Crea un registro insertando los valores del schema de entrada."""
        obj_in_data = obj_in.model_dump()
        db_obj = self.model(**obj_in_data)
        
        # Opcional si la entidad soporta auditoria básica
        if creado_por and hasattr(db_obj, "creado_por"):
            db_obj.creado_por = creado_por
            
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Actualiza un registro con nuevos datos preservando campos estáticos o inmutables."""
        obj_data = db_obj.__dict__
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
            
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
                
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> ModelType:
        """Elimina un registro de la base de datos (Hard Delete)."""
        obj = db.query(self.model).get(id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    def build_query(self, db: Session, spec: QuerySpec) -> Query:
        """
        Punto de extensión para repositorios hijos. 
        Por defecto, este método sólo aplica parámetros genéricos.
        """
        q = db.query(self.model)
        
        # Filtros genéricos que coincidan con la tabla
        for key, value in spec.filters.items():
            if hasattr(self.model, key) and value is not None:
                q = q.filter(getattr(self.model, key) == value)
                
        # Eager Load relations
        for rel in spec.include_relations:
            if hasattr(self.model, rel):
                q = q.options(joinedload(getattr(self.model, rel)))
                
        # Sorting Genérico
        if spec.order_by and hasattr(self.model, spec.order_by):
            col = getattr(self.model, spec.order_by)
            if spec.descending:
                col = col.desc()
            q = q.order_by(col)
            
        return q

    def find_all(self, db: Session, spec: QuerySpec) -> List[ModelType]:
        """Retorna lista usando filtro padronizado."""
        return self.build_query(db, spec).offset(spec.skip).limit(spec.limit).all()

    def count_all(self, db: Session, spec: Optional[QuerySpec] = None) -> int:
        """Retorna el contador en base a los metadatos de búsqueda especificados."""
        if not spec:
            return db.query(self.model).count()
        return self.build_query(db, spec).order_by(None).count()
