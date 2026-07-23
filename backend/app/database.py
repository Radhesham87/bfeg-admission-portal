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
