import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# ---------------------------------------------------------------------------
# Asegurar que el directorio backend esté en el path
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar settings para obtener la URL de BD dinámicamente
from app.core.config import settings  # noqa: E402

# Importar Base y TODOS los modelos para que autogenerate los detecte
from app.db.database import Base  # noqa: E402
from app.models import (  # noqa: E402, F401
    Usuario, Alumno, Asistencia, Curso, MallaCurricular,
    Aula, AulaGrupo, AulaCurso,
    Docente, DocenteCurso, Horario, EventoCalendario, ListaGuardada,
    SesionExamen, Nota,
    PeriodoAcademico, Matricula, ObligacionPago, Pago
)

# ---------------------------------------------------------------------------
# Configuración de Alembic
# ---------------------------------------------------------------------------
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata de todos los modelos para autogeneración
target_metadata = Base.metadata

# Inyectar la URL de BD desde nuestros settings (sobreescribe alembic.ini)
config.set_main_option("sqlalchemy.url", settings.db_url)


def run_migrations_offline() -> None:
    """Ejecutar migraciones en modo 'offline' (sin conexión activa)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        render_as_batch=url.startswith("sqlite"),  # Batch mode para SQLite
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Ejecutar migraciones en modo 'online' (con conexión activa)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        is_sqlite = str(connection.engine.url).startswith("sqlite")
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=is_sqlite,  # Batch mode para SQLite
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
