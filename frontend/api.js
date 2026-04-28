const API_BASE = 'http://localhost:8000/api/v1';
const userId = 1;

async function sendChatMessage(message, language = 'english') {
  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, user_id: userId, language })
    });
    return await response.json();
  } catch (error) {
    console.error('Chat API error:', error);
    return { response: 'Sorry, I am having trouble connecting. Please try again.' };
  }
}

async function loadUserData() {
  try {
    const [income, stress, emergency, spending, recommendations] = await Promise.all([
      fetch(`${API_BASE}/analysis/income/${userId}`).then(r => r.json()),
      fetch(`${API_BASE}/analysis/stress/${userId}`).then(r => r.json()),
      fetch(`${API_BASE}/analysis/emergency/${userId}`).then(r => r.json()),
      fetch(`${API_BASE}/analysis/spending/${userId}`).then(r => r.json()),
      fetch(`${API_BASE}/recommendations/${userId}`).then(r => r.json())
    ]);
    
    console.log('📊 Financial Data Loaded:', { income, stress, emergency, spending, recommendations });
    
    // Display income analysis
    if (income) {
      const incomeCard = document.querySelector('.insight-card:nth-child(1) .insight-value');
      if (incomeCard) incomeCard.textContent = `${income.stability_score}/100`;
      const incomeDesc = document.querySelector('.insight-card:nth-child(1) .insight-desc');
      if (incomeDesc) incomeDesc.textContent = `Strategy: ${income.recommended_sip_strategy}`;
    }
    
    // Display stress score
    if (stress) {
      const stressCard = document.querySelector('.insight-card:nth-child(2) .insight-value');
      if (stressCard) {
        stressCard.textContent = `${stress.score}/100`;
        const riskColor = stress.risk_level === 'LOW' ? '#10b981' : stress.risk_level === 'MEDIUM' ? '#f59e0b' : '#ef4444';
        stressCard.style.color = riskColor;
      }
      const stressDesc = document.querySelector('.insight-card:nth-child(2) .insight-desc');
      if (stressDesc) stressDesc.textContent = `Risk: ${stress.risk_level}`;
    }
    
    // Display emergency fund
    if (emergency && emergency.emergency_status) {
      const emergencyCard = document.querySelector('.insight-card:nth-child(3) .insight-value');
      if (emergencyCard) {
        const status = emergency.emergency_status.adequate ? '✅ Adequate' : '⚠️ Build Fund';
        emergencyCard.textContent = status;
        emergencyCard.style.fontSize = '18px';
      }
      const emergencyDesc = document.querySelector('.insight-card:nth-child(3) .insight-desc');
      if (emergencyDesc) {
        const months = emergency.emergency_status.months_covered || 0;
        emergencyDesc.textContent = `${months.toFixed(1)} months covered`;
      }
    }
    
    // Display spending analysis
    if (spending && spending.spending_analysis) {
      const spendCard = document.querySelector('.insight-card:nth-child(4) .insight-value');
      if (spendCard) {
        const totalSpend = Object.values(spending.spending_analysis).reduce((a, b) => a + (typeof b === 'number' ? b : 0), 0);
        spendCard.textContent = `₹${totalSpend.toLocaleString('en-IN')}`;
      }
      const spendDesc = document.querySelector('.insight-card:nth-child(4) .insight-desc');
      if (spendDesc && spending.savings_opportunities && spending.savings_opportunities.length > 0) {
        spendDesc.textContent = `${spending.savings_opportunities.length} savings opportunities`;
      }
    }
    
    return { income, stress, emergency, spending, recommendations };
  } catch (error) {
    console.error('❌ Load error:', error);
  }
}

loadUserData();


// ══════════════════════════════════════════════════════════
// NIRVANAX — Governance API Functions
// ══════════════════════════════════════════════════════════

async function sendGovernanceChat(message, userId = 1, language = 'english') {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, user_id: userId, language })
  });
  if (!res.ok) throw new Error(`Chat API error: ${res.status}`);
  return res.json();
}

async function getGovernanceLogs(userId = 1, limit = 20) {
  const res = await fetch(`${API_BASE}/governance/logs/${userId}?limit=${limit}`);
  if (!res.ok) throw new Error(`Governance logs error: ${res.status}`);
  return res.json();
}

async function getGovernanceStats() {
  const res = await fetch(`${API_BASE}/governance/stats`);
  if (!res.ok) throw new Error(`Governance stats error: ${res.status}`);
  return res.json();
}

async function getSentinelStats() {
  const res = await fetch(`${API_BASE}/security/firewall-stats`);
  if (!res.ok) throw new Error(`Sentinel stats error: ${res.status}`);
  return res.json();
}

// ── Verification Panel Renderer ──────────────────────────

function renderVerificationPanel(governance, council) {
  const panel = document.getElementById('verificationPanel');
  if (!panel || !governance) return;

  const { trust_score, risk_level, consensus, verdicts, alerts, bias_flags } = governance;

  // Show panel
  panel.style.display = 'block';

  // Consensus badge
  const vpConsensus = document.getElementById('vpConsensus');
  if (vpConsensus) {
    const actionMap = {
      'APPROVE': { label: '✓ Approved', cls: 'approve' },
      'APPROVE_WITH_CAUTION': { label: '⚠ Caution', cls: 'caution' },
      'BLOCK': { label: '✗ Blocked', cls: 'block' },
      'REVIEW': { label: '⟳ Review', cls: 'review' },
    };
    const a = actionMap[consensus?.action] || { label: consensus?.action, cls: 'review' };
    vpConsensus.textContent = a.label;
    vpConsensus.className = `vp-consensus ${a.cls}`;
  }

  // Trust score bar
  const vpTrustFill = document.getElementById('vpTrustFill');
  const vpTrustVal = document.getElementById('vpTrustVal');
  if (vpTrustFill) vpTrustFill.style.width = `${trust_score}%`;
  if (vpTrustVal) vpTrustVal.textContent = `${trust_score}/100`;

  // Agent verdicts
  const verdictMap = {
    'SAFE': 'safe', 'CAUTION': 'caution', 'BLOCK': 'block',
    'ACCURATE': 'accurate', 'UNCERTAIN': 'uncertain', 'HALLUCINATION': 'hallucination',
    'CONSISTENT': 'consistent', 'INCONSISTENT': 'inconsistent', 'CONTRADICTION': 'contradiction',
  };

  const vpEthicalVerdict = document.getElementById('vpEthicalVerdict');
  const vpMarketVerdict = document.getElementById('vpMarketVerdict');
  const vpLogicVerdict = document.getElementById('vpLogicVerdict');

  if (vpEthicalVerdict) {
    vpEthicalVerdict.textContent = verdicts.ethical;
    vpEthicalVerdict.className = `vp-verdict ${verdictMap[verdicts.ethical] || ''}`;
  }
  if (vpMarketVerdict) {
    vpMarketVerdict.textContent = verdicts.market;
    vpMarketVerdict.className = `vp-verdict ${verdictMap[verdicts.market] || ''}`;
  }
  if (vpLogicVerdict) {
    vpLogicVerdict.textContent = verdicts.logic;
    vpLogicVerdict.className = `vp-verdict ${verdictMap[verdicts.logic] || ''}`;
  }

  // Alerts
  const vpAlerts = document.getElementById('vpAlerts');
  if (vpAlerts) {
    vpAlerts.innerHTML = '';
    const allAlerts = [...(alerts || []), ...(bias_flags || [])];
    allAlerts.forEach(alert => {
      const div = document.createElement('div');
      div.className = 'vp-alert-item';
      div.textContent = alert;
      vpAlerts.appendChild(div);
    });
  }

  // XAI reasoning
  const vpXaiBody = document.getElementById('vpXaiBody');
  if (vpXaiBody && council) {
    vpXaiBody.innerHTML = '';
    const agents = [
      { key: 'ethical_auditor', label: '⚖️ Ethical Auditor (Gemini)' },
      { key: 'market_specialist', label: '📊 Market Specialist (Groq/Llama3)' },
      { key: 'logic_validator', label: '🔬 Logic Validator (Qwen)' },
    ];
    agents.forEach(({ key, label }) => {
      const agent = council[key];
      if (!agent) return;
      const div = document.createElement('div');
      div.className = 'vp-agent-reasoning';
      div.innerHTML = `
        <div class="vp-agent-reasoning-title">${label} · ${agent.latency_s}s</div>
        <div class="vp-agent-reasoning-text">${agent.response || 'No response'}</div>
      `;
      vpXaiBody.appendChild(div);
    });
  }
}

// ── Deliberation Pulse (typing indicator during council deliberation) ──

function showDeliberationPulse(container) {
  const pulse = document.createElement('div');
  pulse.className = 'deliberation-pulse';
  pulse.id = 'deliberationPulse';
  pulse.innerHTML = `
    <div class="pulse-dot"></div>
    <div class="pulse-dot"></div>
    <div class="pulse-dot"></div>
    <span>Council of Three deliberating...</span>
  `;
  container.appendChild(pulse);
  container.scrollTop = container.scrollHeight;
  return pulse;
}

function hideDeliberationPulse() {
  const pulse = document.getElementById('deliberationPulse');
  if (pulse) pulse.remove();
}

// ══════════════════════════════════════════════════════════
// NIRVANAX — 5-Agent Advisory Console API
// ══════════════════════════════════════════════════════════

async function sendAdvisoryQuery(query, userId = 1, language = 'english', mode = 'full') {
  const res = await fetch(`${API_BASE}/advisory/console`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, user_id: userId, language, advisory_mode: mode })
  });
  if (!res.ok) throw new Error(`Advisory API error: ${res.status}`);
  return res.json();
}

async function loadGovernanceAuditTrail(userId = 1, limit = 10) {
  const res = await fetch(`${API_BASE}/governance/logs/${userId}?limit=${limit}`);
  if (!res.ok) throw new Error(`Audit trail error: ${res.status}`);
  return res.json();
}

async function loadGovernanceEvents(userId = 1) {
  const res = await fetch(`${API_BASE}/governance/events/${userId}`);
  if (!res.ok) throw new Error(`Events error: ${res.status}`);
  return res.json();
}

// ── 5-Agent Council Panel Renderer ──────────────────────────────────────────

const VERDICT_CLASSES = {
  // Coordinator
  RECOMMEND: 'positive', CAUTION: 'caution', REJECT: 'negative',
  // Market
  BULLISH: 'positive', NEUTRAL: 'neutral', BEARISH: 'caution', DATA_INVALID: 'negative',
  // Strategy
  OPTIMAL: 'positive', SUBOPTIMAL: 'caution', MISALIGNED: 'negative',
  // Execution
  EXECUTE_NOW: 'positive', SCALE_IN: 'positive', WAIT: 'caution', AVOID: 'negative',
  // Risk
  SAFE: 'positive', MODERATE_RISK: 'caution', HIGH_RISK: 'negative', UNSAFE: 'negative',
};

const CARD_CLASSES = {
  positive: 'approved', caution: 'caution', negative: 'blocked', neutral: 'active'
};

function renderAdvisoryConsole(result) {
  if (!result || !result.governance) return;

  const gov = result.governance;
  const agents = result.agent_deliberation;
  const { trust_score, risk_level, consensus, verdicts, alerts } = gov;

  // ── Trust Ring ──
  const trustRingFill = document.getElementById('trustRingFill');
  const trustRingText = document.getElementById('trustRingText');
  const trustScoreTitle = document.getElementById('trustScoreTitle');
  if (trustRingFill) {
    const circumference = 201;
    const offset = circumference - (trust_score / 100) * circumference;
    trustRingFill.style.strokeDashoffset = offset;
    const color = trust_score >= 75 ? '#10b981' : trust_score >= 50 ? '#f59e0b' : '#ef4444';
    trustRingFill.style.stroke = color;
  }
  if (trustRingText) trustRingText.textContent = trust_score;
  if (trustScoreTitle) {
    const labels = { LOW: '✅ Low Risk', MODERATE: '⚠️ Moderate Risk', HIGH: '🔶 High Risk', CRITICAL: '🚨 Critical' };
    trustScoreTitle.textContent = labels[risk_level] || risk_level;
  }

  // ── Consensus Meter ──
  const consensusFill = document.getElementById('consensusFill');
  const consensusPct = document.getElementById('consensusPct');
  const consensusActionBadge = document.getElementById('consensusActionBadge');
  if (consensusFill) consensusFill.style.width = `${consensus.consensus_percent}%`;
  if (consensusPct) consensusPct.textContent = `${consensus.consensus_percent}%`;
  if (consensusActionBadge) {
    const actionMap = {
      APPROVE: { cls: 'approve', label: '✓ Approved' },
      APPROVE_WITH_CAUTION: { cls: 'caution', label: '⚠ Caution' },
      BLOCK: { cls: 'block', label: '✗ Blocked' },
      REJECT: { cls: 'block', label: '✗ Rejected' },
      REVIEW: { cls: 'review', label: '⟳ Review' },
    };
    const a = actionMap[consensus.action] || { cls: 'review', label: consensus.action };
    consensusActionBadge.innerHTML = `<span class="vp-consensus ${a.cls}" style="margin-top:6px;display:inline-block;">${a.label}</span>`;
  }

  // ── Council Status ──
  const councilStatus = document.getElementById('councilStatus');
  if (councilStatus) {
    councilStatus.textContent = 'Complete';
    councilStatus.className = 'agent-council-status active';
  }

  // ── Agent Cards ──
  const agentMap = [
    { key: 'coordinator', verdictKey: 'coordinator', dataKey: 'core_coordinator' },
    { key: 'market', verdictKey: 'market', dataKey: 'market_intelligence' },
    { key: 'strategy', verdictKey: 'strategy', dataKey: 'strategy_architect' },
    { key: 'execution', verdictKey: 'execution', dataKey: 'execution_governance' },
    { key: 'risk', verdictKey: 'risk', dataKey: 'risk_governance' },
  ];

  agentMap.forEach(({ key, verdictKey, dataKey }) => {
    const verdict = verdicts[verdictKey];
    const agentData = agents[dataKey];
    if (!agentData) return;

    const verdictCls = VERDICT_CLASSES[verdict] || 'neutral';
    const cardCls = CARD_CLASSES[verdictCls] || 'active';

    const card = document.getElementById(`agentCard_${key}`);
    const verdictEl = document.getElementById(`verdict_${key}`);
    const responseEl = document.getElementById(`response_${key}`);
    const latencyEl = document.getElementById(`latency_${key}`);

    if (card) card.className = `agent-card ${cardCls}`;
    if (verdictEl) { verdictEl.textContent = verdict; verdictEl.className = `agent-verdict-badge ${verdictCls}`; }
    if (responseEl) responseEl.textContent = agentData.response || '';
    if (latencyEl) latencyEl.textContent = `${agentData.latency_s}s · ${agentData.model}`;
  });

  // ── Governance Alerts ──
  const alertsEl = document.getElementById('governanceAlerts');
  if (alertsEl && alerts && alerts.length > 0) {
    alertsEl.innerHTML = alerts.map(a => `<div class="vp-alert-item">${a}</div>`).join('');
  } else if (alertsEl) {
    alertsEl.innerHTML = '';
  }

  // ── Global badges ──
  const globalRiskBadge = document.getElementById('globalRiskBadge');
  if (globalRiskBadge) {
    const riskMap = { LOW: 'low', MODERATE: 'moderate', HIGH: 'high', CRITICAL: 'critical' };
    globalRiskBadge.textContent = `Risk: ${risk_level}`;
    globalRiskBadge.className = `risk-badge ${riskMap[risk_level] || 'moderate'}`;
  }

  const ethicalRating = document.getElementById('ethicalRating');
  if (ethicalRating) {
    const grade = trust_score >= 80 ? 'A' : trust_score >= 65 ? 'B' : trust_score >= 50 ? 'C' : 'D';
    ethicalRating.textContent = `⚖️ Ethics: ${grade}`;
    ethicalRating.className = `ethical-safety-badge ${grade}`;
  }

  // ── Execution Plan ──
  const execPlanCard = document.getElementById('executionPlanCard');
  const execPlanBody = document.getElementById('executionPlanBody');
  if (result.execution_plan && execPlanCard && execPlanBody) {
    const ep = result.execution_plan;
    execPlanBody.innerHTML = Object.entries(ep).map(([k, v]) =>
      `<div class="execution-plan-row"><span class="execution-plan-key">${k.replace(/_/g,' ')}</span><span class="execution-plan-val">${v}</span></div>`
    ).join('');
    execPlanCard.style.display = 'block';
  } else if (execPlanCard) {
    execPlanCard.style.display = 'none';
  }

  // ── Alternative Strategies ──
  const altCard = document.getElementById('altStrategiesCard');
  const altBody = document.getElementById('altStrategiesBody');
  if (result.alternative_strategies && altCard && altBody) {
    altBody.innerHTML = result.alternative_strategies.map(s =>
      `<div class="alt-strategy-item">${s}</div>`
    ).join('');
    altCard.style.display = 'block';
  } else if (altCard) {
    altCard.style.display = 'none';
  }
}

// ── Audit Trail Renderer ─────────────────────────────────────────────────────

async function loadAuditTrail() {
  const container = document.getElementById('auditTrailList');
  if (!container) return;
  try {
    const data = await loadGovernanceAuditTrail(1, 8);
    const logs = data.governance_logs || [];
    if (!logs.length) {
      container.innerHTML = '<div style="text-align:center;padding:20px;color:rgba(148,163,184,0.4);font-size:13px;">No governance logs yet.</div>';
      return;
    }
    container.innerHTML = logs.map(log => {
      const dotCls = { APPROVE: 'approve', APPROVE_WITH_CAUTION: 'caution', BLOCK: 'block', REVIEW: 'review' }[log.consensus_action] || 'review';
      const ts = log.timestamp ? new Date(log.timestamp).toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'short' }) : '';
      return `
        <div class="audit-trail-item">
          <div class="audit-dot ${dotCls}"></div>
          <div class="audit-trail-content">
            <div class="audit-trail-query">${(log.query || '').slice(0, 60)}${log.query && log.query.length > 60 ? '...' : ''}</div>
            <div class="audit-trail-meta">${log.intent || 'general'} · ${ts}</div>
          </div>
          <div class="audit-trail-trust">${log.trust_score || '—'}/100</div>
        </div>`;
    }).join('');
  } catch (e) {
    container.innerHTML = '<div style="padding:12px;font-size:12px;color:rgba(148,163,184,0.4);">Connect backend to view audit trail.</div>';
  }
}

// ══════════════════════════════════════════════════════════
// NIRVANAX — Financial Advisor (Google ADK) API Functions
// ══════════════════════════════════════════════════════════

async function sendAdvisorMessage(message, userId = 1) {
  const res = await fetch(`${API_BASE}/advisor/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, user_id: userId })
  });
  if (!res.ok) throw new Error(`Advisor API error: ${res.status}`);
  return res.json();
}

async function getAdvisorSession(userId = 1) {
  const res = await fetch(`${API_BASE}/advisor/session/${userId}`);
  if (!res.ok) throw new Error(`Session error: ${res.status}`);
  return res.json();
}

async function resetAdvisorSessionAPI(userId = 1) {
  const res = await fetch(`${API_BASE}/advisor/session/${userId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(`Reset error: ${res.status}`);
  return res.json();
}

// ── Simple markdown renderer ─────────────────────────────

function renderMarkdown(text) {
  if (!text) return '<p style="color:rgba(148,163,184,0.4)">No content yet.</p>';

  // Strip completion markers
  text = text.replace(/DATA_ANALYSIS_COMPLETE:\s*TRUE/gi, '')
             .replace(/TRADING_ANALYSIS_COMPLETE:\s*TRUE/gi, '')
             .replace(/EXECUTION_PLAN_COMPLETE:\s*TRUE/gi, '')
             .replace(/RISK_EVALUATION_COMPLETE:\s*TRUE/gi, '')
             .trim();

  const lines = text.split('\n');
  let html = '';
  let inList = false;
  let inTable = false;

  for (let i = 0; i < lines.length; i++) {
    let line = lines[i];

    // Inline formatting
    line = line.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    line = line.replace(/`(.+?)`/g, '<code style="background:rgba(99,102,241,0.15);padding:1px 5px;border-radius:3px;font-size:11px">$1</code>');

    // Headers
    if (line.startsWith('### ')) {
      if (inList) { html += '</ul>'; inList = false; }
      html += `<h3 style="color:#6366f1;font-size:13px;font-weight:700;margin:14px 0 6px;text-transform:uppercase;letter-spacing:0.06em">${line.slice(4)}</h3>`;
    } else if (line.startsWith('## ')) {
      if (inList) { html += '</ul>'; inList = false; }
      html += `<h2 style="color:#f1f5f9;font-size:15px;font-weight:700;margin:16px 0 8px;border-bottom:1px solid rgba(255,255,255,0.08);padding-bottom:6px">${line.slice(3)}</h2>`;
    } else if (line.startsWith('# ')) {
      if (inList) { html += '</ul>'; inList = false; }
      html += `<h1 style="color:#f1f5f9;font-size:17px;font-weight:800;margin:18px 0 10px">${line.slice(2)}</h1>`;

    // Horizontal rule
    } else if (line.trim() === '---') {
      if (inList) { html += '</ul>'; inList = false; }
      html += '<hr style="border:none;border-top:1px solid rgba(255,255,255,0.08);margin:12px 0">';

    // Blockquote
    } else if (line.startsWith('> ')) {
      if (inList) { html += '</ul>'; inList = false; }
      html += `<blockquote style="border-left:3px solid #6366f1;padding:4px 10px;margin:6px 0;color:rgba(148,163,184,0.7);font-size:11px">${line.slice(2)}</blockquote>`;

    // Bullet list items (-, *, +)
    } else if (/^[\-\*\+] /.test(line)) {
      if (!inList) { html += '<ul style="padding-left:16px;margin:4px 0">'; inList = true; }
      html += `<li style="color:rgba(148,163,184,0.85);margin:3px 0;font-size:12px">${line.slice(2)}</li>`;

    // Numbered list
    } else if (/^\d+\.\s/.test(line)) {
      if (!inList) { html += '<ul style="padding-left:16px;margin:4px 0">'; inList = true; }
      html += `<li style="color:rgba(148,163,184,0.85);margin:3px 0;font-size:12px">${line.replace(/^\d+\.\s/, '')}</li>`;

    // Indented sub-bullets
    } else if (/^\s+[\-\*\+] /.test(line)) {
      html += `<li style="color:rgba(148,163,184,0.7);margin:2px 0;font-size:11px;margin-left:12px">${line.trim().slice(2)}</li>`;

    // Table rows
    } else if (line.startsWith('|')) {
      if (inList) { html += '</ul>'; inList = false; }
      if (!inTable) { html += '<table style="width:100%;border-collapse:collapse;margin:8px 0;font-size:11px">'; inTable = true; }
      const cells = line.split('|').filter(c => c.trim() && !c.trim().match(/^[-:]+$/));
      if (cells.length > 0) {
        const isHeader = lines[i+1] && lines[i+1].includes('---');
        const tag = isHeader ? 'th' : 'td';
        const style = isHeader
          ? 'background:rgba(99,102,241,0.15);color:#6366f1;padding:6px 8px;text-align:left;font-weight:700'
          : 'padding:5px 8px;border-bottom:1px solid rgba(255,255,255,0.05);color:rgba(148,163,184,0.8)';
        html += '<tr>' + cells.map(c => `<${tag} style="${style}">${c.trim()}</${tag}>`).join('') + '</tr>';
      }

    // Separator row (skip)
    } else if (/^[\|\s\-:]+$/.test(line) && line.includes('|')) {
      // skip markdown table separator

    // Empty line
    } else if (line.trim() === '') {
      if (inList) { html += '</ul>'; inList = false; }
      if (inTable) { html += '</table>'; inTable = false; }
      html += '<div style="height:6px"></div>';

    // Regular paragraph
    } else {
      if (inList) { html += '</ul>'; inList = false; }
      if (inTable) { html += '</table>'; inTable = false; }
      html += `<p style="color:rgba(148,163,184,0.85);margin:4px 0;font-size:12px;line-height:1.6">${line}</p>`;
    }
  }

  if (inList) html += '</ul>';
  if (inTable) html += '</table>';
  return html;
}
