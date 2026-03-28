"""initial_schema

Revision ID: eb99892215b1
Revises: 
Create Date: 2026-02-23

Agrega columna periodo_id a asistencias (multi-tenant por periodo).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eb99892215b1'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.
    
    Usa batch_alter_table para compatibilidad con SQLite (modo batch).
    En PostgreSQL aplica directamente.
    """
    with op.batch_alter_table('asistencias') as batch_op:
        batch_op.add_column(
            sa.Column('periodo_id', sa.Integer(), nullable=True)
        )
        batch_op.create_index(
            'ix_asistencias_periodo_id', ['periodo_id'], unique=False
        )
        batch_op.create_foreign_key(
            'fk_asistencias_periodo_id',
            'periodos_academicos', ['periodo_id'], ['id']
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('asistencias') as batch_op:
        batch_op.drop_constraint('fk_asistencias_periodo_id', type_='foreignkey')
        batch_op.drop_index('ix_asistencias_periodo_id')
        batch_op.drop_column('periodo_id')
