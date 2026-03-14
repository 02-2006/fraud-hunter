"""Initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2026-03-14
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('external_id', sa.String(64), unique=True, nullable=False),
        sa.Column('account_id', sa.String(64), nullable=False),
        sa.Column('merchant_id', sa.String(64)),
        sa.Column('merchant_name', sa.String(256)),
        sa.Column('amount', sa.Float, nullable=False),
        sa.Column('currency', sa.String(3), default='USD'),
        sa.Column('country_origin', sa.String(2)),
        sa.Column('country_merchant', sa.String(2)),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('device_fingerprint', sa.String(128)),
        sa.Column('card_last4', sa.String(4)),
        sa.Column('is_card_present', sa.Boolean, default=True),
        sa.Column('timestamp', sa.DateTime),
        sa.Column('risk_score', sa.Float, default=0.0),
        sa.Column('risk_level', sa.String(16), default='clear'),
        sa.Column('status', sa.String(16), default='pending'),
        sa.Column('features', postgresql.JSON),
        sa.Column('agent_findings', postgresql.JSON),
        sa.Column('ai_reasoning', sa.Text),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
    )
    op.create_index('ix_tx_account_timestamp', 'transactions', ['account_id', 'timestamp'])
    op.create_index('ix_tx_risk_level', 'transactions', ['risk_level'])
    op.create_index('ix_tx_external_id', 'transactions', ['external_id'], unique=True)

    op.create_table(
        'fraud_cases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('case_number', sa.String(32), unique=True, nullable=False),
        sa.Column('account_id', sa.String(64), nullable=False),
        sa.Column('status', sa.String(32), default='open'),
        sa.Column('total_exposure', sa.Float, default=0.0),
        sa.Column('fraud_type', sa.String(64)),
        sa.Column('assigned_to', sa.String(128)),
        sa.Column('notes', sa.Text),
        sa.Column('evidence', postgresql.JSON),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
    )

    op.create_table(
        'alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('transactions.id'), nullable=True),
        sa.Column('case_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('fraud_cases.id'), nullable=True),
        sa.Column('alert_type', sa.String(64), nullable=False),
        sa.Column('severity', sa.String(16), nullable=False),
        sa.Column('message', sa.Text),
        sa.Column('agent_id', sa.String(64)),
        sa.Column('resolved', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime),
    )
    op.create_index('ix_alerts_transaction_id', 'alerts', ['transaction_id'])

    op.create_table(
        'agent_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', sa.String(64), nullable=False),
        sa.Column('agent_type', sa.String(64)),
        sa.Column('transactions_scanned', sa.Integer, default=0),
        sa.Column('flags_raised', sa.Integer, default=0),
        sa.Column('started_at', sa.DateTime),
        sa.Column('ended_at', sa.DateTime, nullable=True),
        sa.Column('status', sa.String(32), default='running'),
        sa.Column('metadata', postgresql.JSON),
    )

    op.create_table(
        'model_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('model_version', sa.String(32)),
        sa.Column('precision', sa.Float),
        sa.Column('recall', sa.Float),
        sa.Column('f1_score', sa.Float),
        sa.Column('false_positive_rate', sa.Float),
        sa.Column('transactions_evaluated', sa.Integer),
        sa.Column('recorded_at', sa.DateTime),
    )


def downgrade() -> None:
    op.drop_table('model_metrics')
    op.drop_table('agent_runs')
    op.drop_table('alerts')
    op.drop_table('fraud_cases')
    op.drop_table('transactions')
