"""adding discord notification toggleable

Revision ID: 60b7b4a547c4
Revises: 23283ad23884
Create Date: 2024-05-24 07:32:22.703268

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "60b7b4a547c4"
down_revision = "23283ad23884"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user_settings", sa.Column("discord_notification", sa.Boolean()))


def downgrade() -> None:
    op.drop_column("user_settings", "discord_notification")
