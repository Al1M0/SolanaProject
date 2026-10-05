"""Immutable experiment manifests and append-only attempts."""
from alembic import op
import sqlalchemy as sa
revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("experiments", sa.Column("id", sa.String(80), primary_key=True), sa.Column("dataset_id", sa.String(80), sa.ForeignKey("datasets.id"), nullable=False), sa.Column("manifest", sa.JSON(), nullable=False), sa.Column("manifest_hash", sa.String(64), nullable=False), sa.Column("status", sa.String(24), nullable=False), sa.Column("frozen_hash", sa.String(64)), sa.Column("training", sa.JSON()), sa.Column("sensitivity", sa.JSON()), sa.Column("holdout", sa.JSON()), sa.Column("error", sa.Text()), sa.Column("history", sa.JSON(), nullable=False), sa.Column("created_at", sa.String(40), nullable=False))
    if op.get_bind().dialect.name == "sqlite":
        op.execute("CREATE TRIGGER experiments_immutable BEFORE UPDATE OF manifest, manifest_hash, dataset_id, id ON experiments BEGIN SELECT RAISE(ABORT, 'Experiment snapshot is immutable'); END")
        op.execute("CREATE TRIGGER experiments_frozen BEFORE UPDATE OF frozen_hash ON experiments WHEN OLD.frozen_hash IS NOT NULL AND NEW.frozen_hash IS NOT OLD.frozen_hash BEGIN SELECT RAISE(ABORT, 'Frozen hash is immutable'); END")
    else:
        op.execute("CREATE FUNCTION protect_experiment_snapshot() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN IF NEW.manifest::text IS DISTINCT FROM OLD.manifest::text OR NEW.manifest_hash IS DISTINCT FROM OLD.manifest_hash OR NEW.dataset_id IS DISTINCT FROM OLD.dataset_id OR NEW.id IS DISTINCT FROM OLD.id OR (OLD.frozen_hash IS NOT NULL AND NEW.frozen_hash IS DISTINCT FROM OLD.frozen_hash) THEN RAISE EXCEPTION 'Experiment snapshot is immutable'; END IF; RETURN NEW; END $$")
        op.execute("CREATE TRIGGER experiments_immutable BEFORE UPDATE ON experiments FOR EACH ROW EXECUTE FUNCTION protect_experiment_snapshot()")

def downgrade():
    op.drop_table("experiments")
    if op.get_bind().dialect.name != "sqlite":
        op.execute("DROP FUNCTION protect_experiment_snapshot()")
