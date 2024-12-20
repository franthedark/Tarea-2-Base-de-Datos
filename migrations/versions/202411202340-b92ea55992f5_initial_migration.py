"""Initial migration

Revision ID: b92ea55992f5
Revises: 
Create Date: 2024-11-20 23:40:59.662917

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b92ea55992f5'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('accounts_users', sa.Column(
    'previous_passwords', 
    postgresql.ARRAY(sa.String()), 
    nullable=False, 
    server_default='{}'  # Valor por defecto: un array vacío
))

    op.add_column('accounts_users', sa.Column('last_login', sa.DateTime(), nullable=True))
    op.drop_column('accounts_users', 'password_history')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('accounts_users', sa.Column('password_history', postgresql.ARRAY(sa.VARCHAR()), autoincrement=False, nullable=True))
    op.drop_column('accounts_users', 'last_login')
    op.drop_column('accounts_users', 'previous_passwords')
    # ### end Alembic commands ###
