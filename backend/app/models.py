"""ORM models — each class maps to one table in Postgres.

SQLAlchemy's ORM (Object-Relational Mapper) lets us work with database rows
as Python objects instead of writing raw SQL for every operation.
"""

import datetime
import enum
from typing import List, Optional  # Required on Python 3.9 — use Optional[X] instead of X | None

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Asset(Base):
    """Represents a financial instrument (stock, ETF, etc.).

    Storing assets in their own table means we never repeat metadata like
    the company name or exchange — we just reference the asset's id.
    This is called normalization: one source of truth per piece of data.
    """

    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)

    # The ticker symbol, e.g. "AAPL". Must be unique — no two assets share a ticker.
    ticker: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)

    name: Mapped[Optional[str]] = mapped_column(String(255))       # e.g. "Apple Inc."
    exchange: Mapped[Optional[str]] = mapped_column(String(50))    # e.g. "NASDAQ"
    asset_type: Mapped[Optional[str]] = mapped_column(String(50))  # e.g. "stock", "etf"

    # created_at is set automatically to now() by the database when a row is inserted.
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships let us navigate from an Asset to its related rows in Python,
    # e.g. asset.price_bars returns a list of PriceBar objects.
    price_bars: Mapped[List["PriceBar"]] = relationship(back_populates="asset")
    ingestion_jobs: Mapped[List["IngestionJob"]] = relationship(back_populates="asset")

    def __repr__(self) -> str:
        return f"<Asset {self.ticker}>"


class PriceBar(Base):
    """One row = one day of OHLCV data for one asset.

    OHLCV = Open, High, Low, Close, Volume — the standard format for daily price data.

    This table will grow large over time (years × tickers × daily bars), so we:
    1. Add a composite unique constraint on (asset_id, date, interval) to prevent duplicates
       during re-ingestion (upserting the same day twice should update, not duplicate).
    2. Convert it to a TimescaleDB hypertable (see migration) so time-range queries
       are fast even at millions of rows.
    """

    __tablename__ = "price_bars"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # Foreign key links each price bar back to its asset.
    # ondelete="CASCADE" means if an Asset is deleted, its price bars are deleted too.
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)

    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)

    # "1d" for daily bars. Keeping this column lets us store intraday data later.
    interval: Mapped[str] = mapped_column(String(10), nullable=False, default="1d")

    # Numeric(12, 4) = up to 12 digits total, 4 after the decimal point.
    # We use Numeric (not Float) for prices because Float has rounding errors.
    open: Mapped[Optional[float]] = mapped_column(Numeric(12, 4))
    high: Mapped[Optional[float]] = mapped_column(Numeric(12, 4))
    low: Mapped[Optional[float]] = mapped_column(Numeric(12, 4))
    close: Mapped[Optional[float]] = mapped_column(Numeric(12, 4))
    volume: Mapped[Optional[int]] = mapped_column(BigInteger)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    asset: Mapped["Asset"] = relationship(back_populates="price_bars")

    __table_args__ = (
        # Prevents duplicate rows for the same asset + date + interval.
        # The ingestion pipeline uses this to upsert (insert or update on conflict).
        UniqueConstraint("asset_id", "date", "interval", name="uq_price_bars_asset_date_interval"),
        # Composite index speeds up the most common query pattern:
        # "give me all daily bars for asset X between date A and date B"
        Index("ix_price_bars_asset_date", "asset_id", "date"),
    )

    def __repr__(self) -> str:
        return f"<PriceBar {self.asset_id} {self.date}>"


class JobStatus(str, enum.Enum):
    """Possible states for an ingestion job.

    Using an enum (instead of raw strings) means the database enforces valid values —
    you can't accidentally insert "sucess" (typo) instead of "success".
    """

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class IngestionJob(Base):
    """Tracks each run of the data ingestion pipeline.

    Every time we fetch price data from the external API, we log it here.
    This gives us visibility into what ran, when, and whether it succeeded —
    essential for debugging and for retry logic.
    """

    __tablename__ = "ingestion_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Nullable: a job might cover multiple assets (bulk refresh) with no specific asset.
    asset_id: Mapped[Optional[int]] = mapped_column(ForeignKey("assets.id", ondelete="SET NULL"))

    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status"), nullable=False, default=JobStatus.PENDING
    )

    # Timestamps for when the job started and finished.
    started_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True))

    # How many price bar rows were inserted or updated.
    rows_upserted: Mapped[Optional[int]] = mapped_column()

    # Store any error message if the job failed.
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    asset: Mapped[Optional["Asset"]] = relationship(back_populates="ingestion_jobs")

    def __repr__(self) -> str:
        return f"<IngestionJob {self.id} {self.status}>"
