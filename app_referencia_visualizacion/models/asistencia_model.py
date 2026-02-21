from sqlalchemy import Column, Integer, String, Date, Time, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class Asistencia(Base):
    __tablename__ = "asistencias"

    id = Column(Integer, primary_key=True, index=True)
    alumno_id = Column(Integer, ForeignKey("alumnos.id"), nullable=False)
    fecha = Column(Date, default=datetime.now().date)
    hora = Column(Time, default=datetime.now().time)
    estado = Column(String, nullable=False)  # "Puntual", "Tarde", "Falta"
    turno = Column(String, nullable=False)   # "Mañana", "Tarde"
    observacion = Column(String, nullable=True)

    alerta_turno = Column(Boolean, default=False)

    # Relación para acceder a los datos del alumno desde la asistencia
    alumno = relationship("Alumno", backref="asistencias")

    def __repr__(self):
        return f"<Asistencia {self.alumno.nombres} - {self.fecha} - {self.estado}>"