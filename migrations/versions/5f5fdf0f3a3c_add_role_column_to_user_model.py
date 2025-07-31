"""Add role column to User model

Revision ID: 5f5fdf0f3a3c
Revises: 8708b10e1072
Create Date: 2025-07-01 11:12:08.153687
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '5f5fdf0f3a3c'
down_revision = '8708b10e1072'
branch_labels = None
depends_on = None

def upgrade():
    # ✅ Add 'role' column with default='user'
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('role', sa.String(length=10), nullable=False, server_default='user')
        )

def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('role')
