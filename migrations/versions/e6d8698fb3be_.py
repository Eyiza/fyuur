"""empty message

Revision ID: e6d8698fb3be
Revises: fdf3bdf9a726
Create Date: 2022-06-04 01:54:00.400913

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e6d8698fb3be'
down_revision = 'fdf3bdf9a726'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('artists', 'genres',
               existing_type=postgresql.ARRAY(sa.VARCHAR(length=120)),
               nullable=False)
    op.create_unique_constraint(None, 'artists', ['name', 'phone', 'website_link'])
    op.alter_column('venues', 'genres',
               existing_type=postgresql.ARRAY(sa.VARCHAR(length=120)),
               nullable=False)
    op.create_unique_constraint(None, 'venues', ['name', 'phone', 'website_link'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'venues', type_='unique')
    op.alter_column('venues', 'genres',
               existing_type=postgresql.ARRAY(sa.VARCHAR(length=120)),
               nullable=True)
    op.drop_constraint(None, 'artists', type_='unique')
    op.alter_column('artists', 'genres',
               existing_type=postgresql.ARRAY(sa.VARCHAR(length=120)),
               nullable=True)
    # ### end Alembic commands ###