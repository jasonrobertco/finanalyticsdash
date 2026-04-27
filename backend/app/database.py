from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

# The engine is the low-level connection to Postgres.
# It manages a pool of connections so we don't open a new one on every request.
engine = create_engine(settings.database_url)

# SessionLocal is a factory — calling it produces a new database session.
# A session is a unit of work: you open it, do reads/writes, then close it.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models.

    Every model (Asset, PriceBar, etc.) inherits from this so SQLAlchemy
    knows they belong to the same database and can manage them together.
    """
    pass


def get_db():
    """FastAPI dependency that provides a database session per request.

    Uses a try/finally so the session is always closed, even if an error occurs.
    'yield' makes this a generator — FastAPI runs code before yield on the way in,
    and code after yield on the way out (like a with-block).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
