"""
Modelo de Lista Guardada (grupos de alumnos).
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


# Tabla intermedia para relación muchos-a-muchos entre Lista y Alumno
lista_items = Table(
    'lista_items', 
    Base.metadata,
    Column('lista_id', Integer, ForeignKey('listas_guardadas.id'), primary_key=True),
    Column('alumno_id', Integer, ForeignKey('alumnos.id'), primary_key=True)
)


class ListaGuardada(Base):
    """Modelo de lista guardada de alumnos."""
    
    __tablename__ = "listas_guardadas"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, nullable=False)  # Ej: "Grupo Danza"
    descripcion = Column(String(255), nullable=True)
    
    # Timestamps
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relación muchos-a-muchos con alumnos
    alumnos = relationship("Alumno", secondary=lista_items, backref="listas")
    
    def __repr__(self):
        return self.nombre
