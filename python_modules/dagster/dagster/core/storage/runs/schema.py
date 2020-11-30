import sqlalchemy as db

RunStorageSqlMetadata = db.MetaData()

RunsTable = db.Table(
    "runs",
    RunStorageSqlMetadata,
    db.Column("id", db.Integer, primary_key=True, autoincrement=True),
    db.Column("run_id", db.String(255), unique=True),
    db.Column(
        "snapshot_id",
        db.String(255),
        db.ForeignKey("snapshots.snapshot_id", name="fk_runs_snapshot_id_snapshots_snapshot_id"),
    ),
    db.Column("pipeline_name", db.String),
    db.Column("status", db.String(63)),
    db.Column("run_body", db.String),
    db.Column("create_timestamp", db.DateTime, server_default=db.text("CURRENT_TIMESTAMP")),
    db.Column("update_timestamp", db.DateTime, server_default=db.text("CURRENT_TIMESTAMP")),
)

# Secondary Index migration table, used to track data migrations, both for event_logs and runs.
# This schema should match the schema in the event_log storage schema
SecondaryIndexMigrationTable = db.Table(
    "secondary_indexes",
    RunStorageSqlMetadata,
    db.Column("id", db.Integer, primary_key=True, autoincrement=True),
    db.Column("name", db.String, unique=True),
    db.Column("create_timestamp", db.DateTime, server_default=db.text("CURRENT_TIMESTAMP")),
    db.Column("migration_completed", db.DateTime),
)

RunTagsTable = db.Table(
    "run_tags",
    RunStorageSqlMetadata,
    db.Column("id", db.Integer, primary_key=True, autoincrement=True),
    db.Column("run_id", None, db.ForeignKey("runs.run_id", ondelete="CASCADE")),
    db.Column("key", db.String),
    db.Column("value", db.String),
)

SnapshotsTable = db.Table(
    "snapshots",
    RunStorageSqlMetadata,
    db.Column("id", db.Integer, primary_key=True, autoincrement=True, nullable=False),
    db.Column("snapshot_id", db.String(255), unique=True, nullable=False),
    db.Column("snapshot_body", db.LargeBinary, nullable=False),
    db.Column("snapshot_type", db.String(63), nullable=False),
)

DaemonHeartbeatsTable = db.Table(
    "daemon_heartbeats",
    RunStorageSqlMetadata,
    db.Column("daemon_type", db.String(255), unique=True, nullable=False),
    db.Column("daemon_id", db.String(255)),
    db.Column("timestamp", db.DateTime, nullable=False),
    db.Column("info", db.String),
)
