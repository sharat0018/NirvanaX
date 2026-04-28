"""
NirvanaX — Financial Coordinator Agent
Inspired by Google ADK Financial Advisor: Coordinator Agent
Role: Guides users through the 4-step institutional advisory workflow.
State Machine: INIT → DATA_ANALYSIS → STRATEGY → EXECUTION → RISK → COMPLETE

Step 1: Data Analyst Agent — market analysis for ticker
Step 2: Trading Analyst Agent — 5+ strategies based on risk/duration
Step 3: Execution Agent — detailed execution plan
Step 4: Risk Evaluation Agent — comprehensive risk assessment
"""

import asyncio
from typing import Dict, Optional, Tuple
from datetime import datetime

from app.services.data_analyst_agent import run_data_analyst
from app.services.trading_analyst_agent import run_trading_analyst
from app.services.execution_agent import run_execution_agent
from app.services.risk_evaluation_agent import run_risk_evaluation
from app.services.indian_stock_api import GrowwAPIService
from app.security import audit_and_revise_response

# ── Session State Store (in-memory, keyed by user_id) ────────────────────────
# In production this would be Redis/DB — for MVP it's in-memory per session
_sessions: Dict[int, Dict] = {}

groww_service = GrowwAPIService()

LEGAL_DISCLAIMER = """
---
> ⚖️ **Legal Disclaimer:** All information provided by NirvanaX Financial Advisor is for **educational and informational purposes only**. It does not constitute financial advice. Always consult a qualified independent financial advisor before making investment decisions. Past performance is not indicative of future results.
"""

INTRO_MESSAGE = """🏛️ **Welcome to NirvanaX Financial Advisor**

I'm your **Financial Coordinator Agent**, backed by a team of 4 specialized AI agents:

| Agent | Role |
|-------|------|
| 📊 **Data Analyst** | In-depth market analysis, SEC/SEBI filings, live data |
| 📈 **Trading Analyst** | 5+ customized trading strategies |
| ⚡ **Execution Agent** | Detailed entry/hold/scale/exit plans |
| 🛡️ **Risk Evaluator** | Comprehensive risk analysis & mitigation |

**How it works:**
1. You provide a stock ticker (e.g., RELIANCE, TCS, INFY)
2. I analyze the market with live Groww API data
3. We develop strategies matched to your risk profile
4. We build an execution plan
5. We evaluate all risks

What stock ticker would you like to analyze today?"""


def _get_session(user_id: int) -> Dict:
    if user_id not in _sessions:
        _sessions[user_id] = {
            "step": "INIT",
            "ticker": None,
            "risk_tolerance": None,
            "investment_duration": None,
            "execution_preferences": None,
            "market_analysis": None,
            "trading_strategies": None,
            "execution_plan": None,
            "risk_evaluation": None,
            "user_profile": None,
            "created_at": datetime.utcnow().isoformat(),
        }
    return _sessions[user_id]


def _reset_session(user_id: int):
    _sessions[user_id] = {
        "step": "INIT",
        "ticker": None,
        "risk_tolerance": None,
        "investment_duration": None,
        "execution_preferences": None,
        "market_analysis": None,
        "trading_strategies": None,
        "execution_plan": None,
        "risk_evaluation": None,
        "user_profile": None,
        "created_at": datetime.utcnow().isoformat(),
    }


def _extract_ticker(text: str) -> Optional[str]:
    """Extract stock ticker from user message — only from KNOWN_TICKERS list."""
    KNOWN_TICKERS = [
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "INFOSYS", "ICICIBANK", "BHARTIARTL",
        "ITC", "WIPRO", "SBIN", "LT", "ONGC", "NTPC", "ADANIENT", "TATAMOTORS",
        "BAJFINANCE", "KOTAKBANK", "AXISBANK", "HCLTECH", "SUNPHARMA", "MARUTI",
        "POWERGRID", "COALINDIA", "IRCTC", "ZOMATO", "PAYTM", "NYKAA", "HDFC",
        "TITAN", "NESTLEIND", "ULTRACEMCO", "ASIANPAINT", "BAJAJFINSV", "TECHM",
        "DIVISLAB", "DRREDDY", "CIPLA", "EICHERMOT", "HEROMOTOCO", "INDUSINDBK",
        "JSWSTEEL", "TATASTEEL", "HINDALCO", "VEDL", "BPCL", "IOC", "GAIL",
        "NIFTY", "SENSEX", "BANKNIFTY",
    ]
    # Words that look like tickers but are common English words — never treat as tickers
    BLACKLIST = {
        "NO", "YES", "OK", "GO", "DO", "IT", "IS", "IN", "ON", "AT", "TO", "UP",
        "OR", "AN", "AS", "BE", "BY", "IF", "OF", "SO", "US", "WE", "MY", "HI",
        "AM", "PM", "ETA", "ETF", "SIP", "EMI", "UPI", "OTP", "PIN", "ATM",
        "NONE", "NULL", "TRUE", "FALSE", "DEFAULT", "PROCEED", "LIMIT", "MARKET",
    }

    text_upper = text.upper().strip()
    words = text_upper.split()

    # First pass: exact match against known tickers only
    for word in words:
        clean = word.strip(".,!?;:()")
        if clean in KNOWN_TICKERS:
            return clean

    # Second pass: single-word messages that look like a ticker (min 5 chars, not blacklisted)
    # Only applies when the entire message is just one word
    if len(words) == 1:
        clean = words[0].strip(".,!?;:()")
        if (5 <= len(clean) <= 12
                and clean.isalpha()
                and clean.isupper()
                and clean not in BLACKLIST):
            return clean

    return None


def _extract_risk_tolerance(text: str) -> Optional[str]:
    text_lower = text.lower()
    if any(w in text_lower for w in ["conservative", "low risk", "safe", "capital preservation"]):
        return "conservative"
    if any(w in text_lower for w in ["aggressive", "high risk", "maximum growth", "speculative"]):
        return "aggressive"
    if any(w in text_lower for w in ["moderate", "medium", "balanced", "medium risk"]):
        return "moderate"
    return None


def _extract_investment_duration(text: str) -> Optional[str]:
    text_lower = text.lower()
    if any(w in text_lower for w in ["short", "short-term", "days", "weeks", "months", "< 3", "less than 3"]):
        return "short-term"
    if any(w in text_lower for w in ["medium", "medium-term", "6 month", "1 year", "3-12"]):
        return "medium-term"
    if any(w in text_lower for w in ["long", "long-term", "years", "retirement", "> 1", "more than 1"]):
        return "long-term"
    return None


async def process_coordinator_message(
    user_id: int,
    message: str,
    user_profile: Optional[Dict] = None,
) -> Dict:
    """
    Main coordinator entry point. Processes user message and advances workflow state.

    Returns:
        Dict with response text, current step, session state, and any agent outputs
    """
    session = _get_session(user_id)
    msg_lower = message.lower().strip()

    # ── Reset commands ──
    if any(w in msg_lower for w in ["restart", "reset", "start over", "new analysis", "start again"]):
        _reset_session(user_id)
        return {
            "response": f"Session reset. {INTRO_MESSAGE}",
            "step": "INIT",
            "session": _get_session(user_id),
            "agent_output": None,
        }

    # ── Who are you ──
    if any(w in msg_lower for w in ["who are you", "what can you do", "help", "what is this"]):
        return {
            "response": INTRO_MESSAGE,
            "step": session["step"],
            "session": session,
            "agent_output": None,
        }

    # ── STEP: INIT — waiting for ticker ──
    if session["step"] == "INIT":
        ticker = _extract_ticker(message)

        if not ticker:
            return {
                "response": (
                    "I need a stock ticker to begin analysis. Please provide a valid NSE/BSE ticker symbol.\n\n"
                    "**Examples:** RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK, WIPRO, SBIN\n\n"
                    "Which stock would you like to analyze?"
                ),
                "step": "INIT",
                "session": session,
                "agent_output": None,
            }

        # Confirm ticker and start analysis
        session["ticker"] = ticker
        session["user_profile"] = user_profile
        session["step"] = "DATA_ANALYSIS"

        # Run Data Analyst Agent
        try:
            live_data = await groww_service.get_stock_quote(ticker)
            historical = await groww_service.get_historical_data(ticker, days=30)
        except Exception:
            live_data = None
            historical = []

        analysis_result = await run_data_analyst(
            ticker=ticker,
            live_market_data=live_data,
            historical_data=historical,
            timeframe_days=7,
        )

        # Strip completion markers from report before storing
        clean_report = analysis_result["report"]
        for marker in ["DATA_ANALYSIS_COMPLETE: TRUE", "DATA_ANALYSIS_COMPLETE:TRUE"]:
            clean_report = clean_report.replace(marker, "").strip()
        analysis_result["report"] = clean_report
        session["market_analysis"] = clean_report
        session["step"] = "AWAITING_RISK_PROFILE"

        # Audit the Data Analyst report with LLM Auditor pipeline
        try:
            audit = await audit_and_revise_response(
                question=f"Market analysis for {ticker}",
                ai_response=analysis_result["report"],
            )
            if audit["was_revised"]:
                session["market_analysis"] = audit["final_response"]
                analysis_result["report"] = audit["final_response"]
                analysis_result["audit_verdict"] = audit["overall_verdict"]
                analysis_result["hallucination_risk"] = audit["hallucination_risk"]
                analysis_result["was_revised"] = True
        except Exception as e:
            print(f"[Coordinator/Audit] {e}")

        response = (
            f"✅ **Step 1 Complete — Market Analysis for {ticker}**\n\n"
            f"The Data Analyst Agent has completed a comprehensive market analysis for **{ticker}**.\n\n"
            f"📊 *Analysis includes: price performance, financial ratios, SEBI filing insights, "
            f"market sentiment, sector analysis, recent news, and macro factors.*\n\n"
            f"---\n\n"
            f"**Step 2: Develop Trading Strategies**\n\n"
            f"To tailor strategies to your needs, please tell me:\n\n"
            f"1. **Risk Tolerance:** conservative / moderate / aggressive\n"
            f"2. **Investment Duration:** short-term (<3 months) / medium-term (3-12 months) / long-term (>1 year)"
        )

        return {
            "response": response,
            "step": "AWAITING_RISK_PROFILE",
            "session": session,
            "agent_output": analysis_result,
            "show_analysis": True,
        }

    # ── STEP: AWAITING_RISK_PROFILE ──
    if session["step"] == "AWAITING_RISK_PROFILE":
        risk = _extract_risk_tolerance(message)
        duration = _extract_investment_duration(message)

        if not risk and not duration:
            return {
                "response": (
                    "Please specify your **risk tolerance** and **investment duration**:\n\n"
                    "- **Risk:** conservative / moderate / aggressive\n"
                    "- **Duration:** short-term / medium-term / long-term\n\n"
                    "Example: *'moderate risk, long-term investment'*"
                ),
                "step": "AWAITING_RISK_PROFILE",
                "session": session,
                "agent_output": None,
            }

        # Use defaults if only one provided
        session["risk_tolerance"] = risk or "moderate"
        session["investment_duration"] = duration or "long-term"
        session["step"] = "TRADING_ANALYSIS"

        # Run Trading Analyst Agent
        strategies_result = await run_trading_analyst(
            ticker=session["ticker"],
            market_analysis_report=session["market_analysis"],
            risk_tolerance=session["risk_tolerance"],
            investment_duration=session["investment_duration"],
            user_profile=session.get("user_profile"),
        )

        clean_strategies = strategies_result["strategies_report"]
        for marker in ["TRADING_ANALYSIS_COMPLETE: TRUE", "TRADING_ANALYSIS_COMPLETE:TRUE"]:
            clean_strategies = clean_strategies.replace(marker, "").strip()
        strategies_result["strategies_report"] = clean_strategies
        session["trading_strategies"] = clean_strategies
        session["step"] = "AWAITING_EXECUTION_PREFS"

        response = (
            f"✅ **Step 2 Complete — Trading Strategies for {session['ticker']}**\n\n"
            f"The Trading Analyst Agent has developed **5+ trading strategies** tailored to your "
            f"**{session['risk_tolerance']} risk profile** and **{session['investment_duration']} horizon**.\n\n"
            f"---\n\n"
            f"**Step 3: Define Execution Plan**\n\n"
            f"The Execution Agent will now create a detailed plan covering entry, holding, scaling, and exit.\n\n"
            f"Do you have any **execution preferences**?\n"
            f"- Preferred order types (limit/market)?\n"
            f"- Preferred broker?\n"
            f"- Any other constraints?\n\n"
            f"*Type 'no preference' or 'proceed' to use best-practice defaults.*"
        )

        return {
            "response": response,
            "step": "AWAITING_EXECUTION_PREFS",
            "session": session,
            "agent_output": strategies_result,
            "show_strategies": True,
        }

    # ── STEP: AWAITING_EXECUTION_PREFS ──
    # This step must NEVER trigger ticker extraction — it always proceeds to execution
    if session["step"] == "AWAITING_EXECUTION_PREFS":
        # Store preferences — any message here is treated as execution prefs or default
        no_pref_words = ["no preference", "no particular", "proceed", "default",
                         "none", "continue", "no", "nope", "skip", "ok", "okay"]
        if any(w in msg_lower for w in no_pref_words):
            session["execution_preferences"] = None
        else:
            session["execution_preferences"] = message

        session["step"] = "EXECUTION_PLANNING"

        # Get live price for execution plan
        live_price = None
        try:
            quote = await groww_service.get_stock_quote(session["ticker"])
            if quote:
                live_price = quote.get("price")
        except Exception:
            pass

        # Brief pause to avoid rate limits after Steps 1+2 consumed Groq/Gemini quota
        await asyncio.sleep(8)

        # Run Execution Agent
        execution_result = await run_execution_agent(
            ticker=session["ticker"],
            selected_strategy=session["trading_strategies"],
            market_analysis=session["market_analysis"],
            risk_tolerance=session["risk_tolerance"],
            investment_duration=session["investment_duration"],
            execution_preferences=session["execution_preferences"],
            live_price=live_price,
        )

        clean_exec = execution_result["execution_plan"]
        for marker in ["EXECUTION_PLAN_COMPLETE: TRUE", "EXECUTION_PLAN_COMPLETE:TRUE"]:
            clean_exec = clean_exec.replace(marker, "").strip()
        execution_result["execution_plan"] = clean_exec
        session["execution_plan"] = clean_exec
        session["step"] = "RISK_EVALUATION"

        # Brief pause before risk evaluation
        await asyncio.sleep(12)

        # Auto-proceed to risk evaluation
        risk_result = await run_risk_evaluation(
            ticker=session["ticker"],
            trading_strategies=session["trading_strategies"],
            execution_plan=session["execution_plan"],
            market_analysis=session["market_analysis"],
            risk_tolerance=session["risk_tolerance"],
            investment_duration=session["investment_duration"],
            user_profile=session.get("user_profile"),
        )

        clean_risk = risk_result["risk_evaluation"]
        for marker in ["RISK_EVALUATION_COMPLETE: TRUE", "RISK_EVALUATION_COMPLETE:TRUE"]:
            clean_risk = clean_risk.replace(marker, "").strip()
        risk_result["risk_evaluation"] = clean_risk
        session["risk_evaluation"] = clean_risk
        session["final_recommendation"] = risk_result["final_recommendation"]

        # Audit the Risk Evaluation report
        try:
            risk_audit = await audit_and_revise_response(
                question=f"Risk evaluation for {session['ticker']} trading strategy",
                ai_response=risk_result["risk_evaluation"],
            )
            if risk_audit["was_revised"]:
                session["risk_evaluation"] = risk_audit["final_response"]
                risk_result["risk_evaluation"] = risk_audit["final_response"]
                risk_result["audit_verdict"] = risk_audit["overall_verdict"]
        except Exception as e:
            print(f"[Coordinator/RiskAudit] {e}")
        session["step"] = "COMPLETE"

        response = (
            f"✅ **Steps 3 & 4 Complete — Execution Plan & Risk Evaluation for {session['ticker']}**\n\n"
            f"**Execution Agent** has created a detailed phase-by-phase execution plan.\n"
            f"**Risk Evaluation Agent** has completed a comprehensive risk assessment.\n\n"
            f"🏁 **Final Recommendation: {risk_result['final_recommendation']}**\n\n"
            f"---\n\n"
            f"**Advisory Process Complete** ✅\n\n"
            f"We have completed all 4 steps:\n"
            f"1. ✅ Market Analysis ({session['ticker']})\n"
            f"2. ✅ Trading Strategies ({session['risk_tolerance']} risk, {session['investment_duration']})\n"
            f"3. ✅ Execution Plan\n"
            f"4. ✅ Risk Evaluation\n\n"
            f"Type **'show analysis'**, **'show strategies'**, **'show execution'**, or **'show risk'** "
            f"to view any section in detail.\n\n"
            f"Type **'restart'** to analyze a new ticker.\n\n"
            f"{LEGAL_DISCLAIMER}"
        )

        return {
            "response": response,
            "step": "COMPLETE",
            "session": session,
            "agent_output": {
                "execution": execution_result,
                "risk": risk_result,
            },
            "show_execution": True,
            "show_risk": True,
            "final_recommendation": risk_result["final_recommendation"],
        }

    # ── STEP: COMPLETE — handle show commands and new analysis requests ──
    if session["step"] == "COMPLETE":
        # Show commands
        if "show analysis" in msg_lower or "market analysis" in msg_lower:
            return {"response": f"## 📊 Market Analysis — {session['ticker']}\n\n{session['market_analysis']}",
                    "step": "COMPLETE", "session": session, "agent_output": None}
        if "show strateg" in msg_lower or "trading strateg" in msg_lower:
            return {"response": f"## 📈 Trading Strategies — {session['ticker']}\n\n{session['trading_strategies']}",
                    "step": "COMPLETE", "session": session, "agent_output": None}
        if "show execution" in msg_lower or "execution plan" in msg_lower:
            return {"response": f"## ⚡ Execution Plan — {session['ticker']}\n\n{session['execution_plan']}",
                    "step": "COMPLETE", "session": session, "agent_output": None}
        if "show risk" in msg_lower or "risk evaluation" in msg_lower or "risk assessment" in msg_lower:
            return {"response": f"## 🛡️ Risk Evaluation — {session['ticker']}\n\n{session['risk_evaluation']}",
                    "step": "COMPLETE", "session": session, "agent_output": None}

        # New ticker request — only reset if a known ticker is explicitly found
        new_ticker = _extract_ticker(message)
        if new_ticker and new_ticker != session.get("ticker"):
            _reset_session(user_id)
            return await process_coordinator_message(user_id, message, user_profile)

        # Default: remind user of available commands
        return {
            "response": (
                f"The advisory process for **{session['ticker']}** is complete. "
                f"**Final Recommendation: {session.get('final_recommendation', 'PROCEED WITH CAUTION')}**\n\n"
                f"Commands:\n"
                f"- `show analysis` / `show strategies` / `show execution` / `show risk`\n"
                f"- Type a new ticker (e.g. TCS) to start a fresh analysis\n"
                f"- `restart` to reset\n\n"
                f"{LEGAL_DISCLAIMER}"
            ),
            "step": "COMPLETE", "session": session, "agent_output": None,
        }

    # Fallback
    return {
        "response": INTRO_MESSAGE,
        "step": "INIT",
        "session": _get_session(user_id),
        "agent_output": None,
    }


def get_session_state(user_id: int) -> Dict:
    return _get_session(user_id)


def clear_session(user_id: int):
    _reset_session(user_id)
