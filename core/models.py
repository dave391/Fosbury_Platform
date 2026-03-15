from sqlalchemy import Column
from sqlalchemy import Boolean
from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import JSON
from sqlalchemy import String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    exchange_accounts = relationship("ExchangeAccount", back_populates="owner")
    exchange_credentials = relationship("ExchangeCredentials", back_populates="owner")
    strategies = relationship("Strategy", back_populates="owner")


class ExchangeAccount(Base):
    __tablename__ = "exchange_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    exchange_name = Column(String, nullable=False, index=True)
    label = Column(String, nullable=True)
    cached_balance_usdc = Column(Float, nullable=True, default=None)
    balance_updated_at = Column(DateTime(timezone=True), nullable=True, default=None)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    disabled_at = Column(DateTime(timezone=True), nullable=True)

    owner = relationship("User", back_populates="exchange_accounts")
    credentials = relationship("ExchangeCredentials", back_populates="exchange_account")
    strategies = relationship("Strategy", back_populates="exchange_account")


class ExchangeCredentials(Base):
    __tablename__ = "exchange_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    exchange_account_id = Column(Integer, ForeignKey("exchange_accounts.id"), nullable=False, index=True)

    exchange_name = Column(String, default="deribit", nullable=False)

    encrypted_spot_api_key = Column(String, nullable=True)
    encrypted_spot_api_secret = Column(String, nullable=True)

    encrypted_futures_api_key = Column(String, nullable=True)
    encrypted_futures_api_secret = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    disabled_at = Column(DateTime(timezone=True), nullable=True)

    owner = relationship("User", back_populates="exchange_credentials")
    exchange_account = relationship("ExchangeAccount", back_populates="credentials")


class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    exchange_account_id = Column(Integer, ForeignKey("exchange_accounts.id"), nullable=False, index=True)
    asset = Column(String, nullable=False, index=True)
    strategy_key = Column(String, nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, default="ACTIVE", nullable=False)
    config = Column(JSON, nullable=True)
    allocated_capital_usdc = Column(Float, default=0.0, nullable=False)
    total_quantity = Column(Float, default=0.0, nullable=False)
    entry_spot_px = Column(Float, nullable=True)
    entry_perp_px = Column(Float, nullable=True)
    realized_pnl_usdc = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)

    owner = relationship("User", back_populates="strategies")
    exchange_account = relationship("ExchangeAccount", back_populates="strategies")
    positions = relationship("StrategyPosition", back_populates="strategy")
    snapshots = relationship("EquitySnapshot", back_populates="strategy")
    closure = relationship("StrategyClosure", back_populates="strategy", uselist=False)
    decision_logs = relationship("DecisionLog", back_populates="strategy")


class DecisionLog(Base):
    __tablename__ = "decision_log"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False, index=True)
    strategy_key = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    last_seen = Column(DateTime(timezone=True), nullable=False)
    action = Column(String, nullable=False)
    reason = Column(String, nullable=True)
    executed = Column(Boolean, nullable=True)
    execution_error = Column(String, nullable=True)
    price_at_decision = Column(Float, nullable=True)
    liquidation_distance_pct = Column(Float, nullable=True)
    excess_margin = Column(Float, nullable=True)
    metrics_snapshot = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    strategy = relationship("Strategy", back_populates="decision_logs")


class StrategyPosition(Base):
    __tablename__ = "strategy_positions"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False, index=True)
    allocated_capital_usdc = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    entry_spot_px = Column(Float, nullable=True)
    entry_perp_px = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    strategy = relationship("Strategy", back_populates="positions")


class EquitySnapshot(Base):
    __tablename__ = "equity_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False, index=True)
    snapshot_date = Column(Date, nullable=False)
    equity_usdc = Column(Float, nullable=False)
    funding_delta_usdc = Column(Float, nullable=False, default=0.0)
    fees_delta_usdc = Column(Float, nullable=False, default=0.0)
    run_id = Column(String, nullable=True)
    as_of = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    strategy = relationship("Strategy", back_populates="snapshots")


class StrategyClosure(Base):
    __tablename__ = "strategy_closures"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=False)
    starting_capital_usdc = Column(Float, nullable=False)
    final_capital_usdc = Column(Float, nullable=False)
    pnl_usdc = Column(Float, nullable=False)
    apr_percent = Column(Float, nullable=False)
    fees_usdc = Column(Float, nullable=False)
    days_active = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    strategy = relationship("Strategy", back_populates="closure")
