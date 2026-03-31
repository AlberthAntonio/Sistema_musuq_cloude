"""add composite indexes for performance

Revision ID: a1b2c3d4e5f6
Revises: eb99892215b1
Create Date: 2026-03-28 08:35:00.000000

Índices compuestos para mejorar rendimiento en consultas críticas.
Plan Maestro §7.3 - Índices compuestos sugeridos.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'eb99892215b1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Crear índices compuestos priorizados.
    Usa SQL directo para compatibilidad con SQLite.
    """
    conn = op.get_bind()

    # ---- Limpiar duplicados en asistencias antes de crear UNIQUE ----
    conn.execute(text("""
        DELETE FROM asistencias
        WHERE id NOT IN (
            SELECT MAX(id)
            FROM asistencias
            GROUP BY alumno_id, fecha, turno
        )
    """))

    # ---- Índices de asistencias ----
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_asist_periodo_fecha_estado "
        "ON asistencias (periodo_id, fecha, estado)"
    ))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_asist_alumno_fecha "
        "ON asistencias (alumno_id, fecha)"
    ))
    conn.execute(text(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_asist_alumno_fecha_turno "
        "ON asistencias (alumno_id, fecha, turno)"
    ))

    # ---- Índices de matrículas ----
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_mat_periodo_estado_grupo "
        "ON matriculas (periodo_id, estado, grupo)"
    ))

    # ---- Índices de obligaciones de pago ----
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_oblig_matricula_estado_venc "
        "ON obligaciones_pago (matricula_id, estado, fecha_vencimiento)"
    ))

    # ---- Índices de pagos ----
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_pago_obligacion_fecha "
        "ON pagos (obligacion_id, fecha)"
    ))

    # ---- Índice de alumnos ----
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_alum_activo_apellidos "
        "ON alumnos (activo, apell_paterno, apell_materno)"
    ))


def downgrade() -> None:
    """Eliminar todos los índices agregados."""
    conn = op.get_bind()
    conn.execute(text("DROP INDEX IF EXISTS ix_alum_activo_apellidos"))
    conn.execute(text("DROP INDEX IF EXISTS ix_pago_obligacion_fecha"))
    conn.execute(text("DROP INDEX IF EXISTS ix_oblig_matricula_estado_venc"))
    conn.execute(text("DROP INDEX IF EXISTS ix_mat_periodo_estado_grupo"))
    conn.execute(text("DROP INDEX IF EXISTS uq_asist_alumno_fecha_turno"))
    conn.execute(text("DROP INDEX IF EXISTS ix_asist_alumno_fecha"))
    conn.execute(text("DROP INDEX IF EXISTS ix_asist_periodo_fecha_estado"))
