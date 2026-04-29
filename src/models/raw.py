from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class Fighter(Base):
    __tablename__ = "fighters"
    __table_args__ = {"schema": "raw"}

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[str] = mapped_column(Text, unique=True)
    full_name: Mapped[str | None] = mapped_column(Text)
    first_name: Mapped[str | None] = mapped_column(Text)
    last_name: Mapped[str | None] = mapped_column(Text)
    nickname: Mapped[str | None] = mapped_column(Text)
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    height_cm: Mapped[float | None] = mapped_column(Numeric(5, 1))
    reach_cm: Mapped[float | None] = mapped_column(Numeric(5, 1))
    stance: Mapped[str | None] = mapped_column(Text)
    weight_class: Mapped[str | None] = mapped_column(Text)
    wins: Mapped[int | None] = mapped_column(Integer)
    losses: Mapped[int | None] = mapped_column(Integer)
    draws: Mapped[int | None] = mapped_column(Integer)
    photo_url: Mapped[str | None] = mapped_column(Text)
    photo_source: Mapped[str | None] = mapped_column(Text)
    photo_status: Mapped[str | None] = mapped_column(Text)
    photo_last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_payload: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Event(Base):
    __tablename__ = "events"
    __table_args__ = {"schema": "raw"}

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[str] = mapped_column(Text, unique=True)
    event_name: Mapped[str | None] = mapped_column(Text)
    event_date: Mapped[date | None] = mapped_column(Date)
    location: Mapped[str | None] = mapped_column(Text)
    promotion: Mapped[str | None] = mapped_column(Text)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Fight(Base):
    __tablename__ = "fights"
    __table_args__ = {"schema": "raw"}

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[str] = mapped_column(Text, unique=True)
    event_source_id: Mapped[str | None] = mapped_column(Text)
    event_id: Mapped[int | None] = mapped_column(ForeignKey("raw.events.id"))
    fighter_1_source_id: Mapped[str | None] = mapped_column(Text)
    fighter_2_source_id: Mapped[str | None] = mapped_column(Text)
    fighter_1_id: Mapped[int | None] = mapped_column(ForeignKey("raw.fighters.id"))
    fighter_2_id: Mapped[int | None] = mapped_column(ForeignKey("raw.fighters.id"))
    winner_source_id: Mapped[str | None] = mapped_column(Text)
    winner_id: Mapped[int | None] = mapped_column(ForeignKey("raw.fighters.id"))
    weight_class: Mapped[str | None] = mapped_column(Text)
    gender: Mapped[str | None] = mapped_column(Text)
    fight_order: Mapped[int | None] = mapped_column(Integer)
    scheduled_rounds: Mapped[int | None] = mapped_column(Integer)
    time_format_raw: Mapped[str | None] = mapped_column(Text)
    finish_round: Mapped[int | None] = mapped_column(Integer)
    finish_time_seconds: Mapped[int | None] = mapped_column(Integer)
    result_method: Mapped[str | None] = mapped_column(Text)
    result_details: Mapped[str | None] = mapped_column(Text)
    referee: Mapped[str | None] = mapped_column(Text)
    title_fight: Mapped[bool | None] = mapped_column(Boolean)
    performance_bonus: Mapped[bool | None] = mapped_column(Boolean)
    fight_of_the_night: Mapped[bool | None] = mapped_column(Boolean)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FightStats(Base):
    __tablename__ = "fight_stats"
    __table_args__ = (
        UniqueConstraint("fight_id", "fighter_id"),
        {"schema": "raw"},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    fight_id: Mapped[int] = mapped_column(ForeignKey("raw.fights.id"))
    fighter_id: Mapped[int] = mapped_column(ForeignKey("raw.fighters.id"))
    knockdowns: Mapped[int | None] = mapped_column(Integer)
    sig_strikes_landed: Mapped[int | None] = mapped_column(Integer)
    sig_strikes_attempted: Mapped[int | None] = mapped_column(Integer)
    total_strikes_landed: Mapped[int | None] = mapped_column(Integer)
    total_strikes_attempted: Mapped[int | None] = mapped_column(Integer)
    takedowns_landed: Mapped[int | None] = mapped_column(Integer)
    takedowns_attempted: Mapped[int | None] = mapped_column(Integer)
    submissions_attempted: Mapped[int | None] = mapped_column(Integer)
    reversals: Mapped[int | None] = mapped_column(Integer)
    control_time_seconds: Mapped[int | None] = mapped_column(Integer)
    head_strikes_landed: Mapped[int | None] = mapped_column(Integer)
    head_strikes_attempted: Mapped[int | None] = mapped_column(Integer)
    body_strikes_landed: Mapped[int | None] = mapped_column(Integer)
    body_strikes_attempted: Mapped[int | None] = mapped_column(Integer)
    leg_strikes_landed: Mapped[int | None] = mapped_column(Integer)
    leg_strikes_attempted: Mapped[int | None] = mapped_column(Integer)
    distance_strikes_landed: Mapped[int | None] = mapped_column(Integer)
    distance_strikes_attempted: Mapped[int | None] = mapped_column(Integer)
    clinch_strikes_landed: Mapped[int | None] = mapped_column(Integer)
    clinch_strikes_attempted: Mapped[int | None] = mapped_column(Integer)
    ground_strikes_landed: Mapped[int | None] = mapped_column(Integer)
    ground_strikes_attempted: Mapped[int | None] = mapped_column(Integer)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
