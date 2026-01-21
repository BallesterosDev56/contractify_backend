"""Initial schema with all modules

Revision ID: 001_initial
Revises:
Create Date: 2026-01-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create schemas
    op.execute('CREATE SCHEMA IF NOT EXISTS users')
    op.execute('CREATE SCHEMA IF NOT EXISTS contracts')
    op.execute('CREATE SCHEMA IF NOT EXISTS ai')
    op.execute('CREATE SCHEMA IF NOT EXISTS signatures')
    op.execute('CREATE SCHEMA IF NOT EXISTS notifications')
    op.execute('CREATE SCHEMA IF NOT EXISTS audit')

    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # ============== Users Schema ==============

    op.create_table(
        'users',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('first_name', sa.String(100)),
        sa.Column('last_name', sa.String(100)),
        sa.Column('role', sa.String(20), default='USER'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        schema='users'
    )

    op.create_table(
        'user_preferences',
        sa.Column('user_id', sa.String(100), primary_key=True),
        sa.Column('preferences', postgresql.JSONB, default={}),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        schema='users'
    )

    op.create_table(
        'user_sessions',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('user_id', sa.String(100), nullable=False, index=True),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        schema='users'
    )

    # ============== Contracts Schema ==============

    op.create_table(
        'contracts',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('contract_type', sa.String(100), nullable=False),
        sa.Column('template_id', sa.String(100), nullable=False),
        sa.Column('owner_user_id', sa.String(100), nullable=False, index=True),
        sa.Column('status', sa.String(20), default='DRAFT', nullable=False),
        sa.Column('metadata', postgresql.JSONB, default={}, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('signed_at', sa.DateTime(timezone=True)),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
        sa.CheckConstraint("char_length(title) >= 3", name='contracts_title_min_length'),
        sa.CheckConstraint("status IN ('DRAFT', 'GENERATED', 'SIGNING', 'SIGNED', 'CANCELLED', 'EXPIRED')", name='contracts_status_valid'),
        schema='contracts'
    )

    op.create_table(
        'contract_versions',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('contract_id', postgresql.UUID(as_uuid=False), sa.ForeignKey('contracts.contracts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.Integer, nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('source', sa.String(10), nullable=False),
        sa.Column('created_by', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('version > 0', name='version_number_positive'),
        sa.CheckConstraint("source IN ('AI', 'USER')", name='version_source_valid'),
        sa.UniqueConstraint('contract_id', 'version', name='version_unique_per_contract'),
        schema='contracts'
    )

    op.create_table(
        'contract_parties',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('contract_id', postgresql.UUID(as_uuid=False), sa.ForeignKey('contracts.contracts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(10), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('signature_status', sa.String(10), default='PENDING', nullable=False),
        sa.Column('signed_at', sa.DateTime(timezone=True)),
        sa.Column('signing_order', sa.Integer, default=1, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("role IN ('HOST', 'GUEST', 'WITNESS')", name='party_role_valid'),
        sa.CheckConstraint("signature_status IN ('PENDING', 'INVITED', 'SIGNED')", name='party_signature_status_valid'),
        sa.CheckConstraint('signing_order > 0', name='party_signing_order_positive'),
        sa.UniqueConstraint('contract_id', 'email', name='party_email_unique_per_contract'),
        schema='contracts'
    )

    op.create_table(
        'activity_logs',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('contract_id', postgresql.UUID(as_uuid=False), sa.ForeignKey('contracts.contracts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('action', sa.String(20), nullable=False),
        sa.Column('user_id', sa.String(100), nullable=False),
        sa.Column('user_name', sa.String(255), nullable=False),
        sa.Column('details', postgresql.JSONB, default={}, nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("action IN ('CREATED', 'UPDATED', 'GENERATED', 'SIGNED', 'SENT', 'CANCELLED')", name='activity_action_valid'),
        schema='contracts'
    )

    # ============== AI Schema ==============

    op.create_table(
        'async_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('job_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), default='PENDING', nullable=False),
        sa.Column('progress', sa.Integer, default=0),
        sa.Column('input_data', postgresql.JSONB, default={}),
        sa.Column('result', postgresql.JSONB),
        sa.Column('error', sa.Text),
        sa.Column('user_id', sa.String(100), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        schema='ai'
    )

    op.create_table(
        'ai_cache',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('cache_key', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('metadata', postgresql.JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        schema='ai'
    )

    # ============== Signatures Schema ==============

    op.create_table(
        'signatures',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('contract_id', sa.String(100), nullable=False, index=True),
        sa.Column('party_id', sa.String(100), nullable=False, index=True),
        sa.Column('party_name', sa.String(255)),
        sa.Column('role', sa.String(20)),
        sa.Column('document_hash', sa.String(64)),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.Text),
        sa.Column('geolocation', sa.String(255)),
        sa.Column('evidence', postgresql.JSONB, default={}),
        sa.Column('signed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema='signatures'
    )

    op.create_table(
        'signature_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('token', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('contract_id', sa.String(100), nullable=False),
        sa.Column('party_id', sa.String(100), nullable=False),
        sa.Column('used', sa.Boolean, default=False),
        sa.Column('used_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        schema='signatures'
    )

    # ============== Notifications Schema ==============

    op.create_table(
        'invitations',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('contract_id', sa.String(100), nullable=False, index=True),
        sa.Column('party_id', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('message', sa.Text),
        sa.Column('status', sa.String(20), default='SENT'),
        sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('cancelled_at', sa.DateTime(timezone=True)),
        sa.Column('sent_by', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema='notifications'
    )

    op.create_table(
        'reminders',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('contract_id', sa.String(100), nullable=False, index=True),
        sa.Column('party_id', sa.String(100), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('sent', sa.Boolean, default=False),
        sa.Column('sent_at', sa.DateTime(timezone=True)),
        sa.Column('created_by', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema='notifications'
    )

    # ============== Audit Schema ==============

    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('contract_id', sa.String(100), nullable=False, index=True),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('actor', sa.String(255)),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.Text),
        sa.Column('details', postgresql.JSONB, default={}),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema='audit'
    )

    # ============== Indexes ==============

    op.create_index('idx_contracts_owner_lookup', 'contracts', ['owner_user_id', sa.text('created_at DESC')],
                    schema='contracts', postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_contracts_status', 'contracts', ['status'],
                    schema='contracts', postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_versions_contract', 'contract_versions', ['contract_id', sa.text('version DESC')], schema='contracts')
    op.create_index('idx_parties_contract', 'contract_parties', ['contract_id'], schema='contracts')
    op.create_index('idx_activity_contract', 'activity_logs', ['contract_id', sa.text('timestamp DESC')], schema='contracts')


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('audit_logs', schema='audit')
    op.drop_table('reminders', schema='notifications')
    op.drop_table('invitations', schema='notifications')
    op.drop_table('signature_tokens', schema='signatures')
    op.drop_table('signatures', schema='signatures')
    op.drop_table('ai_cache', schema='ai')
    op.drop_table('async_jobs', schema='ai')
    op.drop_table('activity_logs', schema='contracts')
    op.drop_table('contract_parties', schema='contracts')
    op.drop_table('contract_versions', schema='contracts')
    op.drop_table('contracts', schema='contracts')
    op.drop_table('user_sessions', schema='users')
    op.drop_table('user_preferences', schema='users')
    op.drop_table('users', schema='users')

    # Drop schemas
    op.execute('DROP SCHEMA IF EXISTS audit CASCADE')
    op.execute('DROP SCHEMA IF EXISTS notifications CASCADE')
    op.execute('DROP SCHEMA IF EXISTS signatures CASCADE')
    op.execute('DROP SCHEMA IF EXISTS ai CASCADE')
    op.execute('DROP SCHEMA IF EXISTS contracts CASCADE')
    op.execute('DROP SCHEMA IF EXISTS users CASCADE')
