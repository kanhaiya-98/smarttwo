"""Database migration for supplier discovery feature."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers
revision = 'supplier_discovery_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create discovered_suppliers table
    op.create_table(
        'discovered_suppliers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('website', sa.String(length=500), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('location', sa.String(length=100), nullable=True),
        sa.Column('display_email', sa.String(length=255), nullable=True),
        sa.Column('actual_email', sa.String(length=255), nullable=True),
        sa.Column('found_via_search', sa.Boolean(), nullable=True),
        sa.Column('search_query', sa.String(length=500), nullable=True),
        sa.Column('search_rank', sa.Integer(), nullable=True),
        sa.Column('discovery_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_demo_mode', sa.Boolean(), nullable=True),
        sa.Column('demo_identifier', sa.String(length=100), nullable=True),
        sa.Column('emails_sent', sa.Integer(), nullable=True),
        sa.Column('emails_received', sa.Integer(), nullable=True),
        sa.Column('last_email_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_response_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_responsive', sa.Boolean(), nullable=True),
        sa.Column('procurement_task_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_discovered_suppliers_id'), 'discovered_suppliers', ['id'], unique=False)
    
    # Create email_threads table
    op.create_table(
        'email_threads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('procurement_task_id', sa.Integer(), nullable=True),
        sa.Column('display_recipient', sa.String(length=255), nullable=True),
        sa.Column('actual_recipient', sa.String(length=255), nullable=True),
        sa.Column('subject', sa.Text(), nullable=True),
        sa.Column('thread_identifier', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('round_number', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_activity', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['supplier_id'], ['discovered_suppliers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_threads_id'), 'email_threads', ['id'], unique=False)
    op.create_index(op.f('ix_email_threads_supplier_id'), 'email_threads', ['supplier_id'], unique=False)
    op.create_index(op.f('ix_email_threads_procurement_task_id'), 'email_threads', ['procurement_task_id'], unique=False)
    
    # Create email_messages table
    op.create_table(
        'email_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('thread_id', sa.Integer(), nullable=False),
        sa.Column('sender', sa.String(length=255), nullable=True),
        sa.Column('recipient', sa.String(length=255), nullable=True),
        sa.Column('display_sender', sa.String(length=255), nullable=True),
        sa.Column('display_recipient', sa.String(length=255), nullable=True),
        sa.Column('subject', sa.Text(), nullable=True),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('html_body', sa.Text(), nullable=True),
        sa.Column('is_from_agent', sa.Boolean(), nullable=True),
        sa.Column('parsed_data', sa.JSON(), nullable=True),
        sa.Column('quoted_price', sa.Float(), nullable=True),
        sa.Column('delivery_days', sa.Integer(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['thread_id'], ['email_threads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_messages_id'), 'email_messages', ['id'], unique=False)
    op.create_index(op.f('ix_email_messages_thread_id'), 'email_messages', ['thread_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_email_messages_thread_id'), table_name='email_messages')
    op.drop_index(op.f('ix_email_messages_id'), table_name='email_messages')
    op.drop_table('email_messages')
    
    op.drop_index(op.f('ix_email_threads_procurement_task_id'), table_name='email_threads')
    op.drop_index(op.f('ix_email_threads_supplier_id'), table_name='email_threads')
    op.drop_index(op.f('ix_email_threads_id'), table_name='email_threads')
    op.drop_table('email_threads')
    
    op.drop_index(op.f('ix_discovered_suppliers_id'), table_name='discovered_suppliers')
    op.drop_table('discovered_suppliers')
