from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.pipeline.models.base import Base


class IngestionState(Base):
    __tablename__ = "ingestion_state"
    __table_args__ = {"schema": "raw"}

    id: Mapped[int] = mapped_column(primary_key=True)
    source_name: Mapped[str] = mapped_column(Text, default="ufcstats")
    date_from: Mapped[date | None] = mapped_column(Date)
    date_to: Mapped[date | None] = mapped_column(Date)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(Text, default="running")
    last_event_date: Mapped[date | None] = mapped_column(Date)
    last_event_source_id: Mapped[str | None] = mapped_column(Text)
    events_inserted: Mapped[int] = mapped_column(Integer, default=0)
    events_updated: Mapped[int] = mapped_column(Integer, default=0)
    fighters_inserted: Mapped[int] = mapped_column(Integer, default=0)
    fighters_updated: Mapped[int] = mapped_column(Integer, default=0)
    fights_inserted: Mapped[int] = mapped_column(Integer, default=0)
    fights_updated: Mapped[int] = mapped_column(Integer, default=0)
    fight_stats_inserted: Mapped[int] = mapped_column(Integer, default=0)
    fight_stats_updated: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    error_traceback: Mapped[str | None] = mapped_column(Text)
