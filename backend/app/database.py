from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/nirvanax.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── Preserved tables ──────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    phone = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    amount = Column(Float)
    category = Column(String)
    description = Column(String)
    date = Column(DateTime)
    merchant = Column(String)


class IncomeStats(Base):
    __tablename__ = "income_stats"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    monthly_income = Column(Float)
    stability_score = Column(Float)
    income_type = Column(String)
    calculated_at = Column(DateTime, default=datetime.utcnow)


class StressScore(Base):
    __tablename__ = "stress_scores"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    score = Column(Float)
    debt_ratio = Column(Float)
    emergency_adequacy = Column(Float)
    savings_rate = Column(Float)
    spending_volatility = Column(Float)
    portfolio_diversification = Column(Float)
    calculated_at = Column(DateTime, default=datetime.utcnow)


class Investment(Base):
    __tablename__ = "investments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    product_type = Column(String)
    product_name = Column(String)
    amount = Column(Float)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class ConsentLog(Base):
    __tablename__ = "consent_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    consent_type = Column(String)
    consent_given = Column(Boolean)
    consent_metadata = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)


# ── Governance Audit Infrastructure ──────────────────────────────────────────

class GovernanceLog(Base):
    """Full 5-agent governance audit trail for every query."""
    __tablename__ = "governance_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    query = Column(Text)
    intent = Column(String)
    primary_response = Column(Text)

    # Agent outputs
    coordinator_response = Column(Text)
    market_intelligence_response = Column(Text)
    strategy_architect_response = Column(Text)
    execution_governance_response = Column(Text)
    risk_governance_response = Column(Text)

    # Verdicts
    coordinator_verdict = Column(String)
    market_verdict = Column(String)
    strategy_verdict = Column(String)
    execution_verdict = Column(String)
    risk_verdict = Column(String)

    # Governance scores
    trust_score = Column(Float)
    risk_level = Column(String)
    consensus_action = Column(String)
    consensus_percent = Column(Float)

    # Audit metadata
    governance_alerts = Column(JSON)
    bias_flags = Column(JSON)
    hallucination_incidents = Column(JSON)
    engine_grounded = Column(Boolean, default=True)
    execution_ms = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)


class RecommendationHistory(Base):
    """Tracks every recommendation made with its governance outcome."""
    __tablename__ = "recommendation_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    governance_log_id = Column(Integer, index=True)
    product_name = Column(String)
    product_type = Column(String)
    suitability_score = Column(Float)
    trust_score = Column(Float)
    risk_level = Column(String)
    consensus_action = Column(String)
    was_executed = Column(Boolean, default=False)
    user_feedback = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)


class GovernanceEvent(Base):
    """Tracks significant governance events: blocks, alerts, bias flags."""
    __tablename__ = "governance_events"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    event_type = Column(String)   # BLOCK | ALERT | BIAS_FLAG | HALLUCINATION | COMPLIANCE
    severity = Column(String)     # LOW | MEDIUM | HIGH | CRITICAL
    agent_source = Column(String)
    description = Column(Text)
    query_preview = Column(String)
    resolved = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


# ── DB lifecycle ──────────────────────────────────────────────────────────────

def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
