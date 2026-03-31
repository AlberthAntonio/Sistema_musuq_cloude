"""add alumno photo binary columns

Revision ID: c7d9e1f2a3b4
Revises: a1b2c3d4e5f6
Create Date: 2026-03-29 12:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c7d9e1f2a3b4"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("alumnos", sa.Column("foto_data", sa.LargeBinary(), nullable=True))
    op.add_column("alumnos", sa.Column("foto_mime_type", sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column("alumnos", "foto_mime_type")
    op.drop_column("alumnos", "foto_data")
