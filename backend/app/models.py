from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


# ── Preserved schemas ─────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    phone: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    phone: str
    class Config:
        from_attributes = True


class TransactionInput(BaseModel):
    amount: float
    category: str
    description: str
    date: datetime
    merchant: Optional[str] = None


class ProductRecommendation(BaseModel):
    product_name: str
    product_type: str
    suitability_score: float
    expected_return: float
    risk_level: str
    min_investment: float
    tax_benefit: bool
    description: str


class ChatMessage(BaseModel):
    message: str
    user_id: int
    language: Optional[str] = "english"


# ── 5-Agent Institutional Advisory Schemas ────────────────────────────────────

class AgentOutput(BaseModel):
    agent: str
    model: str
    response: str
    latency_s: float
    verdict: str


class InstitutionalDeliberation(BaseModel):
    core_coordinator: AgentOutput
    market_intelligence: AgentOutput
    strategy_architect: AgentOutput
    execution_governance: AgentOutput
    risk_governance: AgentOutput


class InstitutionalVerdicts(BaseModel):
    coordinator: str
    market: str
    strategy: str
    execution: str
    risk: str


class ConsensusReport(BaseModel):
    action: str
    consensus_percent: float
    summary: str


class InstitutionalGovernanceReport(BaseModel):
    trust_score: float
    risk_level: str
    consensus: ConsensusReport
    verdicts: InstitutionalVerdicts
    alerts: List[str]
    engine_grounded: bool
    timestamp: str


class AdvisoryConsoleRequest(BaseModel):
    query: str
    user_id: int
    language: Optional[str] = "english"
    advisory_mode: Optional[str] = "full"  # full | quick | market_only | strategy_only


class AdvisoryConsoleResponse(BaseModel):
    query: str
    primary_response: str
    governance: InstitutionalGovernanceReport
    agent_deliberation: InstitutionalDeliberation
    recommendations: Optional[List[ProductRecommendation]] = None
    execution_plan: Optional[Dict[str, Any]] = None
    alternative_strategies: Optional[List[str]] = None
    execution_ms: int


# ── Legacy compatible response (keeps existing frontend working) ──────────────

class ChatResponse(BaseModel):
    response: str
    recommendations: Optional[List[ProductRecommendation]] = None
    action_required: Optional[str] = None
    governance: Optional[Dict[str, Any]] = None
    agent_deliberation: Optional[Dict[str, Any]] = None
