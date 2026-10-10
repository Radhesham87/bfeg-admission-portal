import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Cloud Run has an ephemeral filesystem, so production must point at a managed
# database. Set DATABASE_URL to your Postgres connection string there.
# Local development falls back to a SQLite file.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bfeg_local.db")

if DATABASE_URL.startswith("postgres://"):          # Heroku/Neon style URL
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_columns():
    """Add columns introduced after the first deploy (create_all never alters tables)."""
    from sqlalchemy import inspect, text
    wanted = {
        "ps_launch_hash": "VARCHAR(64) DEFAULT ''",
        "ps_sync_status": "VARCHAR(20) DEFAULT ''",
        "ps_sync_error": "TEXT DEFAULT ''",
        "ps_last_attempt_at": "TIMESTAMP WITH TIME ZONE" if not DATABASE_URL.startswith("sqlite") else "TIMESTAMP",
        "version": "INTEGER NOT NULL DEFAULT 1",
        "ps_revision_key": "VARCHAR(80) DEFAULT ''",
        "updated_at": "TIMESTAMP WITH TIME ZONE" if not DATABASE_URL.startswith("sqlite") else "TIMESTAMP",
    }
    existing = {c["name"] for c in inspect(engine).get_columns("submissions")}
    with engine.begin() as conn:
        for name, ddl in wanted.items():
            if name not in existing:
                conn.execute(text(f"ALTER TABLE submissions ADD COLUMN {name} {ddl}"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_submissions_ps_launch_hash ON submissions (ps_launch_hash)"))
