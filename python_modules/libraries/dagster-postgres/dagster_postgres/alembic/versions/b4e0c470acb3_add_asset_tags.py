"""add asset tags

Revision ID: b4e0c470acb3
Revises: 3e71cf573ba6
Create Date: 2021-03-04 10:20:27.847208

"""
from dagster.core.storage.migration.utils import add_asset_detail_columns

# revision identifiers, used by Alembic.
revision = "b4e0c470acb3"
down_revision = "3e71cf573ba6"
branch_labels = None
depends_on = None


def upgrade():
    add_asset_detail_columns()


def downgrade():
    pass
