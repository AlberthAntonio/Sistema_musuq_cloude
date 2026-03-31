"""
Configuración de base de datos con SQLAlchemy.
Pool de conexiones optimizado según entorno.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

# Crear engine según configuración
# SQLite: config simple (no soporta pool real)
# PostgreSQL: pool completo con pre_ping, overflow, timeouts
if settings.USE_SQLITE:
    engine = create_engine(
        settings.db_url,
        echo=False,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(
        settings.db_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
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
        Aula, AulaGrupo, AulaCurso,
        Docente, DocenteCurso, Horario, PlantillaHorario, PlantillaBloque,
        EventoCalendario, ListaGuardada,
        SesionExamen, Nota,
        PeriodoAcademico, Matricula, ObligacionPago, Pago
    )
    Base.metadata.create_all(bind=engine)
