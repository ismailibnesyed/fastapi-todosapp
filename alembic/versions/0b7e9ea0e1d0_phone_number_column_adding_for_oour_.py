"""Phone Number Column adding for oour user table

Revision ID: 0b7e9ea0e1d0
Revises: 
Create Date: 2026-08-03 02:39:15.329290

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0b7e9ea0e1d0'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column('phone_number', sa.String, nullable=True)) # nullable must be true because already users table has user data without phone number
    # """Upgrade schema."""
    # pass


def downgrade() -> None:
    op.drop_column('users', 'phone_number')
    # """Downgrade schema."""
    # pass
