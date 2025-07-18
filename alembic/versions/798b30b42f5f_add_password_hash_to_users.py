"""add_password_hash_to_users

Revision ID: 798b30b42f5f
Revises: c3989e3b5115
Create Date: 2025-05-31 19:45:40.401690

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '798b30b42f5f'
down_revision: Union[str, None] = 'c3989e3b5115'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('password_hash', sa.String(length=255), nullable=False))
    op.alter_column('users', 'username',
                existing_type=sa.VARCHAR(length=50),
                nullable=True)
    op.alter_column('users', 'email',
                existing_type=sa.VARCHAR(length=100),
                nullable=True)
    op.alter_column('users', 'is_active',
                existing_type=sa.BOOLEAN(),
                nullable=True)
    op.alter_column('users', 'is_superuser',
                existing_type=sa.BOOLEAN(),
                nullable=True)
    op.alter_column('users', 'created_at',
                existing_type=postgresql.TIMESTAMP(),
                type_=sa.DateTime(timezone=True),
                nullable=True,
                existing_server_default=sa.text('now()'))
    op.alter_column('users', 'updated_at',
                existing_type=postgresql.TIMESTAMP(),
                type_=sa.DateTime(timezone=True),
                nullable=True,
                existing_server_default=sa.text('now()'))
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.alter_column('users', 'updated_at',
                existing_type=sa.DateTime(timezone=True),
                type_=postgresql.TIMESTAMP(),
                nullable=False,
                existing_server_default=sa.text('now()'))
    op.alter_column('users', 'created_at',
                existing_type=sa.DateTime(timezone=True),
                type_=postgresql.TIMESTAMP(),
                nullable=False,
                existing_server_default=sa.text('now()'))
    op.alter_column('users', 'is_superuser',
                existing_type=sa.BOOLEAN(),
                nullable=False)
    op.alter_column('users', 'is_active',
                existing_type=sa.BOOLEAN(),
                nullable=False)
    op.alter_column('users', 'email',
                existing_type=sa.VARCHAR(length=100),
                nullable=False)
    op.alter_column('users', 'username',
                existing_type=sa.VARCHAR(length=50),
                nullable=False)
    op.drop_column('users', 'password_hash')
    # ### end Alembic commands ###
