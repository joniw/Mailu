"""add bcc table

Revision ID: 9da727ebb07a
Revises: 8f9ea78776f4
Create Date: 2022-06-16 15:10:10.984295

"""

# revision identifiers, used by Alembic.
revision = '9da727ebb07a'
down_revision = '8f9ea78776f4'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('bcc',
    sa.Column('created_at', sa.Date(), nullable=False),
    sa.Column('updated_at', sa.Date(), nullable=True),
    sa.Column('comment', sa.String(length=255), nullable=True),
    sa.Column('domain_name', sa.String(length=255), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('localpart', sa.String(length=80), nullable=False),
    sa.Column('bcc', sa.String(length=255), nullable=False),
    sa.Column('type', sa.Enum('sender', 'recipient'), nullable=False),
    sa.Column('user_permissions', sa.Enum('hidden', 'visible', 'edit'), nullable=False),
    sa.ForeignKeyConstraint(['domain_name'], ['domain.name'], name=op.f('bcc_domain_name_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('bcc_pkey'))
    )


def downgrade():
    op.drop_table('bcc')
