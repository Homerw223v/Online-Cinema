"""add notification fields

Revision ID: 88caa71825dc
Revises: 341c8f219e82
Create Date: 2024-03-17 11:42:58.770647

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '88caa71825dc'
down_revision: Union[str, None] = '341c8f219e82'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("confirmed_email", sa.Boolean, nullable=False, default=False),
        schema="auth",
    )
    op.add_column(
        "users",
        sa.Column("notice_email", sa.Boolean, nullable=False, default=True),
        schema="auth",
    )
    op.add_column(
        "users",
        sa.Column("notice_websocket", sa.Boolean, nullable=False, default=True),
        schema="auth",
    )
    op.add_column(
        "users",
        sa.Column("timezone_min", sa.Integer, nullable=False, default=180),
        schema="auth",
    )


def downgrade() -> None:
    op.add_column(table_name="users", column_name="confirmed_email", schema="auth")
    op.add_column(table_name="users", column_name="notice_email", schema="auth")
    op.add_column(table_name="users", column_name="notice_websocket", schema="auth")
    op.add_column(table_name="users", column_name="timezone_min", schema="auth")
