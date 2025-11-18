"""Initial migration - Create all tables

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True, default=False),
        sa.Column('subscription_tier', sa.String(), nullable=True, default='free'),
        sa.Column('subscription_expires_at', sa.DateTime(), nullable=True),
        sa.Column('exchange_credentials', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create exchange_credentials table
    op.create_table(
        'exchange_credentials',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('exchange_name', sa.String(), nullable=False),
        sa.Column('api_key_encrypted', sa.String(), nullable=False),
        sa.Column('api_secret_encrypted', sa.String(), nullable=False),
        sa.Column('is_testnet', sa.Boolean(), nullable=True, default=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_exchange_credentials_user_id'), 'exchange_credentials', ['user_id'], unique=False)

    # Create strategies table
    op.create_table(
        'strategies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('strategy_type', sa.String(), nullable=False),
        sa.Column('parameters', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('model_path', sa.String(), nullable=True),
        sa.Column('model_version', sa.String(), nullable=True),
        sa.Column('backtest_results', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('sharpe_ratio', sa.Numeric(10, 4), nullable=True),
        sa.Column('max_drawdown', sa.Numeric(10, 4), nullable=True),
        sa.Column('win_rate', sa.Numeric(5, 2), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_public', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create trading_bots table
    op.create_table(
        'trading_bots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('exchange', sa.String(), nullable=False),
        sa.Column('trading_pair', sa.String(), nullable=False),
        sa.Column('strategy_id', sa.Integer(), nullable=True),
        sa.Column('initial_capital', sa.Numeric(20, 8), nullable=False),
        sa.Column('current_capital', sa.Numeric(20, 8), nullable=False),
        sa.Column('max_position_size', sa.Numeric(5, 2), nullable=True, default=10.0),
        sa.Column('stop_loss_percentage', sa.Numeric(5, 2), nullable=True, default=5.0),
        sa.Column('take_profit_percentage', sa.Numeric(5, 2), nullable=True, default=10.0),
        sa.Column('max_daily_loss', sa.Numeric(20, 8), nullable=True),
        sa.Column('status', sa.String(), nullable=True, default='stopped'),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('total_trades', sa.Integer(), nullable=True, default=0),
        sa.Column('winning_trades', sa.Integer(), nullable=True, default=0),
        sa.Column('losing_trades', sa.Integer(), nullable=True, default=0),
        sa.Column('total_profit_loss', sa.Numeric(20, 8), nullable=True, default=0),
        sa.Column('win_rate', sa.Numeric(5, 2), nullable=True, default=0),
        sa.Column('config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('stopped_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['strategy_id'], ['strategies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create orders table
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bot_id', sa.Integer(), nullable=False),
        sa.Column('exchange_order_id', sa.String(), nullable=True),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('side', sa.String(), nullable=False),
        sa.Column('order_type', sa.String(), nullable=False),
        sa.Column('quantity', sa.Numeric(20, 8), nullable=False),
        sa.Column('price', sa.Numeric(20, 8), nullable=True),
        sa.Column('stop_price', sa.Numeric(20, 8), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('filled_quantity', sa.Numeric(20, 8), nullable=True, default=0),
        sa.Column('remaining_quantity', sa.Numeric(20, 8), nullable=False),
        sa.Column('average_fill_price', sa.Numeric(20, 8), nullable=True),
        sa.Column('fee', sa.Numeric(20, 8), nullable=True, default=0),
        sa.Column('fee_currency', sa.String(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('filled_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['bot_id'], ['trading_bots.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_orders_exchange_order_id'), 'orders', ['exchange_order_id'], unique=True)

    # Create trades table
    op.create_table(
        'trades',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bot_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('entry_order_id', sa.Integer(), nullable=True),
        sa.Column('exit_order_id', sa.Integer(), nullable=True),
        sa.Column('entry_price', sa.Numeric(20, 8), nullable=False),
        sa.Column('entry_quantity', sa.Numeric(20, 8), nullable=False),
        sa.Column('entry_time', sa.DateTime(), nullable=False),
        sa.Column('exit_price', sa.Numeric(20, 8), nullable=True),
        sa.Column('exit_quantity', sa.Numeric(20, 8), nullable=True),
        sa.Column('exit_time', sa.DateTime(), nullable=True),
        sa.Column('profit_loss', sa.Numeric(20, 8), nullable=True),
        sa.Column('profit_loss_percentage', sa.Numeric(10, 4), nullable=True),
        sa.Column('realized_pnl', sa.Numeric(20, 8), nullable=True, default=0),
        sa.Column('is_open', sa.Boolean(), nullable=True, default=True),
        sa.Column('trade_side', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['bot_id'], ['trading_bots.id'], ),
        sa.ForeignKeyConstraint(['entry_order_id'], ['orders.id'], ),
        sa.ForeignKeyConstraint(['exit_order_id'], ['orders.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create market_data table
    op.create_table(
        'market_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('exchange', sa.String(), nullable=False),
        sa.Column('timeframe', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('open', sa.Numeric(20, 8), nullable=False),
        sa.Column('high', sa.Numeric(20, 8), nullable=False),
        sa.Column('low', sa.Numeric(20, 8), nullable=False),
        sa.Column('close', sa.Numeric(20, 8), nullable=False),
        sa.Column('volume', sa.Numeric(20, 8), nullable=False),
        sa.Column('indicators', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_market_data_symbol'), 'market_data', ['symbol'], unique=False)
    op.create_index(op.f('ix_market_data_timestamp'), 'market_data', ['timestamp'], unique=False)


def downgrade() -> None:
    op.drop_table('market_data')
    op.drop_table('trades')
    op.drop_table('orders')
    op.drop_table('trading_bots')
    op.drop_table('strategies')
    op.drop_table('exchange_credentials')
    op.drop_table('users')
