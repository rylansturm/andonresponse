"""kpi table

Revision ID: dfff15cfffba
Revises: 2960e7f06db0
Create Date: 2019-02-04 19:11:48.367243

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dfff15cfffba'
down_revision = '2960e7f06db0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('KPI',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('id_user', sa.Integer(), nullable=True),
    sa.Column('d', sa.Date(), nullable=True),
    sa.Column('demand', sa.Integer(), nullable=True),
    sa.Column('plan_cycle_time', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['id_user'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_KPI_d'), 'KPI', ['d'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_KPI_d'), table_name='KPI')
    op.drop_table('KPI')
    # ### end Alembic commands ###
