from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Creamos la base de datos en la carpeta raíz del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "asistencia.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Configuración del motor de base de datos
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """Crea las tablas en la base de datos si no existen."""
    from app.models.usuario_model import Usuario  # Importación local para evitar ciclos
    from app.models.alumno_model import Alumno
    from app.models.pago_model import Pago  # Importación local para evitar ciclos
    from app.models.asistencia_model import Asistencia
    from app.models.lista_model import ListaGuardada
    from app.models.nota_model import Nota  
    from app.models.sesion_model import SesionExamen
    from app.models.curso_model import Curso, MallaCurricular
    from app.models.docente_model import Docente
    from app.models.horario_model import Horario
    from app.models.evento_model import EventoCalendario

    Base.metadata.create_all(bind=engine)

def get_session():
    """
    Retorna una nueva sesión de SQLAlchemy
    Uso: 
        session = get_session()
        # ... hacer consultas ...
        session.close()
    """
    return SessionLocal()