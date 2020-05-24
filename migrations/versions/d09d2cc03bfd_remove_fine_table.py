"""remove fine table

Revision ID: d09d2cc03bfd
Revises: 9b9749bff31a
Create Date: 2020-05-24 15:57:41.082890

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd09d2cc03bfd'
down_revision = '9b9749bff31a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('fine')
    op.drop_table('sqlite_sequence')
    op.alter_column('gameweek_performance', 'element_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('gameweek_performance', 'element_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.create_table('sqlite_sequence',
    sa.Column('name', sa.NullType(), nullable=True),
    sa.Column('seq', sa.NullType(), nullable=True)
    )
    op.create_table('fine',
    sa.Column('fine_id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(length=64), nullable=True),
    sa.Column('description', sa.VARCHAR(length=256), nullable=True),
    sa.PrimaryKeyConstraint('fine_id')
    )
    # ### end Alembic commands ###