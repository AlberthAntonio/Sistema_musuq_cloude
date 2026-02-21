from sqlalchemy import Column, Integer, String, Date, Float
from sqlalchemy.orm import relationship
from app.database import Base

class Alumno(Base):
    __tablename__ = "alumnos"

    # ID interno de base de datos
    id = Column(Integer, primary_key=True, index=True)
    
    # --- Datos Académicos (Tu Código Generado) ---
    codigo_matricula = Column(String, unique=True, nullable=False) # Ej: POA250001
    
    # --- Datos del Alumno ---
    dni = Column(String, unique=True, nullable=False)
    nombres = Column(String, nullable=False)
    apell_paterno = Column(String, nullable=False)
    apell_materno = Column(String, nullable=False)
    fecha_nacimiento = Column(Date, nullable=True)
    
    grupo = Column(String, nullable=True)       # A, B, C, D
    carrera = Column(String, nullable=True)     # Medicina, Ing...
    modalidad = Column(String, nullable=True)   # Ordinario, Primera Opción...
    horario = Column(String, nullable=True)     # MATUTINO, VESPERTINO, DOBLE HORARIO
    
    # ⭐ FUTURO: Para modalidad COLEGIO
    grado = Column(String, nullable=True)  # 1ro, 2do, 3ro, 4to, 5to (para COLEGIO)

    # --- Datos de Padres/Apoderados ---
    nombre_padre_completo = Column(String, nullable=True) # Guardaremos Nombres + Apellidos
    celular_padre_1 = Column(String, nullable=True)
    celular_padre_2 = Column(String, nullable=True)
    descripcion = Column(String, nullable=True)

    # --- Datos Económicos (Pagos) ---
    costo_matricula = Column(Float, default=0.0)

    # Relación inversa: Un alumno tiene MUCHOS pagos
    pagos = relationship("Pago", back_populates="alumno", cascade="all, delete-orphan")

    # --- TIENES QUE AGREGAR ESTO ---
    # Relación con notas: Un alumno tiene MUCHAS notas
    notas = relationship("Nota", back_populates="alumno", cascade="all, delete-orphan")

    def __repr__(self):
        return f"{self.codigo_matricula} - {self.apell_paterno} {self.apell_materno}"