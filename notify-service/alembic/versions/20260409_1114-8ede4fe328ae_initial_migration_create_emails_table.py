"""Initial migration: create emails table

Revision ID: 8ede4fe328ae
Revises: 
Create Date: 2026-04-09 11:14:28.413900

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '8ede4fe328ae'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create emails table."""
    connection = op.get_bind()
    
    # Create ENUM type if it doesn't exist
    # Using savepoint to handle potential duplicate error gracefully
    connection.execute(sa.text(
        """
        DO $$ BEGIN
            CREATE TYPE emailstatus AS ENUM ('PENDING', 'PROCESSING', 'SUCCESS', 'FAILED');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
        """
    ))
    
    # Create emails table
    op.create_table(
        'emails',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('recipient', sa.String(length=255), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('status', postgresql.ENUM('PENDING', 'PROCESSING', 'SUCCESS', 'FAILED', name='emailstatus', create_type=False), nullable=False, server_default='PENDING'),
        sa.Column('task_id', sa.String(length=255), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_emails_id', 'emails', ['id'], unique=False)
    op.create_index('ix_emails_recipient', 'emails', ['recipient'], unique=False)
    op.create_index('ix_emails_status', 'emails', ['status'], unique=False)
    op.create_index('ix_emails_task_id', 'emails', ['task_id'], unique=True)
    op.create_index('ix_emails_created_at', 'emails', ['created_at'], unique=False)


def downgrade() -> None:
    """Drop emails table."""
    op.drop_index('ix_emails_created_at', table_name='emails')
    op.drop_index('ix_emails_task_id', table_name='emails')
    op.drop_index('ix_emails_status', table_name='emails')
    op.drop_index('ix_emails_recipient', table_name='emails')
    op.drop_index('ix_emails_id', table_name='emails')
    op.drop_table('emails')
    
    # Drop ENUM
    email_status = postgresql.ENUM('PENDING', 'PROCESSING', 'SUCCESS', 'FAILED', name='emailstatus')
    email_status.drop(op.get_bind(), checkfirst=True)

