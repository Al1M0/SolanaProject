"""One-time signed wallet sessions and real observed portfolio history."""
from alembic import op
import sqlalchemy as sa
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("wallet_nonces", sa.Column("id", sa.String(64), primary_key=True), sa.Column("wallet", sa.String(44), nullable=False), sa.Column("nonce", sa.String(64), nullable=False), sa.Column("message", sa.Text(), nullable=False), sa.Column("origin", sa.String(240), nullable=False), sa.Column("issued_at", sa.Integer(), nullable=False), sa.Column("expires_at", sa.Integer(), nullable=False), sa.Column("consumed", sa.Integer(), nullable=False, server_default="0"))
    op.create_index("idx_wallet_nonces_wallet_issued", "wallet_nonces", ["wallet", "issued_at"])
    op.create_table("wallet_sessions", sa.Column("token_hash", sa.String(64), primary_key=True), sa.Column("wallet", sa.String(44), nullable=False), sa.Column("expires_at", sa.Integer(), nullable=False))
    op.create_table("wallet_snapshots", sa.Column("id", sa.String(100), primary_key=True), sa.Column("wallet", sa.String(44), nullable=False), sa.Column("ts", sa.Integer(), nullable=False), sa.Column("sol_balance", sa.Float(), nullable=False), sa.Column("valued_usd", sa.Float()), sa.Column("complete", sa.Integer(), nullable=False), sa.Column("payload", sa.JSON(), nullable=False))
    op.create_index("idx_wallet_snapshots_wallet_ts", "wallet_snapshots", ["wallet", "ts"])

def downgrade():
    for table in ("wallet_snapshots", "wallet_sessions", "wallet_nonces"):
        op.drop_table(table)
