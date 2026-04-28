"""
NirvanaX — Sentinel Layer v2
Upgraded with Google ADK LLM Auditor architecture (Critic → Reviser pipeline).

Architecture (inspired by google/adk-samples/llm-auditor):
  Layer 1 — Deterministic Firewall: regex-based prompt injection + fraud detection (instant, zero latency)
  Layer 2 — Critic Agent: extracts all factual CLAIMS from AI response, verifies each against
             Gemini's knowledge, assigns verdicts (Accurate/Inaccurate/Disputed/Unsupported/N/A)
  Layer 3 — Reviser Agent: takes Critic findings, minimally edits the response to fix inaccuracies
             while preserving style, structure, and length
  Layer 4 — Engine Cross-Validation: deterministic engine outputs override AI claims

Goal: Ensure every NirvanaX AI response is factually grounded, hallucination-free, and verified
before it reaches the user.
"""

import re
import httpx
import os
import time
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nirvanax.sentinel")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# ── Exact prompts from Google ADK LLM Auditor (google/adk-samples) ───────────

CRITIC_PROMPT = """You are a professional investigative journalist, excelling at critical thinking and verifying information before it is printed to a highly-trustworthy financial publication.
In this task you are given a question-answer pair from a financial AI assistant. The publication editor tasked you to double-check the answer text for factual accuracy, especially regarding:
- Stock prices, market data, financial ratios
- Investment return claims and projections
- Company financial metrics (revenue, profit, EPS, debt)
- Regulatory information (SEBI, RBI, tax rules)
- Economic data and macro indicators

# Your task

Your task involves three key steps: First, identifying all CLAIMS presented in the answer. Second, determining the reliability of each CLAIM. And lastly, provide an overall assessment.

## Step 1: Identify the CLAIMS
Carefully read the provided answer text. Extract every distinct CLAIM made within the answer. A CLAIM can be a statement of fact about the world or a logical argument presented to support a point. Focus especially on numerical claims, return projections, and market data.

## Step 2: Verify each CLAIM
For each CLAIM you identified in Step 1, perform the following:
* Consider the Context: Take into account the original question and any other CLAIMS already identified within the answer.
* Use your knowledge to verify: Use your training knowledge to assess whether the claim is plausible and accurate.
* Determine the VERDICT: Based on your evaluation, assign one of the following verdicts:
    * Accurate: The information is correct, complete, and consistent with reliable financial knowledge.
    * Inaccurate: The information contains errors, fabricated numbers, or inconsistencies with known financial facts.
    * Disputed: Reliable sources offer conflicting information — no definitive agreement.
    * Unsupported: No reliable basis can be found to substantiate the claim (potential hallucination).
    * Not Applicable: The claim is subjective opinion or general advice that doesn't require factual verification.
* Provide a JUSTIFICATION: Clearly explain the reasoning behind your assessment.

## Step 3: Provide an overall assessment
After evaluating each CLAIM, provide an OVERALL VERDICT and OVERALL JUSTIFICATION.
Overall verdicts: Accurate | Mostly Accurate | Contains Inaccuracies | Hallucinated

# Output format
The last block of your output MUST be a Markdown-formatted list with this exact structure:

## Verification Results
* **Claim**: [exact claim text]
  * **Verdict**: [Accurate/Inaccurate/Disputed/Unsupported/Not Applicable]
  * **Justification**: [your reasoning]

## Overall Assessment
* **Overall Verdict**: [Accurate/Mostly Accurate/Contains Inaccuracies/Hallucinated]
* **Overall Justification**: [summary reasoning]
* **Hallucination Risk**: [Low/Medium/High]
* **Requires Revision**: [Yes/No]

Here is the question and answer to double-check:
"""

REVISER_PROMPT = """You are a professional financial editor working for a highly-trustworthy financial advisory platform.
You are given a question-answer pair from a financial AI assistant. A reviewer has double-checked the answer and provided findings.
Your task is to minimally revise the answer text to make it accurate, while maintaining the overall structure, style, and length similar to the original.

The reviewer has identified CLAIMs and assigned VERDICTs:
    * Accurate: No edit needed.
    * Inaccurate: Fix following the reviewer's justification.
    * Disputed: Present two or more sides of the argument for balance.
    * Unsupported: Omit if not central, or soften the claim (e.g., "may", "historically", "generally").
    * Not Applicable: No edit needed.

Editing rules:
  * Fix Inaccurate claims using the reviewer's justification.
  * Soften Unsupported claims — replace specific numbers with ranges or qualitative descriptions.
  * Do NOT introduce any new claims or fabricate new data.
  * Keep edits minimal — preserve the original structure, tone, and length.
  * Ensure the revised answer is self-consistent and fluent.
  * For financial claims you cannot verify, use hedging language: "historically", "typically", "may", "approximately".

Output format:
  * Output ONLY the revised answer text (no preamble, no explanation).
  * After the answer, output exactly: ---END-OF-EDIT---
  * Stop immediately after ---END-OF-EDIT---

Here are the question-answer pair and reviewer findings:
"""


class SentinelLayer:
    """
    NirvanaX Sentinel Layer v2 — LLM Auditor-powered hallucination detection.

    Pipeline:
    1. Deterministic firewall (regex) — instant, zero latency
    2. Critic Agent (Gemini/Groq) — claim extraction + verification
    3. Reviser Agent (Gemini/Groq) — minimal correction of inaccuracies
    4. Engine cross-validation — deterministic ground truth override
    """

    def __init__(self):
        self.stats = {
            "blocked": 0,
            "allowed": 0,
            "hallucinations_caught": 0,
            "responses_revised": 0,
            "responses_accurate": 0,
            "bias_flags": 0,
        }

        # ── Layer 1: Deterministic attack patterns ────────────────────────────
        self.attack_patterns = {
            "SYSTEM_OVERRIDE": [
                r"ignore\s+(previous|all|above)\s+(instructions|prompts|rules)",
                r"disregard\s+(previous|all|system)\s+(instructions|context)",
                r"forget\s+(everything|all|previous)\s+(instructions|you were told)",
                r"new\s+instructions?:\s*you\s+are",
                r"system\s*:\s*you\s+are\s+now",
                r"override\s+your\s+(programming|instructions|rules)",
                r"ignore\s+all\s+previous",
                r"ignore.*instructions.*transfer",
            ],
            "ROLE_MANIPULATION": [
                r"you\s+are\s+no\s+longer\s+a\s+(financial|banking|assistant)",
                r"pretend\s+to\s+be\s+(admin|developer|system|root)",
                r"act\s+as\s+(if\s+you\s+are|a)\s+(hacker|attacker|admin)",
                r"roleplay\s+as\s+(admin|system|developer)",
                r"simulate\s+(being|that\s+you\s+are)\s+(admin|root)",
                r"act\s+as.*hacker",
            ],
            "DATA_EXFILTRATION": [
                r"show\s+(me\s+)?(all|other)\s+(users?|accounts?|passwords?|credentials?)",
                r"reveal\s+(system|internal|hidden|secret)\s+(data|information|config|prompt|instructions)",
                r"display\s+(database|table|schema|backend)\s+(structure|content)",
                r"print\s+(environment|config|secret|api)\s+(variables?|keys?)",
                r"what\s+is\s+your\s+(system\s+prompt|internal\s+instructions)",
                r"repeat\s+(your|the)\s+(system\s+prompt|instructions|rules)",
                r"get\s+me\s+the\s+(api\s+key|credentials?|passwords?)",
            ],
            "FINANCIAL_FRAUD": [
                r"transfer\s+\d+.*to\s+(account|upi|wallet).*\d+",
                r"send\s+money\s+to\s+(account|upi).*without\s+(verification|otp|confirmation)",
                r"bypass\s+(authentication|verification|otp|security)",
                r"skip\s+(verification|otp|2fa|authentication)",
                r"approve\s+(transaction|transfer|payment)\s+without\s+(otp|verification)",
                r"execute\s+(unauthorized|fraudulent)\s+(transaction|transfer)",
            ],
        }

        # ── Layer 1: Hallucination trigger patterns (prompt-level) ────────────
        self.hallucination_triggers = [
            r"guaranteed\s+\d+%\s+returns?",
            r"risk[\s-]free\s+(returns?|profit|investment)",
            r"(double|triple)\s+your\s+money\s+in\s+\d+\s+(days?|weeks?|months?)",
            r"100%\s+(safe|guaranteed|assured)\s+(returns?|profit)",
            r"no\s+risk\s+(investment|scheme|plan)",
            r"secret\s+(investment|trading)\s+(strategy|formula|method)",
        ]

        # ── Whitelist ─────────────────────────────────────────────────────────
        self.legitimate_patterns = [
            r"what\s+is\s+my\s+(balance|account\s+balance)",
            r"show\s+my\s+(transactions|spending|portfolio)",
            r"how\s+(much|can)\s+i\s+(invest|save)",
            r"recommend\s+(investments?|mutual\s+funds?|stocks?)",
            r"tell\s+me\s+(about|the)?\s*(stock\s+)?trends?\s+(in|of|for|about)?\s*\w+",
            r"\w+\s+(stock|share|equity)\s+(price|trends?|performance)",
            r"(stock|share|equity)\s+(trends?|price|performance)\s+(in|of|for)?\s*\w+",
            r"what\s+is\s+my\s+(stress\s+score|financial\s+health)",
            r"(reliance|tcs|infy|hdfc|icici|wipro|bharti|itc|sbin|lt)\s+(stock|share)",
            r"(nirvanax|governance|trust\s+score|council|verification)",
        ]

        self.audit_log: List[Dict] = []

    # ══════════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ══════════════════════════════════════════════════════════════════════════

    def validate(self, prompt: str, user_id: int) -> Tuple[bool, str, str]:
        """Layer 1: Deterministic prompt validation. Instant, zero latency."""
        if self._is_legitimate(prompt):
            self.stats["allowed"] += 1
            return True, prompt, "NONE"

        hallucination, h_pattern = self._detect_hallucination_trigger(prompt)
        if hallucination:
            self.stats["hallucinations_caught"] += 1
            self._log_event(user_id, prompt, "HALLUCINATION_TRIGGER", h_pattern)
            logger.warning(f"[Sentinel] HALLUCINATION_TRIGGER blocked — User {user_id}")
            return False, "", "HALLUCINATION_TRIGGER"

        threat, threat_type = self._detect_attack(prompt)
        if threat:
            self.stats["blocked"] += 1
            self._log_event(user_id, prompt, threat_type, "")
            logger.warning(f"[Sentinel] {threat_type} blocked — User {user_id}")
            return False, "", threat_type

        sanitized = self._sanitize(prompt)
        self.stats["allowed"] += 1
        return True, sanitized, "NONE"

    async def audit_and_revise(
        self,
        question: str,
        ai_response: str,
        engine_data: Optional[Dict] = None,
    ) -> Dict:
        """
        Layers 2-4: Full LLM Auditor pipeline.
        Critic verifies claims → Reviser fixes inaccuracies → Engine cross-validation.

        Returns:
            {
                "final_response": str,          # verified + revised response
                "original_response": str,        # original AI response
                "was_revised": bool,             # whether revision was needed
                "overall_verdict": str,          # Accurate/Mostly Accurate/Contains Inaccuracies/Hallucinated
                "hallucination_risk": str,       # Low/Medium/High
                "claims": list,                  # individual claim verdicts
                "engine_contradictions": list,   # contradictions with deterministic engines
                "audit_latency_ms": int,
            }
        """
        start = time.time()

        # ── Layer 4: Engine cross-validation (deterministic, instant) ─────────
        engine_contradictions = self._cross_validate_with_engines(ai_response, engine_data)

        # ── Layer 2: Critic Agent ─────────────────────────────────────────────
        critic_findings = await self._run_critic(question, ai_response)

        # ── Layer 3: Reviser Agent ────────────────────────────────────────────
        requires_revision = (
            critic_findings.get("overall_verdict") in ["Contains Inaccuracies", "Hallucinated"]
            or critic_findings.get("requires_revision") is True
            or len(engine_contradictions) > 0
        )

        final_response = ai_response
        was_revised = False

        if requires_revision:
            revised = await self._run_reviser(question, ai_response, critic_findings, engine_contradictions)
            if revised and revised != ai_response:
                final_response = revised
                was_revised = True
                self.stats["responses_revised"] += 1
                logger.info(f"[Sentinel] Response revised — verdict: {critic_findings.get('overall_verdict')}")
            else:
                self.stats["responses_accurate"] += 1
        else:
            self.stats["responses_accurate"] += 1

        if critic_findings.get("hallucination_risk") == "High":
            self.stats["hallucinations_caught"] += 1

        elapsed_ms = round((time.time() - start) * 1000)

        return {
            "final_response": final_response,
            "original_response": ai_response,
            "was_revised": was_revised,
            "overall_verdict": critic_findings.get("overall_verdict", "Unknown"),
            "hallucination_risk": critic_findings.get("hallucination_risk", "Unknown"),
            "requires_revision": requires_revision,
            "claims": critic_findings.get("claims", []),
            "critic_raw": critic_findings.get("raw_output", ""),
            "engine_contradictions": engine_contradictions,
            "audit_latency_ms": elapsed_ms,
        }

    def validate_ai_response(self, response: str, engine_data: Optional[Dict] = None) -> Dict:
        """
        Synchronous Layer 4 only — engine cross-validation without LLM audit.
        Used when async audit_and_revise is not called.
        """
        issues = self._cross_validate_with_engines(response, engine_data)

        # Also check response-level hallucination patterns
        for pattern in self.hallucination_triggers:
            if re.search(pattern, response, re.IGNORECASE):
                issues.append({"type": "HALLUCINATION_PATTERN", "detail": f"Pattern: {pattern}"})

        return {
            "is_safe": len(issues) == 0,
            "issues": issues,
            "validated_at": datetime.utcnow().isoformat(),
        }

    def get_stats(self) -> Dict:
        total = self.stats["blocked"] + self.stats["allowed"]
        return {
            **self.stats,
            "total_requests": total,
            "block_rate_percent": round(self.stats["blocked"] / total * 100, 2) if total else 0,
            "recent_audit_log": self.audit_log[-10:],
            "timestamp": datetime.utcnow().isoformat(),
        }

    # ══════════════════════════════════════════════════════════════════════════
    # LAYER 2: CRITIC AGENT
    # ══════════════════════════════════════════════════════════════════════════

    async def _run_critic(self, question: str, answer: str) -> Dict:
        """
        Run the Critic Agent using exact Google ADK LLM Auditor prompt.
        Extracts claims, verifies each, returns structured findings.
        """
        prompt = f"{CRITIC_PROMPT}\nQuestion: {question}\n\nAnswer: {answer}"

        raw_output = await self._call_llm_for_audit(prompt, max_tokens=1500, temperature=0.1)

        if not raw_output:
            return {
                "overall_verdict": "Unknown",
                "hallucination_risk": "Medium",
                "requires_revision": False,
                "claims": [],
                "raw_output": "",
            }

        return self._parse_critic_output(raw_output)

    def _parse_critic_output(self, raw: str) -> Dict:
        """Parse structured Critic output into claims list and overall verdict."""
        claims = []
        overall_verdict = "Unknown"
        hallucination_risk = "Low"
        requires_revision = False

        # Extract overall verdict
        verdict_match = re.search(
            r"\*\*Overall Verdict\*\*:\s*(.+?)(?:\n|$)", raw, re.IGNORECASE
        )
        if verdict_match:
            overall_verdict = verdict_match.group(1).strip()

        # Extract hallucination risk
        risk_match = re.search(
            r"\*\*Hallucination Risk\*\*:\s*(.+?)(?:\n|$)", raw, re.IGNORECASE
        )
        if risk_match:
            hallucination_risk = risk_match.group(1).strip()

        # Extract requires revision
        revision_match = re.search(
            r"\*\*Requires Revision\*\*:\s*(.+?)(?:\n|$)", raw, re.IGNORECASE
        )
        if revision_match:
            requires_revision = revision_match.group(1).strip().lower() == "yes"

        # Extract individual claims
        claim_blocks = re.findall(
            r"\*\*Claim\*\*:\s*(.+?)\n.*?\*\*Verdict\*\*:\s*(.+?)\n.*?\*\*Justification\*\*:\s*(.+?)(?=\n\s*\*\*Claim|\n\s*##|$)",
            raw,
            re.DOTALL | re.IGNORECASE,
        )
        for claim_text, verdict, justification in claim_blocks:
            claims.append({
                "claim": claim_text.strip(),
                "verdict": verdict.strip(),
                "justification": justification.strip()[:300],
            })

        # Auto-detect if revision needed from verdicts
        if not requires_revision:
            bad_verdicts = {"Inaccurate", "Unsupported", "Hallucinated"}
            if any(c["verdict"] in bad_verdicts for c in claims):
                requires_revision = True
            if overall_verdict in ["Contains Inaccuracies", "Hallucinated"]:
                requires_revision = True

        return {
            "overall_verdict": overall_verdict,
            "hallucination_risk": hallucination_risk,
            "requires_revision": requires_revision,
            "claims": claims,
            "raw_output": raw,
        }

    # ══════════════════════════════════════════════════════════════════════════
    # LAYER 3: REVISER AGENT
    # ══════════════════════════════════════════════════════════════════════════

    async def _run_reviser(
        self,
        question: str,
        original_answer: str,
        critic_findings: Dict,
        engine_contradictions: List[Dict],
    ) -> str:
        """
        Run the Reviser Agent using exact Google ADK LLM Auditor prompt.
        Minimally edits the response to fix inaccuracies.
        """
        # Build findings text for reviser
        findings_text = f"Question: {question}\n\nAnswer: {original_answer}\n\nFindings:\n"

        for i, claim in enumerate(critic_findings.get("claims", []), 1):
            findings_text += (
                f"\n* Claim {i}: {claim['claim']}\n"
                f"    * Verdict: {claim['verdict']}\n"
                f"    * Justification: {claim['justification']}\n"
            )

        # Add engine contradictions as additional findings
        if engine_contradictions:
            findings_text += "\n* Engine Cross-Validation Contradictions:\n"
            for ec in engine_contradictions:
                findings_text += f"    * {ec['type']}: {ec['detail']}\n"

        findings_text += (
            f"\n* Overall verdict: {critic_findings.get('overall_verdict', 'Unknown')}\n"
            f"* Overall justification: Response contains claims requiring correction.\n"
        )

        prompt = f"{REVISER_PROMPT}\n{findings_text}"

        raw_output = await self._call_llm_for_audit(prompt, max_tokens=1000, temperature=0.1)

        if not raw_output:
            return original_answer

        # Extract revised text (everything before ---END-OF-EDIT---)
        end_marker = "---END-OF-EDIT---"
        if end_marker in raw_output:
            revised = raw_output.split(end_marker)[0].strip()
        else:
            revised = raw_output.strip()

        # Safety: if revision is empty or too short, return original
        if not revised or len(revised) < len(original_answer) * 0.3:
            return original_answer

        return revised

    # ══════════════════════════════════════════════════════════════════════════
    # LAYER 4: ENGINE CROSS-VALIDATION
    # ══════════════════════════════════════════════════════════════════════════

    def _cross_validate_with_engines(
        self, response: str, engine_data: Optional[Dict]
    ) -> List[Dict]:
        """
        Cross-validate AI response against deterministic engine outputs.
        Catches contradictions between AI claims and computed ground truth.
        """
        contradictions = []
        if not engine_data:
            return contradictions

        # Stress score validation
        if "stress_score" in engine_data:
            engine_score = float(engine_data["stress_score"])
            score_matches = re.findall(r"stress\s+score[:\s]+(\d+)", response, re.IGNORECASE)
            for match in score_matches:
                claimed = float(match)
                if abs(claimed - engine_score) > 20:
                    contradictions.append({
                        "type": "STRESS_SCORE_CONTRADICTION",
                        "detail": f"AI claimed stress score {claimed}, engine computed {engine_score:.1f}",
                        "severity": "HIGH",
                    })

        # Savings rate validation
        if "savings_rate" in engine_data:
            engine_rate = float(engine_data["savings_rate"])
            rate_matches = re.findall(r"savings?\s+rate[:\s]+(\d+\.?\d*)%?", response, re.IGNORECASE)
            for match in rate_matches:
                claimed = float(match)
                if abs(claimed - engine_rate) > 15:
                    contradictions.append({
                        "type": "SAVINGS_RATE_CONTRADICTION",
                        "detail": f"AI claimed savings rate {claimed}%, engine computed {engine_rate:.1f}%",
                        "severity": "MEDIUM",
                    })

        # Emergency fund status validation
        if "emergency_status" in engine_data:
            engine_status = engine_data["emergency_status"].lower()
            if engine_status == "inadequate" and re.search(
                r"emergency\s+fund\s+(is\s+)?(adequate|sufficient|good|healthy)", response, re.IGNORECASE
            ):
                contradictions.append({
                    "type": "EMERGENCY_FUND_CONTRADICTION",
                    "detail": "AI claimed emergency fund is adequate, but engine computed it as inadequate",
                    "severity": "HIGH",
                })

        return contradictions

    # ══════════════════════════════════════════════════════════════════════════
    # LLM CALLER (Gemini → Groq fallback)
    # ══════════════════════════════════════════════════════════════════════════

    async def _call_llm_for_audit(
        self, prompt: str, max_tokens: int = 800, temperature: float = 0.1
    ) -> str:
        """
        Call LLM for audit tasks.
        Uses Groq first (faster, avoids Gemini rate limits from main analysis).
        Gemini fallback with 429 handling.
        Reduced max_tokens to 800 to stay within rate limits.
        """
        import asyncio as _aio

        # Try Groq first — faster and separate quota from Gemini
        if GROQ_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        GROQ_URL,
                        headers={
                            "Authorization": f"Bearer {GROQ_API_KEY}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": "llama-3.1-8b-instant",
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": max_tokens,
                            "temperature": temperature,
                        },
                    )
                    if resp.status_code == 200:
                        return resp.json()["choices"][0]["message"]["content"].strip()
                    if resp.status_code == 429:
                        logger.warning("[Sentinel/Groq] Rate limited — waiting 5s")
                        await _aio.sleep(5)
                    else:
                        logger.warning(f"[Sentinel/Groq] HTTP {resp.status_code}")
            except Exception as e:
                logger.warning(f"[Sentinel/Groq] {e}")

        # Gemini fallback
        if GEMINI_API_KEY:
            try:
                await _aio.sleep(2)  # Small delay to avoid simultaneous rate limits
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        f"{GEMINI_URL}?key={GEMINI_API_KEY}",
                        json={
                            "contents": [{"parts": [{"text": prompt}]}],
                            "generationConfig": {
                                "maxOutputTokens": max_tokens,
                                "temperature": temperature,
                            },
                        },
                    )
                    if resp.status_code == 200:
                        return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if resp.status_code == 429:
                        logger.warning("[Sentinel/Gemini] Rate limited — skipping audit this request")
                    else:
                        logger.warning(f"[Sentinel/Gemini] HTTP {resp.status_code}")
            except Exception as e:
                logger.warning(f"[Sentinel/Gemini] {e}")

        logger.warning("[Sentinel] LLM audit skipped — rate limits active, using engine validation only")
        return ""

    # ══════════════════════════════════════════════════════════════════════════
    # PRIVATE HELPERS
    # ══════════════════════════════════════════════════════════════════════════

    def _is_legitimate(self, prompt: str) -> bool:
        lower = prompt.lower()
        return any(re.search(p, lower, re.IGNORECASE) for p in self.legitimate_patterns)

    def _detect_attack(self, prompt: str) -> Tuple[bool, str]:
        lower = prompt.lower()
        for threat_type, patterns in self.attack_patterns.items():
            for pattern in patterns:
                if re.search(pattern, lower, re.IGNORECASE):
                    return True, threat_type
        return False, "NONE"

    def _detect_hallucination_trigger(self, prompt: str) -> Tuple[bool, str]:
        lower = prompt.lower()
        for pattern in self.hallucination_triggers:
            if re.search(pattern, lower, re.IGNORECASE):
                return True, pattern
        return False, ""

    def _sanitize(self, prompt: str) -> str:
        sanitized = re.sub(r"[<>{}[\]\\]", "", prompt)
        sanitized = re.sub(r"\s+", " ", sanitized).strip()
        return sanitized[:500]

    def _log_event(self, user_id: int, prompt: str, threat_type: str, detail: str):
        self.audit_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "threat_type": threat_type,
            "prompt_preview": prompt[:100],
            "detail": detail,
        })
        if len(self.audit_log) > 500:
            self.audit_log = self.audit_log[-500:]


# ── Singleton ─────────────────────────────────────────────────────────────────
sentinel = SentinelLayer()


def validate_user_prompt(prompt: str, user_id: int) -> Tuple[bool, str, str]:
    """Layer 1: Synchronous prompt validation."""
    return sentinel.validate(prompt, user_id)


def validate_ai_response(response: str, engine_data: Optional[Dict] = None) -> Dict:
    """Layer 4: Synchronous engine cross-validation."""
    return sentinel.validate_ai_response(response, engine_data)


async def audit_and_revise_response(
    question: str,
    ai_response: str,
    engine_data: Optional[Dict] = None,
) -> Dict:
    """Layers 2-4: Full async LLM Auditor pipeline (Critic → Reviser → Engine validation)."""
    return await sentinel.audit_and_revise(question, ai_response, engine_data)


def get_sentinel_stats() -> Dict:
    return sentinel.get_stats()
