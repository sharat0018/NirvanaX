from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import (
    get_db, User, Transaction, Investment, ConsentLog,
    GovernanceLog, RecommendationHistory, GovernanceEvent
)
from app.models import (
    UserCreate, UserResponse, TransactionInput,
    ChatMessage, ChatResponse, ProductRecommendation,
    AdvisoryConsoleRequest, AdvisoryConsoleResponse
)
from app.engines.income_engine import IncomeEngine
from app.engines.stress_score import StressScoreEngine
from app.engines.emergency_radar import EmergencyRadar
from app.engines.spend_analyzer import SpendAnalyzer
from app.services.recommendation import RecommendationEngine
from app.services.ollama_service import OllamaService
from app.services.indian_stock_api import GrowwAPIService
from app.services.multi_agent_system import orchestrate_institutional_advisory
from app.security import validate_user_prompt, validate_ai_response, audit_and_revise_response, get_sentinel_stats

router = APIRouter()

income_engine = IncomeEngine()
stress_engine = StressScoreEngine()
emergency_radar = EmergencyRadar()
spend_analyzer = SpendAnalyzer()
recommendation_engine = RecommendationEngine()
ollama_service = OllamaService()
indian_stock_service = GrowwAPIService()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_user_financial_context(user_id: int, db: Session) -> dict:
    """Build financial context from DB transactions."""
    transactions = db.query(Transaction).filter(Transaction.user_id == user_id).all()
    income_txns = [t for t in transactions if t.amount > 0]
    expense_txns = [t for t in transactions if t.amount < 0]
    monthly_income = sum(t.amount for t in income_txns) / max(len(income_txns), 1) if income_txns else 0
    monthly_expenses = abs(sum(t.amount for t in expense_txns)) / max(len(expense_txns), 1) if expense_txns else 0
    monthly_savings = monthly_income - monthly_expenses
    savings_rate = (monthly_savings / monthly_income * 100) if monthly_income > 0 else 0
    return {
        "transactions": transactions,
        "monthly_income": monthly_income,
        "monthly_expenses": monthly_expenses,
        "monthly_savings": monthly_savings,
        "savings_rate": savings_rate,
    }


def _persist_governance_log(
    db: Session, user_id: int, query: str, intent: str,
    primary_response: str, result: dict, sentinel_issues: list, engine_grounded: bool
):
    """Persist full 5-agent governance log to database."""
    try:
        gov = result["governance"]
        agents = result["agent_deliberation"]
        verdicts = gov["verdicts"]

        log = GovernanceLog(
            user_id=user_id,
            query=query,
            intent=intent,
            primary_response=primary_response,
            coordinator_response=agents["core_coordinator"]["response"],
            market_intelligence_response=agents["market_intelligence"]["response"],
            strategy_architect_response=agents["strategy_architect"]["response"],
            execution_governance_response=agents["execution_governance"]["response"],
            risk_governance_response=agents["risk_governance"]["response"],
            coordinator_verdict=verdicts["coordinator"],
            market_verdict=verdicts["market"],
            strategy_verdict=verdicts["strategy"],
            execution_verdict=verdicts["execution"],
            risk_verdict=verdicts["risk"],
            trust_score=gov["trust_score"],
            risk_level=gov["risk_level"],
            consensus_action=gov["consensus"]["action"],
            consensus_percent=gov["consensus"]["consensus_percent"],
            governance_alerts=gov["alerts"],
            bias_flags=[],
            hallucination_incidents=sentinel_issues,
            engine_grounded=engine_grounded,
            execution_ms=result["execution_ms"],
        )
        db.add(log)

        # Log governance events for blocks/high-risk
        if gov["consensus"]["action"] == "BLOCK":
            db.add(GovernanceEvent(
                user_id=user_id,
                event_type="BLOCK",
                severity="HIGH",
                agent_source=verdicts.get("coordinator", "unknown"),
                description=gov["consensus"]["summary"],
                query_preview=query[:100],
            ))
        elif gov["risk_level"] in ["HIGH", "CRITICAL"]:
            db.add(GovernanceEvent(
                user_id=user_id,
                event_type="ALERT",
                severity=gov["risk_level"],
                agent_source="risk_governance",
                description=f"Risk level {gov['risk_level']} detected",
                query_preview=query[:100],
            ))

        db.commit()
        return log.id
    except Exception as e:
        print(f"[Governance log error] {e}")
        return None


# ── Users ─────────────────────────────────────────────────────────────────────

@router.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(email=user.email, name=user.name, phone=user.phone)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ── Transactions ──────────────────────────────────────────────────────────────

@router.post("/transactions/{user_id}")
def add_transactions(user_id: int, transactions: List[TransactionInput], db: Session = Depends(get_db)):
    for txn in transactions:
        db.add(Transaction(
            user_id=user_id, amount=txn.amount, category=txn.category,
            description=txn.description, date=txn.date, merchant=txn.merchant
        ))
    db.commit()
    return {"message": f"Added {len(transactions)} transactions"}


# ── Ground Truth Financial Engines ───────────────────────────────────────────

@router.get("/analysis/income/{user_id}")
def analyze_income(user_id: int, db: Session = Depends(get_db)):
    ctx = _build_user_financial_context(user_id, db)
    txn_data = [{"amount": t.amount, "category": t.category} for t in ctx["transactions"]]
    return income_engine.analyze(txn_data)


@router.get("/analysis/stress/{user_id}")
def analyze_stress(user_id: int, db: Session = Depends(get_db)):
    ctx = _build_user_financial_context(user_id, db)
    user_data = {
        "monthly_income": ctx["monthly_income"], "monthly_expenses": ctx["monthly_expenses"],
        "monthly_savings": ctx["monthly_savings"], "monthly_debt": 0,
        "liquid_balance": 50000, "monthly_expenses_history": [ctx["monthly_expenses"]], "investments": []
    }
    return stress_engine.analyze(user_data)


@router.get("/analysis/emergency/{user_id}")
def analyze_emergency(user_id: int, db: Session = Depends(get_db)):
    ctx = _build_user_financial_context(user_id, db)
    return emergency_radar.analyze({"liquid_balance": 50000, "monthly_expenses": ctx["monthly_expenses"]})


@router.get("/analysis/spending/{user_id}")
def analyze_spending(user_id: int, db: Session = Depends(get_db)):
    ctx = _build_user_financial_context(user_id, db)
    txn_data = [{"amount": t.amount, "description": t.description, "merchant": t.merchant or ""} for t in ctx["transactions"]]
    spending = spend_analyzer.analyze_spending(txn_data)
    return {"spending_analysis": spending, "savings_opportunities": spend_analyzer.detect_savings_opportunities(spending)}


@router.get("/recommendations/{user_id}", response_model=List[ProductRecommendation])
def get_recommendations(user_id: int, db: Session = Depends(get_db)):
    ctx = _build_user_financial_context(user_id, db)
    user_profile = {
        "monthly_income": ctx["monthly_income"], "monthly_expenses": ctx["monthly_expenses"],
        "liquid_balance": 50000, "stress_score": 65, "tax_saving_needed": True
    }
    return recommendation_engine.get_recommendations(user_profile)


@router.get("/languages")
def get_supported_languages():
    return {"languages": [
        {"code": "english", "name": "English", "native_name": "English"},
        {"code": "hindi", "name": "Hindi", "native_name": "हिन्दी"},
        {"code": "tamil", "name": "Tamil", "native_name": "தமிழ்"},
        {"code": "telugu", "name": "Telugu", "native_name": "తెలుగు"},
        {"code": "marathi", "name": "Marathi", "native_name": "मराठी"},
        {"code": "bengali", "name": "Bengali", "native_name": "বাংলা"},
    ]}


# ── NirvanaX Advisory Console (5-Agent Institutional System) ─────────────────

@router.post("/advisory/console")
async def advisory_console(request: AdvisoryConsoleRequest, db: Session = Depends(get_db)):
    """
    NirvanaX Flagship: 5-Agent Institutional Advisory Console
    Flow: Sentinel → Engines → Ollama → 5-Agent Council → Governance Log → Response
    """
    # 1. Sentinel validation
    is_safe, sanitized, threat_type = validate_user_prompt(request.query, request.user_id)
    if not is_safe:
        return {
            "query": request.query,
            "primary_response": f"🛡️ Sentinel blocked: {threat_type}",
            "governance": {"trust_score": 0, "risk_level": "CRITICAL",
                           "consensus": {"action": "BLOCK", "consensus_percent": 0, "summary": f"Sentinel: {threat_type}"},
                           "verdicts": {}, "alerts": [f"Sentinel blocked: {threat_type}"], "engine_grounded": False},
            "agent_deliberation": {},
            "execution_ms": 0,
        }

    # 2. Language detection
    language = request.language or "english"
    if language == "english":
        if any(c in request.query for c in ['ह', 'न', 'क', 'म']): language = "hindi"
        elif any(c in request.query for c in ['த', 'ன', 'க', 'ம']): language = "tamil"
        elif any(c in request.query for c in ['త', 'న', 'క', 'మ']): language = "telugu"

    # 3. Intent classification
    user_query = sanitized.lower()
    KNOWN_STOCKS = ["reliance", "tcs", "hdfc", "infy", "infosys", "icici", "wipro", "sbin",
                    "lt", "ongc", "ntpc", "adani", "tatamotors", "tata", "bajaj", "kotak",
                    "axis", "hul", "maruti", "sunpharma", "zomato", "paytm", "nykaa"]
    intent = "general"
    if any(w in user_query for w in ["spend", "expense", "spending", "budget", "bills"]):
        intent = "spending_analysis"
    elif any(w in user_query for w in ["nifty", "sensex", "market index", "indices"]):
        intent = "stock_query"
    elif any(w in user_query for w in ["mutual fund", "mf", "sip", "elss", "fund"]):
        intent = "mutual_fund_query"
    elif any(s in user_query for s in KNOWN_STOCKS):
        intent = "stock_query"
    elif any(w in user_query for w in ["invest", "portfolio", "recommend", "suggest", "stock", "equity"]):
        intent = "investment_recommendation"
    elif any(w in user_query for w in ["emergency", "savings", "save"]):
        intent = "emergency_fund"
    elif any(w in user_query for w in ["stress", "financial health", "score"]):
        intent = "financial_health"

    # 4. Load financial context + run engines
    ctx = _build_user_financial_context(request.user_id, db)
    context = {"user_id": request.user_id, "language": language, "intent": intent}
    engine_grounded = False

    if intent == "spending_analysis":
        txn_data = [{"amount": t.amount, "description": t.description, "merchant": t.merchant or ""} for t in ctx["transactions"]]
        spending = spend_analyzer.analyze_spending(txn_data)
        context["spending_data"] = {"monthly_expenses": ctx["monthly_expenses"],
                                     "spending_breakdown": spending,
                                     "savings_opportunities": spend_analyzer.detect_savings_opportunities(spending)}
        engine_grounded = True

    elif intent == "stock_query":
        try:
            stop_words = ['tell', 'me', 'about', 'show', 'stock', 'price', 'share', 'the', 'how', 'is']
            words = [w for w in user_query.split() if w not in stop_words]
            specific_stocks = []
            if words:
                symbol = await indian_stock_service.search_stock_symbol(' '.join(words))
                if symbol:
                    stock_data = await indian_stock_service.get_stock_quote(symbol)
                    if stock_data:
                        specific_stocks.append(stock_data)
            context["market_data"] = {
                "specific_stocks": specific_stocks or None,
                "trending_stocks": (await indian_stock_service.get_trending_stocks())[:10],
                "market_indices": await indian_stock_service.get_market_indices(),
            }
        except Exception as e:
            print(f"[Market data] {e}")

    elif intent == "mutual_fund_query":
        try:
            context["mutual_funds"] = await indian_stock_service.get_mutual_funds()
        except Exception as e:
            print(f"[MF data] {e}")

    elif intent in ["investment_recommendation", "financial_health", "emergency_fund"]:
        user_data = {
            "monthly_income": ctx["monthly_income"], "monthly_expenses": ctx["monthly_expenses"],
            "monthly_savings": ctx["monthly_savings"], "monthly_debt": 0,
            "liquid_balance": 50000, "monthly_expenses_history": [ctx["monthly_expenses"]], "investments": []
        }
        stress_analysis = stress_engine.analyze(user_data)
        emergency_analysis = emergency_radar.analyze(user_data)
        context["financial_profile"] = {
            "monthly_income": ctx["monthly_income"], "monthly_expenses": ctx["monthly_expenses"],
            "savings_rate": round(ctx["savings_rate"], 1), "stress_score": stress_analysis["score"],
            "emergency_status": "adequate" if emergency_analysis["emergency_status"]["adequate"] else "inadequate",
        }
        if intent == "investment_recommendation":
            recs = recommendation_engine.get_recommendations({
                "monthly_income": ctx["monthly_income"], "monthly_expenses": ctx["monthly_expenses"],
                "liquid_balance": 50000, "stress_score": stress_analysis["score"], "tax_saving_needed": True
            })
            context["recommendations"] = [
                {"product_name": r["product_name"], "product_type": r["product_type"],
                 "suitability_score": r["suitability_score"], "risk_level": r["risk_level"],
                 "min_investment": r["min_investment"]} for r in recs[:3]
            ]
        engine_grounded = True

    # 5. Generate primary response via Ollama
    primary_response = await ollama_service.generate_response(sanitized, context)

    # 6. LLM Auditor: Critic → Reviser pipeline (Google ADK-inspired)
    # Verifies every factual claim, fixes inaccuracies, cross-validates with engines
    engine_data = context.get("financial_profile") or context.get("stress_data")
    audit_result = await audit_and_revise_response(
        question=sanitized,
        ai_response=primary_response,
        engine_data=engine_data,
    )
    # Use the verified+revised response going forward
    primary_response = audit_result["final_response"]
    sentinel_check = {
        "issues": audit_result["engine_contradictions"],
        "was_revised": audit_result["was_revised"],
        "overall_verdict": audit_result["overall_verdict"],
        "hallucination_risk": audit_result["hallucination_risk"],
        "claims_verified": len(audit_result["claims"]),
        "audit_latency_ms": audit_result["audit_latency_ms"],
    }

    # 7. 5-Agent institutional advisory deliberation
    advisory_result = await orchestrate_institutional_advisory(
        user_query=sanitized,
        primary_response=primary_response,
        context=context,
        engine_grounded=engine_grounded,
    )

    # 8. Persist governance log
    _persist_governance_log(
        db, request.user_id, request.query, intent,
        primary_response, advisory_result, sentinel_check.get("issues", []), engine_grounded
    )

    # 9. Block if governance says BLOCK
    if advisory_result["governance"]["consensus"]["action"] == "BLOCK":
        primary_response = (
            "🛡️ NirvanaX Governance Council blocked this recommendation. "
            "One or more agents flagged a critical issue. "
            "Please consult a certified financial advisor."
        )

    # 10. Build recommendations
    recommendations = None
    if intent == "investment_recommendation":
        try:
            recommendations = recommendation_engine.get_recommendations({
                "monthly_income": ctx["monthly_income"], "monthly_expenses": ctx["monthly_expenses"],
                "liquid_balance": 50000,
                "stress_score": context.get("financial_profile", {}).get("stress_score", 65),
                "tax_saving_needed": True
            })
        except Exception as e:
            print(f"[Reco error] {e}")

    # 11. Build execution plan
    execution_plan = None
    exec_verdict = advisory_result["governance"]["verdicts"].get("execution", "")
    if exec_verdict in ["EXECUTE_NOW", "SCALE_IN"] and recommendations:
        execution_plan = {
            "action": exec_verdict,
            "timing": "Immediate" if exec_verdict == "EXECUTE_NOW" else "Gradual scale-in over 3 months",
            "top_product": recommendations[0]["product_name"] if recommendations else None,
            "suggested_allocation": f"₹{min(ctx['monthly_savings'] * 0.3, 5000):,.0f}/month",
            "rebalance_trigger": "Quarterly or when allocation drifts >5%",
        }

    # 12. Alternative strategies
    alt_strategies = [
        "Consider SIP in index funds for lower cost exposure",
        "Build emergency fund to 6 months before equity allocation",
        "Explore NPS for additional tax benefits under 80CCD",
    ] if advisory_result["governance"]["trust_score"] < 70 else None

    return {
        "query": request.query,
        "primary_response": primary_response,
        "governance": advisory_result["governance"],
        "agent_deliberation": advisory_result["agent_deliberation"],
        "recommendations": [r.__dict__ if hasattr(r, '__dict__') else r for r in (recommendations or [])],
        "execution_plan": execution_plan,
        "alternative_strategies": alt_strategies,
        "execution_ms": advisory_result["execution_ms"],
    }


# ── Legacy chat endpoint (backward compatible) ────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage, db: Session = Depends(get_db)):
    """Legacy chat endpoint — routes to advisory console internally."""
    result = await advisory_console(
        AdvisoryConsoleRequest(
            query=message.message,
            user_id=message.user_id,
            language=message.language,
        ),
        db=db,
    )
    return ChatResponse(
        response=result.get("primary_response", ""),
        recommendations=result.get("recommendations"),
        governance=result.get("governance"),
        agent_deliberation=result.get("agent_deliberation"),
    )


# ── Market Data ───────────────────────────────────────────────────────────────

@router.get("/market/mutual-funds")
async def get_mutual_funds(category: str = None):
    return {"data": await indian_stock_service.get_mutual_funds(category)}


@router.get("/market/indices")
async def get_market_indices():
    return {"data": await indian_stock_service.get_market_indices()}


@router.get("/market/trending")
async def get_trending_stocks():
    return {"data": await indian_stock_service.get_trending_stocks()}


@router.get("/market/nse-active")
async def get_nse_active():
    return {"data": await indian_stock_service.get_nse_most_active()}


# ── Investments ───────────────────────────────────────────────────────────────

@router.post("/investments/{user_id}")
def create_investment(user_id: int, product_name: str, amount: float,
                      product_type: str = "MUTUAL_FUND", db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    ctx = _build_user_financial_context(user_id, db)
    emergency_analysis = emergency_radar.analyze({"liquid_balance": 50000, "monthly_expenses": ctx["monthly_expenses"]})
    if not emergency_analysis["emergency_status"]["adequate"] and product_type in ["EQUITY", "MUTUAL_FUND"]:
        raise HTTPException(status_code=400,
            detail="Investment blocked by NirvanaX Emergency Radar: Build emergency fund first")
    db.add(ConsentLog(user_id=user_id, consent_type="INVESTMENT", consent_given=True,
                      consent_metadata={"product": product_name, "amount": amount, "product_type": product_type}))
    investment = Investment(user_id=user_id, product_type=product_type,
                            product_name=product_name, amount=amount, status="PENDING_BANK_APPROVAL")
    db.add(investment)
    db.commit()
    db.refresh(investment)
    return {
        "message": "Investment order created",
        "order_id": f"NVX-{investment.id}",
        "status": "PENDING_BANK_APPROVAL",
        "next_steps": ["Bank will verify balance", "Payment gateway processes UPI/Net Banking",
                       "Fund house allocates units", "Confirmation via email/SMS"],
        "estimated_processing_time": "2-3 business days"
    }


@router.get("/investments/{user_id}")
def get_investments(user_id: int, db: Session = Depends(get_db)):
    investments = db.query(Investment).filter(Investment.user_id == user_id).all()
    return {"investments": [
        {"id": inv.id, "order_id": f"NVX-{inv.id}", "product_type": inv.product_type,
         "product_name": inv.product_name, "amount": inv.amount, "status": inv.status,
         "created_at": inv.created_at.isoformat() if inv.created_at else None}
        for inv in investments
    ]}


@router.post("/investments/order/{investment_id}/simulate-bank")
def simulate_bank_response(investment_id: int, approved: bool = True, db: Session = Depends(get_db)):
    investment = db.query(Investment).filter(Investment.id == investment_id).first()
    if not investment:
        raise HTTPException(status_code=404, detail="Investment not found")
    investment.status = "COMPLETED" if approved else "REJECTED"
    db.commit()
    return {"order_id": f"NVX-{investment.id}", "status": investment.status}


# ── Governance & Security Endpoints ──────────────────────────────────────────

@router.get("/security/firewall-stats")
def get_security_stats():
    return get_sentinel_stats()


@router.get("/governance/logs/{user_id}")
def get_governance_logs(user_id: int, limit: int = 20, db: Session = Depends(get_db)):
    logs = (db.query(GovernanceLog).filter(GovernanceLog.user_id == user_id)
            .order_by(GovernanceLog.timestamp.desc()).limit(limit).all())
    return {"governance_logs": [
        {
            "id": log.id, "query": log.query, "intent": log.intent,
            "trust_score": log.trust_score, "risk_level": log.risk_level,
            "consensus_action": log.consensus_action, "consensus_percent": log.consensus_percent,
            "verdicts": {
                "coordinator": log.coordinator_verdict, "market": log.market_verdict,
                "strategy": log.strategy_verdict, "execution": log.execution_verdict,
                "risk": log.risk_verdict,
            },
            "alerts": log.governance_alerts, "engine_grounded": log.engine_grounded,
            "execution_ms": log.execution_ms,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
        }
        for log in logs
    ]}


@router.get("/governance/stats")
def get_governance_stats(db: Session = Depends(get_db)):
    total = db.query(GovernanceLog).count()
    blocked = db.query(GovernanceLog).filter(GovernanceLog.consensus_action == "BLOCK").count()
    approved = db.query(GovernanceLog).filter(GovernanceLog.consensus_action == "APPROVE").count()
    caution = db.query(GovernanceLog).filter(GovernanceLog.consensus_action == "APPROVE_WITH_CAUTION").count()
    avg_trust_rows = db.query(GovernanceLog.trust_score).all()
    avg_trust = round(sum(r[0] for r in avg_trust_rows) / len(avg_trust_rows), 1) if avg_trust_rows else 0
    events = db.query(GovernanceEvent).order_by(GovernanceEvent.timestamp.desc()).limit(10).all()
    return {
        "platform": "NirvanaX",
        "total_governed_queries": total,
        "approved": approved,
        "approved_with_caution": caution,
        "blocked": blocked,
        "average_trust_score": avg_trust,
        "recent_events": [
            {"type": e.event_type, "severity": e.severity, "description": e.description,
             "timestamp": e.timestamp.isoformat() if e.timestamp else None}
            for e in events
        ],
        "sentinel_stats": get_sentinel_stats(),
        "audit_pipeline": "LLM Auditor (Critic→Reviser) + Engine Cross-Validation",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/governance/events/{user_id}")
def get_governance_events(user_id: int, limit: int = 20, db: Session = Depends(get_db)):
    events = (db.query(GovernanceEvent).filter(GovernanceEvent.user_id == user_id)
              .order_by(GovernanceEvent.timestamp.desc()).limit(limit).all())
    return {"events": [
        {"id": e.id, "type": e.event_type, "severity": e.severity, "agent": e.agent_source,
         "description": e.description, "query_preview": e.query_preview, "resolved": e.resolved,
         "timestamp": e.timestamp.isoformat() if e.timestamp else None}
        for e in events
    ]}


# ══════════════════════════════════════════════════════════════════════════════
# NIRVANAX — Google ADK Financial Advisor Endpoints
# 4-Step Institutional Advisory Workflow
# ══════════════════════════════════════════════════════════════════════════════

from app.services.financial_coordinator import (
    process_coordinator_message,
    get_session_state,
    clear_session,
)
from app.services.data_analyst_agent import run_data_analyst
from app.services.trading_analyst_agent import run_trading_analyst
from app.services.execution_agent import run_execution_agent
from app.services.risk_evaluation_agent import run_risk_evaluation
from pydantic import BaseModel as PydanticBase


class AdvisorChatRequest(PydanticBase):
    message: str
    user_id: int = 1
    language: Optional[str] = "english"


class DataAnalystRequest(PydanticBase):
    ticker: str
    user_id: int = 1
    timeframe_days: int = 7


class TradingAnalystRequest(PydanticBase):
    ticker: str
    market_analysis: str
    risk_tolerance: str = "moderate"
    investment_duration: str = "long-term"
    user_id: int = 1


class ExecutionRequest(PydanticBase):
    ticker: str
    selected_strategy: str
    market_analysis: str
    risk_tolerance: str = "moderate"
    investment_duration: str = "long-term"
    execution_preferences: Optional[str] = None
    user_id: int = 1


class RiskEvalRequest(PydanticBase):
    ticker: str
    trading_strategies: str
    execution_plan: str
    market_analysis: str
    risk_tolerance: str = "moderate"
    investment_duration: str = "long-term"
    user_id: int = 1


@router.post("/advisor/chat")
async def financial_advisor_chat(request: AdvisorChatRequest, db: Session = Depends(get_db)):
    """
    NirvanaX Financial Advisor — Conversational 4-step workflow.
    Inspired by Google ADK Financial Advisor architecture.
    Step 1: Data Analyst → Step 2: Trading Analyst → Step 3: Execution → Step 4: Risk Evaluation
    """
    # Build user profile from engines if available
    user_profile = None
    try:
        ctx = _build_user_financial_context(request.user_id, db)
        if ctx["monthly_income"] > 0:
            user_data = {
                "monthly_income": ctx["monthly_income"],
                "monthly_expenses": ctx["monthly_expenses"],
                "monthly_savings": ctx["monthly_savings"],
                "monthly_debt": 0,
                "liquid_balance": 50000,
                "monthly_expenses_history": [ctx["monthly_expenses"]],
                "investments": [],
            }
            stress = stress_engine.analyze(user_data)
            emergency = emergency_radar.analyze(user_data)
            user_profile = {
                "monthly_income": ctx["monthly_income"],
                "monthly_expenses": ctx["monthly_expenses"],
                "savings_rate": round(ctx["savings_rate"], 1),
                "stress_score": stress["score"],
                "emergency_status": "adequate" if emergency["emergency_status"]["adequate"] else "inadequate",
            }
    except Exception as e:
        print(f"[Advisor profile] {e}")

    result = await process_coordinator_message(
        user_id=request.user_id,
        message=request.message,
        user_profile=user_profile,
    )

    return {
        "response": result["response"],
        "step": result["step"],
        "session_state": {
            "ticker": result["session"].get("ticker"),
            "risk_tolerance": result["session"].get("risk_tolerance"),
            "investment_duration": result["session"].get("investment_duration"),
            "step": result["step"],
        },
        "agent_output": result.get("agent_output"),
        "show_analysis": result.get("show_analysis", False),
        "show_strategies": result.get("show_strategies", False),
        "show_execution": result.get("show_execution", False),
        "show_risk": result.get("show_risk", False),
        "final_recommendation": result.get("final_recommendation"),
    }


@router.get("/advisor/session/{user_id}")
def get_advisor_session(user_id: int):
    """Get current advisor session state for a user."""
    session = get_session_state(user_id)
    return {
        "user_id": user_id,
        "step": session["step"],
        "ticker": session.get("ticker"),
        "risk_tolerance": session.get("risk_tolerance"),
        "investment_duration": session.get("investment_duration"),
        "has_analysis": session.get("market_analysis") is not None,
        "has_strategies": session.get("trading_strategies") is not None,
        "has_execution": session.get("execution_plan") is not None,
        "has_risk_eval": session.get("risk_evaluation") is not None,
        "final_recommendation": session.get("final_recommendation"),
        "created_at": session.get("created_at"),
    }


@router.delete("/advisor/session/{user_id}")
def reset_advisor_session(user_id: int):
    """Reset advisor session for a user."""
    clear_session(user_id)
    return {"message": f"Session reset for user {user_id}"}


@router.post("/advisor/data-analyst")
async def run_data_analyst_endpoint(request: DataAnalystRequest, db: Session = Depends(get_db)):
    """Run Data Analyst Agent directly for a ticker."""
    try:
        live_data = await indian_stock_service.get_stock_quote(request.ticker)
        historical = await indian_stock_service.get_historical_data(request.ticker, days=30)
    except Exception:
        live_data = None
        historical = []

    result = await run_data_analyst(
        ticker=request.ticker,
        live_market_data=live_data,
        historical_data=historical,
        timeframe_days=request.timeframe_days,
    )
    return result


@router.post("/advisor/trading-analyst")
async def run_trading_analyst_endpoint(request: TradingAnalystRequest, db: Session = Depends(get_db)):
    """Run Trading Analyst Agent directly."""
    ctx = _build_user_financial_context(request.user_id, db)
    user_profile = {
        "monthly_income": ctx["monthly_income"],
        "monthly_expenses": ctx["monthly_expenses"],
        "savings_rate": round(ctx["savings_rate"], 1),
    } if ctx["monthly_income"] > 0 else None

    return await run_trading_analyst(
        ticker=request.ticker,
        market_analysis_report=request.market_analysis,
        risk_tolerance=request.risk_tolerance,
        investment_duration=request.investment_duration,
        user_profile=user_profile,
    )


@router.post("/advisor/execution")
async def run_execution_endpoint(request: ExecutionRequest):
    """Run Execution Agent directly."""
    live_price = None
    try:
        quote = await indian_stock_service.get_stock_quote(request.ticker)
        if quote:
            live_price = quote.get("price")
    except Exception:
        pass

    return await run_execution_agent(
        ticker=request.ticker,
        selected_strategy=request.selected_strategy,
        market_analysis=request.market_analysis,
        risk_tolerance=request.risk_tolerance,
        investment_duration=request.investment_duration,
        execution_preferences=request.execution_preferences,
        live_price=live_price,
    )


@router.post("/advisor/risk-evaluation")
async def run_risk_evaluation_endpoint(request: RiskEvalRequest, db: Session = Depends(get_db)):
    """Run Risk Evaluation Agent directly."""
    ctx = _build_user_financial_context(request.user_id, db)
    user_profile = {
        "monthly_income": ctx["monthly_income"],
        "monthly_expenses": ctx["monthly_expenses"],
        "savings_rate": round(ctx["savings_rate"], 1),
    } if ctx["monthly_income"] > 0 else None

    return await run_risk_evaluation(
        ticker=request.ticker,
        trading_strategies=request.trading_strategies,
        execution_plan=request.execution_plan,
        market_analysis=request.market_analysis,
        risk_tolerance=request.risk_tolerance,
        investment_duration=request.investment_duration,
        user_profile=user_profile,
    )
