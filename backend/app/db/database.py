"""
Configuración de base de datos con SQLAlchemy.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

# Crear engine según configuración
engine = create_engine(
    settings.db_url,
    echo=settings.DEBUG,
    # Para SQLite necesitamos check_same_thread=False
    connect_args={"check_same_thread": False} if settings.USE_SQLITE else {}
)

# Sesión de base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()


def get_db():
    """
    Dependency para obtener sesión de BD.
    Uso en FastAPI:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Crea todas las tablas en la base de datos."""
    # Importar todos los modelos para que SQLAlchemy los registre
    from app.models import (
        Usuario, Alumno, Asistencia, Curso, MallaCurricular,
        Docente, Horario, EventoCalendario, ListaGuardada,
        SesionExamen, Nota, Pago
    )
    Base.metadata.create_all(bind=engine)
