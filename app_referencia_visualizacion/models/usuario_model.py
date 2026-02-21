from sqlalchemy import Column, Integer, String
from app.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    nombre_completo = Column(String, nullable=True)
    rol = Column(String, default="docente")  # Ejemplo: 'admin', 'docente'

    def __repr__(self):
        return f"<Usuario(username='{self.username}', rol='{self.rol}')>"