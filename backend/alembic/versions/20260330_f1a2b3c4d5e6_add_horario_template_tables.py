"""add horario template tables and fk

Revision ID: f1a2b3c4d5e6
Revises: c7d9e1f2a3b4
Create Date: 2026-03-30 08:45:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f1a2b3c4d5e6"
down_revision = "c7d9e1f2a3b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "plantillas_horario",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("aula_id", sa.Integer(), nullable=False),
        sa.Column("grupo", sa.String(length=10), nullable=False),
        sa.Column("periodo", sa.String(length=20), nullable=False),
        sa.Column("turno", sa.String(length=20), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["aula_id"], ["aulas.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_plantillas_horario_aula_grupo_periodo_turno_activo",
        "plantillas_horario",
        ["aula_id", "grupo", "periodo", "turno", "activo"],
        unique=False,
    )

    op.create_table(
        "plantilla_bloques",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plantilla_id", sa.Integer(), nullable=False),
        sa.Column("dia_semana", sa.Integer(), nullable=False),
        sa.Column("hora_inicio", sa.String(length=5), nullable=False),
        sa.Column("hora_fin", sa.String(length=5), nullable=False),
        sa.Column("tipo_bloque", sa.String(length=20), nullable=False),
        sa.Column("etiqueta", sa.String(length=100), nullable=True),
        sa.Column("orden_visual", sa.Integer(), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("dia_semana >= 1 AND dia_semana <= 6", name="ck_plantilla_bloques_dia_semana"),
        sa.CheckConstraint("hora_inicio < hora_fin", name="ck_plantilla_bloques_horas"),
        sa.CheckConstraint(
            "tipo_bloque IN ('CLASE', 'RECREO', 'LIBRE')",
            name="ck_plantilla_bloques_tipo",
        ),
        sa.ForeignKeyConstraint(["plantilla_id"], ["plantillas_horario.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_plantilla_bloques_plantilla_id", "plantilla_bloques", ["plantilla_id"], unique=False)
    op.create_index(
        "ix_plantilla_bloques_plantilla_dia_inicio",
        "plantilla_bloques",
        ["plantilla_id", "dia_semana", "hora_inicio"],
        unique=False,
    )

    with op.batch_alter_table("horarios") as batch_op:
        batch_op.add_column(sa.Column("plantilla_bloque_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_horarios_plantilla_bloque_id", ["plantilla_bloque_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_horarios_plantilla_bloque_id",
            "plantilla_bloques",
            ["plantilla_bloque_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("horarios") as batch_op:
        batch_op.drop_constraint("fk_horarios_plantilla_bloque_id", type_="foreignkey")
        batch_op.drop_index("ix_horarios_plantilla_bloque_id")
        batch_op.drop_column("plantilla_bloque_id")

    op.drop_index("ix_plantilla_bloques_plantilla_dia_inicio", table_name="plantilla_bloques")
    op.drop_index("ix_plantilla_bloques_plantilla_id", table_name="plantilla_bloques")
    op.drop_table("plantilla_bloques")

    op.drop_index(
        "ix_plantillas_horario_aula_grupo_periodo_turno_activo",
        table_name="plantillas_horario",
    )
    op.drop_table("plantillas_horario")
