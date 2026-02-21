from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.database import Base

# Tabla intermedia (La "unión" entre una Lista y un Alumno)
lista_items = Table('lista_items', Base.metadata,
    Column('lista_id', Integer, ForeignKey('listas_guardadas.id')),
    Column('alumno_id', Integer, ForeignKey('alumnos.id'))
)

class ListaGuardada(Base):
    __tablename__ = "listas_guardadas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False) # Ej: "Grupo Danza"
    
    # Relación: Una lista tiene muchos alumnos
    alumnos = relationship("Alumno", secondary=lista_items, backref="listas")

    def __repr__(self):
        return self.nombre