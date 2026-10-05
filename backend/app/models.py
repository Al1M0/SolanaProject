from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, JSON, ForeignKey, Text, UniqueConstraint, Index
from .db import Base


def now():
    return datetime.now(timezone.utc).isoformat()


class Dataset(Base):
    __tablename__ = "datasets"
    id = Column(String(80), primary_key=True)
    name = Column(String(200), nullable=False)
    kind = Column(String(12), nullable=False)
    metadata_json = Column(JSON, nullable=False)
    quality = Column(JSON, nullable=False)
    content_hash = Column(String(64), nullable=False)
    created_at = Column(String(40), default=now, nullable=False)


class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    dataset_id = Column(String(80), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(String(240), nullable=False)
    ts = Column(Integer, nullable=False)
    type = Column(String(20), nullable=False)
    token = Column(String(80), nullable=False)
    wallet = Column(String(80), nullable=True)
    payload = Column(JSON, nullable=False)
    __table_args__ = (UniqueConstraint("dataset_id", "event_id", name="uq_dataset_event"), Index("ix_events_timeline", "dataset_id", "ts"))


class Strategy(Base):
    __tablename__ = "strategies"
    id = Column(String(80), primary_key=True)
    dataset_id = Column(String(80), ForeignKey("datasets.id"), nullable=False)
    name = Column(String(120), nullable=False)
    config = Column(JSON, nullable=False)
    created_at = Column(String(40), default=now, nullable=False)


class Backtest(Base):
    __tablename__ = "backtests"
    id = Column(String(80), primary_key=True)
    strategy_id = Column(String(80), ForeignKey("strategies.id"), nullable=False)
    dataset_id = Column(String(80), ForeignKey("datasets.id"), nullable=False)
    status = Column(String(20), nullable=False, default="queued")
    progress = Column(Integer, nullable=False, default=0)
    config = Column(JSON, nullable=False)
    result = Column(JSON)
    error = Column(Text)
    created_at = Column(String(40), default=now, nullable=False)


class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True)
    backtest_id = Column(String(80), ForeignKey("backtests.id", ondelete="CASCADE"), nullable=False, index=True)
    trade_id = Column(String(80), nullable=False)
    segment = Column(String(20), nullable=False)
    payload = Column(JSON, nullable=False)
    __table_args__ = (UniqueConstraint("backtest_id", "trade_id", name="uq_backtest_trade"),)


class Report(Base):
    __tablename__ = "reports"
    id = Column(String(80), primary_key=True)
    backtest_id = Column(String(80), ForeignKey("backtests.id"), unique=True, nullable=False)
    markdown = Column(Text, nullable=False)
    created_at = Column(String(40), default=now, nullable=False)


class Ingestion(Base):
    __tablename__ = "ingestions"
    id = Column(String(80), primary_key=True)
    status = Column(String(20), nullable=False, default="queued")
    progress = Column(Integer, default=0, nullable=False)
    request = Column(JSON, nullable=False)
    result = Column(JSON)
    error = Column(Text)
    created_at = Column(String(40), default=now, nullable=False)

class WalletNonce(Base):
    __tablename__ = "wallet_nonces"
    id = Column(String(64), primary_key=True)
    wallet = Column(String(44), nullable=False)
    nonce = Column(String(64), nullable=False)
    message = Column(Text, nullable=False)
    origin = Column(String(240), nullable=False)
    issued_at = Column(Integer, nullable=False)
    expires_at = Column(Integer, nullable=False)
    consumed = Column(Integer, nullable=False, default=0)
    __table_args__ = (Index("idx_wallet_nonces_wallet_issued", "wallet", "issued_at"),)

class WalletSession(Base):
    __tablename__ = "wallet_sessions"
    token_hash = Column(String(64), primary_key=True)
    wallet = Column(String(44), nullable=False)
    expires_at = Column(Integer, nullable=False)

class WalletObservation(Base):
    __tablename__ = "wallet_snapshots"
    id = Column(String(100), primary_key=True)
    wallet = Column(String(44), nullable=False)
    ts = Column(Integer, nullable=False)
    sol_balance = Column(Float, nullable=False)
    valued_usd = Column(Float)
    complete = Column(Integer, nullable=False)
    payload = Column(JSON, nullable=False)
    __table_args__ = (Index("idx_wallet_snapshots_wallet_ts", "wallet", "ts"),)

class Experiment(Base):
    __tablename__ = "experiments"
    id = Column(String(80), primary_key=True)
    dataset_id = Column(String(80), ForeignKey("datasets.id"), nullable=False)
    manifest = Column(JSON, nullable=False)
    manifest_hash = Column(String(64), nullable=False)
    status = Column(String(24), nullable=False)
    frozen_hash = Column(String(64))
    training = Column(JSON)
    sensitivity = Column(JSON)
    holdout = Column(JSON)
    error = Column(Text)
    history = Column(JSON, nullable=False)
    created_at = Column(String(40), default=now, nullable=False)
