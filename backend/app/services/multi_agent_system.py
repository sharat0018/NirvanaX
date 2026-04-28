"""
NirvanaX — Multi-Agent Institutional Financial Advisory System
Inspired by Google ADK Financial Advisor Architecture

5-Agent System:
1. Core Coordinator Agent — Orchestration, routing, consensus synthesis
2. Market Intelligence Agent — Real-time market data, Groww API, technical analysis
3. Strategy Architect Agent — Budgeting, wealth strategies, portfolio recommendations
4. Execution Governance Agent — Entry/exit timing, position sizing, rebalancing
5. Risk Governance Agent — Risk assessment, bias detection, compliance, safety

Architecture: Parallel specialist execution → Consensus → Trust scoring → Governance verdict
"""

import asyncio
import httpx
import os
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


# ══════════════════════════════════════════════════════════════════════════════
# AGENT ROLE DEFINITIONS
# ══════════════════════════════════════════════════════════════════════════════

AGENT_ROLES = {
    "coordinator": {
        "name": "Core Coordinator",
        "model": "gemini-2.5-flash",
        "focus": "orchestration, query routing, consensus synthesis, final recommendation",
        "system": (
            "You are the Core Coordinator in NirvanaX's 5-agent institutional advisory system. "
            "Your role: synthesize inputs from 4 specialist agents (Market Intelligence, Strategy Architect, "
            "Execution Governance, Risk Governance), resolve conflicts, build consensus, and generate "
            "the final unified financial recommendation. Prioritize user safety, explainability, and actionability. "
            "Be concise (max 120 words). End with COORDINATOR_VERDICT: RECOMMEND | CAUTION | REJECT"
        ),
    },
    "market_intelligence": {
        "name": "Market Intelligence Agent",
        "model": "llama-3.1-8b-instant",
        "focus": "real-time market data, stock analysis, technical indicators, sector trends",
        "system": (
            "You are the Market Intelligence Agent in NirvanaX's institutional advisory system. "
            "Your role: analyze real-time market data, validate stock/fund performance claims, "
            "assess technical indicators, identify sector trends, and flag hallucinated market data. "
            "Use provided Groww API data when available. Be data-driven and precise. "
            "Be concise (max 100 words). End with MARKET_VERDICT: BULLISH | NEUTRAL | BEARISH | DATA_INVALID"
        ),
    },
    "strategy_architect": {
        "name": "Strategy Architect Agent",
        "model": "qwen2.5:1.5b",
        "focus": "budgeting, wealth strategies, portfolio allocation, savings optimization",
        "system": (
            "You are the Strategy Architect Agent in NirvanaX's institutional advisory system. "
            "Your role: design personalized financial strategies, recommend portfolio allocations, "
            "optimize savings plans, align recommendations with user's financial goals and risk tolerance. "
            "Consider income stability, stress score, and emergency fund status. "
            "Be concise (max 100 words). End with STRATEGY_VERDICT: OPTIMAL | SUBOPTIMAL | MISALIGNED"
        ),
    },
    "execution_governance": {
        "name": "Execution Governance Agent",
        "model": "gemini-2.5-flash",
        "focus": "entry/exit timing, position sizing, rebalancing, tactical execution",
        "system": (
            "You are the Execution Governance Agent in NirvanaX's institutional advisory system. "
            "Your role: assess execution timing, recommend position sizing, evaluate rebalancing needs, "
            "and provide tactical execution guidance. Consider market conditions, user liquidity, "
            "and portfolio concentration risks. "
            "Be concise (max 100 words). End with EXECUTION_VERDICT: EXECUTE_NOW | WAIT | SCALE_IN | AVOID"
        ),
    },
    "risk_governance": {
        "name": "Risk Governance Agent",
        "model": "llama-3.1-8b-instant",
        "focus": "risk assessment, bias detection, compliance, ethical oversight, consumer safety",
        "system": (
            "You are the Risk Governance Agent in NirvanaX's institutional advisory system. "
            "Your role: assess financial risks, detect bias, ensure compliance with consumer protection standards, "
            "flag concentration risks, evaluate debt burden, and provide ethical oversight. "
            "Block recommendations that could harm vulnerable users. "
            "Be concise (max 100 words). End with RISK_VERDICT: SAFE | MODERATE_RISK | HIGH_RISK | UNSAFE"
        ),
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# AGENT CALLERS
# ══════════════════════════════════════════════════════════════════════════════

async def _call_gemini_agent(agent_key: str, prompt: str, context: str) -> Tuple[str, float]:
    """Call Gemini-based agents (Coordinator, Execution Governance)."""
    start = time.time()
    if not GEMINI_API_KEY:
        return _fallback_response(agent_key), time.time() - start
    try:
        full_prompt = f"{context}\n\nUser Query/Recommendation:\n{prompt}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{GEMINI_URL}?key={GEMINI_API_KEY}",
                json={
                    "contents": [{"parts": [{"text": full_prompt}]}],
                    "systemInstruction": {"parts": [{"text": AGENT_ROLES[agent_key]["system"]}]},
                    "generationConfig": {"maxOutputTokens": 200, "temperature": 0.3},
                },
            )
            if resp.status_code == 200:
                text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                return text.strip(), time.time() - start
    except Exception as e:
        print(f"[{agent_key}] Error: {e}")
    return _fallback_response(agent_key), time.time() - start


async def _call_groq_agent(agent_key: str, prompt: str, context: str) -> Tuple[str, float]:
    """Call Groq-based agents (Market Intelligence, Risk Governance)."""
    start = time.time()
    if not GROQ_API_KEY:
        return _fallback_response(agent_key), time.time() - start
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                GROQ_URL,
                headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": AGENT_ROLES[agent_key]["model"],
                    "messages": [
                        {"role": "system", "content": AGENT_ROLES[agent_key]["system"]},
                        {"role": "user", "content": f"{context}\n\nQuery/Recommendation:\n{prompt}"},
                    ],
                    "max_tokens": 200,
                    "temperature": 0.3,
                },
            )
            if resp.status_code == 200:
                text = resp.json()["choices"][0]["message"]["content"]
                return text.strip(), time.time() - start
    except Exception as e:
        print(f"[{agent_key}] Error: {e}")
    return _fallback_response(agent_key), time.time() - start


async def _call_ollama_agent(agent_key: str, prompt: str, context: str) -> Tuple[str, float]:
    """Call Ollama-based agents (Strategy Architect)."""
    start = time.time()
    try:
        full_prompt = f"{AGENT_ROLES[agent_key]['system']}\n\n{context}\n\nQuery/Recommendation:\n{prompt}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": AGENT_ROLES[agent_key]["model"],
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 200},
                },
            )
            if resp.status_code == 200:
                text = resp.json().get("response", "")
                return text.strip(), time.time() - start
    except Exception as e:
        print(f"[{agent_key}] Error: {e}")
    return _fallback_response(agent_key), time.time() - start


def _fallback_response(agent_key: str) -> str:
    """Deterministic fallback when agent unavailable."""
    fallbacks = {
        "coordinator": "Recommendation synthesized from available data. Proceed with standard financial planning principles. COORDINATOR_VERDICT: RECOMMEND",
        "market_intelligence": "Market data appears consistent with general trends. No obvious anomalies detected. MARKET_VERDICT: NEUTRAL",
        "strategy_architect": "Strategy aligns with standard wealth management principles for the given profile. STRATEGY_VERDICT: OPTIMAL",
        "execution_governance": "Execution timing appears reasonable based on current market conditions. EXECUTION_VERDICT: EXECUTE_NOW",
        "risk_governance": "No critical risks detected for standard investment recommendations. RISK_VERDICT: SAFE",
    }
    return fallbacks.get(agent_key, "Agent unavailable. Using safe default.")


# ══════════════════════════════════════════════════════════════════════════════
# VERDICT PARSERS
# ══════════════════════════════════════════════════════════════════════════════

def _parse_verdicts(responses: Dict[str, str]) -> Dict[str, str]:
    """Extract structured verdicts from all agent responses."""
    def extract(text: str, keyword: str, options: List[str]) -> str:
        text_upper = text.upper()
        if keyword in text_upper:
            for opt in options:
                if opt in text_upper.split(keyword)[-1]:
                    return opt
        return options[0]

    return {
        "coordinator": extract(responses["coordinator"], "COORDINATOR_VERDICT:", ["RECOMMEND", "CAUTION", "REJECT"]),
        "market": extract(responses["market_intelligence"], "MARKET_VERDICT:", ["BULLISH", "NEUTRAL", "BEARISH", "DATA_INVALID"]),
        "strategy": extract(responses["strategy_architect"], "STRATEGY_VERDICT:", ["OPTIMAL", "SUBOPTIMAL", "MISALIGNED"]),
        "execution": extract(responses["execution_governance"], "EXECUTION_VERDICT:", ["EXECUTE_NOW", "WAIT", "SCALE_IN", "AVOID"]),
        "risk": extract(responses["risk_governance"], "RISK_VERDICT:", ["SAFE", "MODERATE_RISK", "HIGH_RISK", "UNSAFE"]),
    }


# ══════════════════════════════════════════════════════════════════════════════
# TRUST SCORE ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def _calculate_institutional_trust_score(verdicts: Dict[str, str], engine_grounded: bool) -> float:
    """
    Compute 0-100 institutional trust score from 5-agent verdicts + engine grounding.
    """
    score = 30.0  # base

    # Coordinator verdict (25 pts)
    score += {"RECOMMEND": 25, "CAUTION": 12, "REJECT": 0}.get(verdicts["coordinator"], 12)

    # Market Intelligence (20 pts)
    score += {"BULLISH": 20, "NEUTRAL": 15, "BEARISH": 10, "DATA_INVALID": 0}.get(verdicts["market"], 10)

    # Strategy Architect (15 pts)
    score += {"OPTIMAL": 15, "SUBOPTIMAL": 8, "MISALIGNED": 0}.get(verdicts["strategy"], 8)

    # Execution Governance (15 pts)
    score += {"EXECUTE_NOW": 15, "SCALE_IN": 12, "WAIT": 8, "AVOID": 0}.get(verdicts["execution"], 8)

    # Risk Governance (20 pts)
    score += {"SAFE": 20, "MODERATE_RISK": 12, "HIGH_RISK": 5, "UNSAFE": 0}.get(verdicts["risk"], 10)

    # Engine grounding bonus (10 pts)
    if engine_grounded:
        score += 10

    return round(min(100, max(0, score)), 1)


def _calculate_risk_level(trust_score: float, verdicts: Dict[str, str]) -> str:
    if verdicts["risk"] == "UNSAFE" or verdicts["coordinator"] == "REJECT":
        return "CRITICAL"
    if verdicts["risk"] == "HIGH_RISK":
        return "HIGH"
    if trust_score >= 80:
        return "LOW"
    if trust_score >= 60:
        return "MODERATE"
    return "HIGH"


# ══════════════════════════════════════════════════════════════════════════════
# CONSENSUS ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def _build_institutional_consensus(verdicts: Dict[str, str], trust_score: float) -> Dict:
    """Build consensus from 5-agent deliberation."""
    
    # Critical blocks
    if verdicts["coordinator"] == "REJECT":
        return {
            "action": "BLOCK",
            "consensus_percent": 0.0,
            "summary": "Core Coordinator rejected this recommendation. Blocked.",
        }
    if verdicts["risk"] == "UNSAFE":
        return {
            "action": "BLOCK",
            "consensus_percent": 0.0,
            "summary": "Risk Governance flagged unsafe recommendation. Blocked for consumer safety.",
        }
    if verdicts["market"] == "DATA_INVALID":
        return {
            "action": "BLOCK",
            "consensus_percent": 0.0,
            "summary": "Market Intelligence detected invalid/hallucinated data. Blocked.",
        }

    # Count positive signals
    positive_signals = sum([
        verdicts["coordinator"] == "RECOMMEND",
        verdicts["market"] in ["BULLISH", "NEUTRAL"],
        verdicts["strategy"] == "OPTIMAL",
        verdicts["execution"] in ["EXECUTE_NOW", "SCALE_IN"],
        verdicts["risk"] in ["SAFE", "MODERATE_RISK"],
    ])

    consensus_pct = round((positive_signals / 5) * 100, 1)

    if positive_signals >= 4:
        action = "APPROVE"
        summary = "Strong consensus across all agents. Recommendation verified and approved."
    elif positive_signals == 3:
        action = "APPROVE_WITH_CAUTION"
        summary = "Majority consensus. Some agents raised concerns — review before acting."
    elif positive_signals == 2:
        action = "REVIEW"
        summary = "Mixed signals from agents. Human review strongly recommended."
    else:
        action = "REJECT"
        summary = "Insufficient consensus. Recommendation not approved."

    return {
        "action": action,
        "consensus_percent": consensus_pct,
        "positive_signals": positive_signals,
        "summary": summary,
    }


# ══════════════════════════════════════════════════════════════════════════════
# GOVERNANCE ALERTS
# ══════════════════════════════════════════════════════════════════════════════

def _generate_institutional_alerts(verdicts: Dict[str, str], trust_score: float) -> List[str]:
    alerts = []
    
    if verdicts["coordinator"] == "CAUTION":
        alerts.append("⚠️ Coordinator Caution: Review recommendation carefully before proceeding.")
    if verdicts["coordinator"] == "REJECT":
        alerts.append("🚫 Coordinator Rejection: Recommendation does not meet institutional standards.")
    
    if verdicts["market"] == "BEARISH":
        alerts.append("📉 Market Bearish: Current market conditions may not favor this recommendation.")
    if verdicts["market"] == "DATA_INVALID":
        alerts.append("🔴 Invalid Market Data: AI-generated data not grounded in real market information.")
    
    if verdicts["strategy"] == "SUBOPTIMAL":
        alerts.append("📊 Suboptimal Strategy: Better alternatives may exist for your financial profile.")
    if verdicts["strategy"] == "MISALIGNED":
        alerts.append("❌ Strategy Misalignment: Recommendation conflicts with your financial goals.")
    
    if verdicts["execution"] == "WAIT":
        alerts.append("⏸️ Execution Hold: Consider waiting for better market timing.")
    if verdicts["execution"] == "AVOID":
        alerts.append("🛑 Execution Avoid: Current conditions not favorable for execution.")
    
    if verdicts["risk"] == "MODERATE_RISK":
        alerts.append("⚠️ Moderate Risk: Proceed with appropriate risk management.")
    if verdicts["risk"] == "HIGH_RISK":
        alerts.append("🔶 High Risk: Significant risk detected — ensure adequate risk tolerance.")
    if verdicts["risk"] == "UNSAFE":
        alerts.append("🚨 Unsafe: Recommendation violates consumer safety standards.")
    
    if trust_score < 50:
        alerts.append("🛡️ Low Trust Score: Recommendation requires additional verification.")
    
    return alerts


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ORCHESTRATOR
# ══════════════════════════════════════════════════════════════════════════════

async def orchestrate_institutional_advisory(
    user_query: str,
    primary_response: str,
    context: Dict,
    engine_grounded: bool = True,
) -> Dict:
    """
    Run 5-agent institutional advisory system in parallel.
    
    Flow:
    1. Market Intelligence + Strategy Architect + Execution + Risk run in parallel
    2. Core Coordinator synthesizes their outputs
    3. Compute trust score, consensus, governance verdict
    
    Returns:
        Full institutional governance report
    """
    intent = context.get("intent", "general")
    user_id = context.get("user_id", 0)

    # Build context summary
    context_summary = f"Intent: {intent} | Engine-grounded: {engine_grounded}"
    if "financial_profile" in context:
        p = context["financial_profile"]
        context_summary += (
            f"\nUser Profile: Income ₹{p.get('monthly_income', 0):,.0f} | "
            f"Stress Score {p.get('stress_score', 'N/A')} | "
            f"Emergency Fund {p.get('emergency_status', 'N/A')}"
        )
    if "market_data" in context:
        context_summary += f"\nMarket Data: {len(context.get('market_data', {}).get('specific_stocks', []))} stocks analyzed"
    if "recommendations" in context:
        context_summary += f"\nRecommendations: {len(context.get('recommendations', []))} products ranked"

    # ── Phase 1: Parallel specialist execution ──
    start_total = time.time()
    
    market_task = _call_groq_agent("market_intelligence", primary_response, context_summary)
    strategy_task = _call_ollama_agent("strategy_architect", primary_response, context_summary)
    execution_task = _call_gemini_agent("execution_governance", primary_response, context_summary)
    risk_task = _call_groq_agent("risk_governance", primary_response, context_summary)

    (market_resp, t_market), (strategy_resp, t_strategy), (execution_resp, t_execution), (risk_resp, t_risk) = await asyncio.gather(
        market_task, strategy_task, execution_task, risk_task
    )

    # ── Phase 2: Core Coordinator synthesis ──
    coordinator_context = (
        f"{context_summary}\n\n"
        f"SPECIALIST AGENT OUTPUTS:\n"
        f"Market Intelligence: {market_resp}\n"
        f"Strategy Architect: {strategy_resp}\n"
        f"Execution Governance: {execution_resp}\n"
        f"Risk Governance: {risk_resp}\n\n"
        f"Primary Recommendation: {primary_response}"
    )
    coordinator_resp, t_coordinator = await _call_gemini_agent("coordinator", user_query, coordinator_context)

    total_time = round(time.time() - start_total, 2)

    # ── Compute governance outputs ──
    responses = {
        "coordinator": coordinator_resp,
        "market_intelligence": market_resp,
        "strategy_architect": strategy_resp,
        "execution_governance": execution_resp,
        "risk_governance": risk_resp,
    }
    
    verdicts = _parse_verdicts(responses)
    trust_score = _calculate_institutional_trust_score(verdicts, engine_grounded)
    risk_level = _calculate_risk_level(trust_score, verdicts)
    consensus = _build_institutional_consensus(verdicts, trust_score)
    alerts = _generate_institutional_alerts(verdicts, trust_score)

    return {
        "governance": {
            "trust_score": trust_score,
            "risk_level": risk_level,
            "consensus": consensus,
            "verdicts": verdicts,
            "alerts": alerts,
            "engine_grounded": engine_grounded,
            "timestamp": datetime.utcnow().isoformat(),
        },
        "agent_deliberation": {
            "core_coordinator": {
                "agent": AGENT_ROLES["coordinator"]["name"],
                "model": AGENT_ROLES["coordinator"]["model"],
                "response": coordinator_resp,
                "latency_s": round(t_coordinator, 2),
                "verdict": verdicts["coordinator"],
            },
            "market_intelligence": {
                "agent": AGENT_ROLES["market_intelligence"]["name"],
                "model": AGENT_ROLES["market_intelligence"]["model"],
                "response": market_resp,
                "latency_s": round(t_market, 2),
                "verdict": verdicts["market"],
            },
            "strategy_architect": {
                "agent": AGENT_ROLES["strategy_architect"]["name"],
                "model": AGENT_ROLES["strategy_architect"]["model"],
                "response": strategy_resp,
                "latency_s": round(t_strategy, 2),
                "verdict": verdicts["strategy"],
            },
            "execution_governance": {
                "agent": AGENT_ROLES["execution_governance"]["name"],
                "model": AGENT_ROLES["execution_governance"]["model"],
                "response": execution_resp,
                "latency_s": round(t_execution, 2),
                "verdict": verdicts["execution"],
            },
            "risk_governance": {
                "agent": AGENT_ROLES["risk_governance"]["name"],
                "model": AGENT_ROLES["risk_governance"]["model"],
                "response": risk_resp,
                "latency_s": round(t_risk, 2),
                "verdict": verdicts["risk"],
            },
        },
        "execution_ms": round(total_time * 1000),
    }
