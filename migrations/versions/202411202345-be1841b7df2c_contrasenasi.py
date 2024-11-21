"""contrasenasi

Revision ID: be1841b7df2c
Revises: b92ea55992f5
Create Date: 2024-11-20 23:45:24.155320

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "be1841b7df2c"
down_revision = "b92ea55992f5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Eliminar 'password_history' si existe
    conn = op.get_bind()
    result = conn.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name='accounts_users' AND column_name='password_history';"
    )
    if result.fetchone():
        op.drop_column("accounts_users", "password_history")


def downgrade() -> None:
    # Revertir eliminaciones
    op.add_column(
        "accounts_users",
        sa.Column(
            "password_history",
            postgresql.JSON(astext_type=sa.Text()),
            autoincrement=False,
            nullable=True,
        ),
    )