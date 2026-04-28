/* ═══════════════════════════════════════════════
   NirvanaX — Verified Financial Intelligence OS
   Interactive Dashboard Script v2.0
   ═══════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
  // ── Cache DOM ──
  const $ = sel => document.querySelector(sel);
  const $$ = sel => document.querySelectorAll(sel);

  // ── TRANSLATIONS (i18n) ──
  const translations = {
    en: {
      "nav_home": "Home", "nav_transactions": "Transactions", "nav_transfer": "Transfer", "nav_invest": "Invest", "nav_loans": "Loans", "nav_bills": "Bills", "nav_assistant": "Assistant",
      "greeting": "Good Evening", "quick_send": "Send Money", "quick_pay": "Pay Bills", "quick_invest": "Invest", "quick_loans": "Loans",
      "bot_greeting": "Hi Akshay! 💚 I'm your AI financial assistant. How can I help you today?",
      "chat_balance": "Check Balance", "chat_txns": "Latest Transactions", "chat_transfer": "Transfer Money", "chat_spending": "Analyze Spending",
      "chat_placeholder": "Ask me anything...", "trade_terminal": "Live Trading", "trade_buy": "Buy", "trade_sell": "Sell",
      "tf_1d": "1D", "tf_1w": "1W", "tf_1m": "1M", "tf_1y": "1Y",
      "resp_balance": "Here is your current account balance summary:",
      "resp_portfolio": "Your investment portfolio is up 12.4% overall. Here is the allocation breakdown:",
      "resp_loan": "Here is your active loan and EMI breakdown:",
      "resp_txns": "Here are your latest transactions:",
      "resp_spending": "Here is your spending breakdown for this month:"
    },
    hi: {
      "nav_home": "होम", "nav_transactions": "लेनदेन", "nav_transfer": "ट्रांसफर", "nav_invest": "निवेश", "nav_loans": "ऋण", "nav_bills": "बिल", "nav_assistant": "सहायक",
      "greeting": "शुभ संध्या", "quick_send": "पैसे भेजें", "quick_pay": "बिल भुगतान", "quick_invest": "निवेश", "quick_loans": "ऋण",
      "bot_greeting": "नमस्ते अक्षय! 💚 मैं आपका AI वित्तीय सहायक हूँ। आज मैं आपकी कैसे मदद कर सकता हूँ?",
      "chat_balance": "बैलेंस जांचें", "chat_txns": "हाल के लेनदेन", "chat_transfer": "पैसे ट्रांसफर", "chat_spending": "खर्च विश्लेषण",
      "chat_placeholder": "मुझसे कुछ भी पूछें...", "trade_terminal": "लाइव ट्रेडिंग", "trade_buy": "खरीदें", "trade_sell": "बेचें",
      "tf_1d": "1दि", "tf_1w": "1स", "tf_1m": "1म", "tf_1y": "1वर्ष",
      "resp_balance": "यहाँ आपके वर्तमान खाते के बैलेंस का विवरण है:",
      "resp_portfolio": "आपका निवेश पोर्टफोलियो कुल मिलाकर 12.4% बढ़ा है। यहाँ आवंटन का विवरण है:",
      "resp_loan": "यहाँ आपके सक्रिय ऋण और EMI का विवरण है:",
      "resp_txns": "यहाँ आपके हाल के लेनदेन हैं:", "resp_spending": "इस महीने का खर्च विवरण:"
    },
    te: {
      "nav_home": "హోమ్", "nav_transactions": "లావాదేవీలు", "nav_transfer": "బదిలీ", "nav_invest": "పెట్టుబడి", "nav_loans": "రుణాలు", "nav_bills": "బిల్లులు", "nav_assistant": "సహాయకుడు",
      "greeting": "శుభ సాయంత్రం", "quick_send": "డబ్బు పంపండి", "quick_pay": "బిల్లు చెల్లింపు", "quick_invest": "పెట్టుబడి", "quick_loans": "రుణాలు",
      "bot_greeting": "హాయ్ అక్షయ్! 💚 నేను మీ AI ఆర్థిక సహాయకుడిని. ఈ రోజు మీకు ఎలా సహాయం చేయగలను?",
      "chat_balance": "బ్యాలెన్స్ తనిఖీ", "chat_txns": "ఇటీవలి లావాదేవీలు", "chat_transfer": "నగదు బదిలీ", "chat_spending": "ఖర్చు విశ్లేషణ",
      "chat_placeholder": "నన్ను ఏదైనా అడగండి...", "trade_terminal": "లైవ్ ట్రేడింగ్", "trade_buy": "కొనండి", "trade_sell": "అమ్మండి",
      "tf_1d": "1రో", "tf_1w": "1వా", "tf_1m": "1నె", "tf_1y": "1సం",
      "resp_balance": "మీ ప్రస్తుత ఖాతా బ్యాలెన్స్ సారాంశం ఇక్కడ ఉంది:",
      "resp_portfolio": "మీ పెట్టుబడి పోర్ట్‌ఫోలియో మొత్తంగా 12.4% పెరిగింది:",
      "resp_loan": "మీ యాక్టివ్ లోన్ మరియు EMI వివరాలు ఇక్కడ ఉన్నాయి:",
      "resp_txns": "మీ తాజా లావాదేవీలు:", "resp_spending": "ఈ నెల ఖర్చు వివరాలు:"
    }
  };

  let currentLang = 'en';

  function setLanguage(lang) {
    if (lang === 'bi') { currentLang = 'bi'; } else { currentLang = lang; }
    const dict = lang === 'bi' ? translations.en : translations[lang];
    if (!dict) return;
    $$('[data-i18n]').forEach(el => {
      const key = el.dataset.i18n;
      if (lang === 'bi') {
        const hi = translations.hi[key] || '';
        el.textContent = (dict[key] || '') + (hi ? ' / ' + hi : '');
      } else { el.textContent = dict[key] || el.textContent; }
    });
    $$('[data-i18n-attr]').forEach(el => {
      const parts = el.dataset.i18nAttr.split(':');
      if (parts.length === 2 && dict[parts[1]]) el.setAttribute(parts[0], dict[parts[1]]);
    });
  }

  // Language Dropdown Logic
  const langBtn = $('#langBtn'), langDropdown = $('#langDropdown');
  langBtn?.addEventListener('click', e => { e.stopPropagation(); langDropdown?.classList.toggle('open'); });
  $$('.lang-option').forEach(opt => {
    opt.addEventListener('click', e => {
      e.preventDefault();
      $$('.lang-option').forEach(o => o.classList.remove('active'));
      opt.classList.add('active');
      setLanguage(opt.dataset.lang);
      langDropdown?.classList.remove('open');
    });
  });

  // ── STARFIELD CANVAS ──
  const canvas = $('#starfield'), ctx = canvas?.getContext('2d');
  let stars = [], shootingStars = [];
  function resizeCanvas() {
    if (!canvas) return;
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  function initStars() {
    stars = [];
    for (let i = 0; i < 200; i++) {
      stars.push({ x: Math.random() * canvas.width, y: Math.random() * canvas.height, r: Math.random() * 1.5 + 0.3, a: Math.random(), da: (Math.random() - 0.5) * 0.02 });
    }
  }
  function addShootingStar() {
    if (shootingStars.length < 2 && Math.random() < 0.005) {
      shootingStars.push({ x: Math.random() * canvas.width, y: Math.random() * canvas.height * 0.4, vx: 4 + Math.random() * 3, vy: 2 + Math.random() * 2, life: 60 + Math.random() * 40, age: 0 });
    }
  }
  function animateStarfield() {
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    // Twinkling stars
    stars.forEach(s => {
      s.a += s.da;
      if (s.a > 1 || s.a < 0.2) s.da *= -1;
      ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255,255,255,${s.a})`; ctx.fill();
    });
    // Shooting stars
    addShootingStar();
    shootingStars = shootingStars.filter(ss => {
      ss.x += ss.vx; ss.y += ss.vy; ss.age++;
      const alpha = 1 - ss.age / ss.life;
      if (alpha <= 0) return false;
      ctx.beginPath();
      ctx.moveTo(ss.x, ss.y);
      ctx.lineTo(ss.x - ss.vx * 8, ss.y - ss.vy * 8);
      const grad = ctx.createLinearGradient(ss.x, ss.y, ss.x - ss.vx * 8, ss.y - ss.vy * 8);
      grad.addColorStop(0, `rgba(255,255,255,${alpha})`);
      grad.addColorStop(1, 'rgba(255,255,255,0)');
      ctx.strokeStyle = grad; ctx.lineWidth = 1.5; ctx.stroke();
      return true;
    });
    requestAnimationFrame(animateStarfield);
  }
  if (canvas) { resizeCanvas(); initStars(); animateStarfield(); window.addEventListener('resize', () => { resizeCanvas(); initStars(); }); }

  // ── 3D CREDIT CARD ──
  const creditCardContainer = $('#creditCardContainer'), creditCard = $('#creditCard');
  const cvvToggle = $('#cvvToggle'), cvvValue = $('#cvvValue');
  let cvvVisible = false;
  creditCardContainer?.addEventListener('click', e => { if (e.target.closest('.cvv-toggle')) return; creditCard.classList.toggle('flipped'); });
  cvvToggle?.addEventListener('click', () => { cvvVisible = !cvvVisible; cvvValue.textContent = cvvVisible ? '847' : '•••'; });
  creditCardContainer?.addEventListener('mousemove', e => {
    if (creditCard.classList.contains('flipped')) return;
    const rect = creditCardContainer.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5, y = (e.clientY - rect.top) / rect.height - 0.5;
    creditCard.style.transform = `rotateY(${x * 15}deg) rotateX(${-y * 15}deg)`;
  });
  creditCardContainer?.addEventListener('mouseleave', () => { if (!creditCard.classList.contains('flipped')) creditCard.style.transform = ''; });

  // ── BALANCE REVEAL ──
  $$('.eye-toggle').forEach(btn => {
    btn.addEventListener('click', e => {
      e.stopPropagation();
      const el = document.getElementById(btn.dataset.target);
      if (!el) return;
      const showing = el.textContent !== '₹•••••';
      el.textContent = showing ? '₹•••••' : el.dataset.amount;
      btn.style.transform = 'scale(1.3)'; setTimeout(() => btn.style.transform = '', 200);
    });
  });

  // ── NAVBAR — PAGE SWITCHING ──
  const navLinks = $$('.nav-links a'), pageSections = $$('.page-section');
  function switchPage(pageName) {
    pageSections.forEach(p => p.classList.remove('active'));
    const target = document.querySelector(`[data-page="${pageName}"]`);
    if (target) { target.classList.add('active'); target.style.animation = 'none'; target.offsetHeight; target.style.animation = ''; }
    navLinks.forEach(l => l.classList.toggle('active', l.dataset.nav === pageName));
    window.scrollTo({ top: 0, behavior: 'smooth' });
    // Trigger scroll reveals on new page
    setTimeout(() => { document.querySelectorAll('.reveal:not(.visible)').forEach(el => revealObserver.observe(el)); }, 100);
  }
  navLinks.forEach(link => {
    link.addEventListener('click', e => {
      if (link.hasAttribute('data-modal')) return;
      e.preventDefault();
      const page = link.dataset.nav;
      if (page) switchPage(page);
    });
  });
  // Quick action nav buttons
  $$('.action-btn[data-nav]').forEach(btn => {
    btn.addEventListener('click', () => switchPage(btn.dataset.nav));
  });

  // Hamburger
  const hamburger = $('#hamburger'), navLinksEl = $('#navLinks');
  hamburger?.addEventListener('click', () => navLinksEl?.classList.toggle('open'));

  // ── THEME TOGGLE ──
  const themeToggle = $('#themeToggle');
  themeToggle?.addEventListener('click', () => {
    const isLight = document.body.getAttribute('data-theme') === 'light';
    document.body.setAttribute('data-theme', isLight ? 'dark' : 'light');
  });

  // ── MODALS ──
  function openModal(id) { document.getElementById(id)?.classList.add('active'); }
  function closeModal(id) { document.getElementById(id)?.classList.remove('active'); }
  $$('[data-modal]').forEach(btn => btn.addEventListener('click', e => { e.preventDefault(); openModal(btn.dataset.modal); }));
  $$('.modal-close').forEach(btn => btn.addEventListener('click', () => closeModal(btn.dataset.close)));
  $$('.modal-overlay').forEach(overlay => overlay.addEventListener('click', e => { if (e.target === overlay) overlay.classList.remove('active'); }));

  // ── TRANSACTION SEARCH & FILTER ──
  const txnSearch = $('#txnSearch');
  if (txnSearch) {
    txnSearch.addEventListener('input', () => {
      const q = txnSearch.value.toLowerCase();
      $$('#fullTxnList .txn-item').forEach(item => {
        const name = item.querySelector('.txn-name')?.textContent.toLowerCase() || '';
        item.style.display = name.includes(q) ? '' : 'none';
      });
    });
  }
  const txnFilter = $('#txnFilter');
  if (txnFilter) {
    txnFilter.addEventListener('change', () => {
      const val = txnFilter.value;
      $$('#fullTxnList .txn-item').forEach(item => {
        const amount = item.querySelector('.txn-amount');
        if (val === 'All Transactions') item.style.display = '';
        else if (val === 'Credits Only') item.style.display = amount?.classList.contains('credit') ? '' : 'none';
        else if (val === 'Debits Only') item.style.display = amount?.classList.contains('debit') ? '' : 'none';
      });
    });
  }

  // ── PROFILE DROPDOWN ──
  const profileBtn = $('#profileBtn'), profileDropdown = $('#profileDropdown');
  profileBtn?.addEventListener('click', e => { e.stopPropagation(); profileDropdown?.classList.toggle('open'); });
  document.addEventListener('click', () => { profileDropdown?.classList.remove('open'); langDropdown?.classList.remove('open'); });

  // ── NOTIFICATIONS ──
  const notifBtn = $('#notifBtn'), notifPanel = $('#notifPanel'), notifBadge = $('#notifBadge');
  notifBtn?.addEventListener('click', e => { e.stopPropagation(); notifPanel?.classList.toggle('open'); });
  document.addEventListener('click', e => { if (!notifPanel?.contains(e.target) && e.target !== notifBtn) notifPanel?.classList.remove('open'); });
  $('#markAllRead')?.addEventListener('click', () => { $$('.notif-item').forEach(i => i.classList.remove('unread')); if (notifBadge) notifBadge.style.display = 'none'; });

  // ── SPENDING CHART ──
  const spendingCanvas = $('#spendingChart');
  if (spendingCanvas && typeof Chart !== 'undefined') {
    new Chart(spendingCanvas, {
      type: 'doughnut',
      data: { labels: ['Food', 'Shopping', 'Transport', 'Bills', 'Entertainment'], datasets: [{ data: [8500, 17498, 320, 2188, 649], backgroundColor: ['#3b82f6', '#a855f7', '#f59e0b', '#10b981', '#ec4899'], borderWidth: 0, borderRadius: 4 }] },
      options: { responsive: true, maintainAspectRatio: false, cutout: '72%', plugins: { legend: { display: false } } }
    });
  }

  // ── SPARKLINE SVG GENERATION ──
  $$('.holding-sparkline').forEach(el => {
    const points = el.dataset.points?.split(',').map(Number);
    if (!points || points.length < 2) return;
    const w = 160, h = 40, min = Math.min(...points), max = Math.max(...points), range = max - min || 1;
    const coords = points.map((v, i) => `${(i / (points.length - 1)) * w},${h - ((v - min) / range) * h}`);
    const isUp = points[points.length - 1] >= points[0];
    const color = isUp ? '#10b981' : '#ef4444';
    el.innerHTML = `<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none"><defs><linearGradient id="sg_${el.dataset.points.slice(0, 5)}" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="${color}" stop-opacity="0.3"/><stop offset="100%" stop-color="${color}" stop-opacity="0"/></linearGradient></defs><path d="M${coords.join(' L')} L${w},${h} L0,${h}Z" fill="url(#sg_${el.dataset.points.slice(0, 5)})"/><polyline points="${coords.join(' ')}" fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round"/></svg>`;
  });

  // ── SCROLL REVEAL (IntersectionObserver) ──
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => { if (entry.isIntersecting) { entry.target.classList.add('visible'); revealObserver.unobserve(entry.target); } });
  }, { threshold: 0.1 });
  $$('.reveal').forEach(el => revealObserver.observe(el));

  // ── STOCK DETAIL PANEL ──
  const stockData = {
    reliance: { name: 'Reliance Industries', price: '₹1,250', buyPrice: '₹1,113', current: '₹62,500', pl: '+₹6,850', plPct: '+12.3%', allocation: '25.4%', history: '+32% (1Y)' },
    tcs: { name: 'TCS', price: '₹1,917', buyPrice: '₹1,812', current: '₹57,500', pl: '+₹3,150', plPct: '+5.8%', allocation: '23.4%', history: '+18% (1Y)' },
    axis: { name: 'Axis Bluechip Fund', price: '₹45,670', buyPrice: '₹38,652', current: '₹45,670', pl: '+₹7,018', plPct: '+18.2%', allocation: '18.6%', history: '+24% (1Y)' },
    hdfc: { name: 'HDFC Mid-Cap Fund', price: '₹40,000', buyPrice: '₹34,934', current: '₹40,000', pl: '+₹5,066', plPct: '+14.5%', allocation: '16.3%', history: '+21% (1Y)' },
    sgb: { name: 'Sovereign Gold Bond', price: '₹40,000', buyPrice: '₹33,697', current: '₹40,000', pl: '+₹6,303', plPct: '+18.7%', allocation: '16.3%', history: '+28% (1Y)' }
  };
  const detailPanel = $('#stockDetailPanel'), detailContent = $('#stockDetailContent');
  $$('.holding-card').forEach(card => {
    card.addEventListener('click', () => {
      const key = card.dataset.stock, data = stockData[key];
      if (!data) return;
      detailContent.innerHTML = `
        <h2 style="font-size:24px;font-weight:700;margin-bottom:4px">${data.name}</h2>
        <p style="color:var(--text-muted);font-size:14px;margin-bottom:24px">Current Price: ${data.price}</p>
        <div class="stock-detail-chart" style="display:flex;align-items:center;justify-content:center;color:var(--text-muted);font-size:13px">📈 Price chart visualization</div>
        <div class="detail-stat-grid">
          <div class="detail-stat"><div class="detail-stat-label">Buy Price</div><div class="detail-stat-value">${data.buyPrice}</div></div>
          <div class="detail-stat"><div class="detail-stat-label">Current Value</div><div class="detail-stat-value">${data.current}</div></div>
          <div class="detail-stat"><div class="detail-stat-label">Profit/Loss</div><div class="detail-stat-value" style="color:var(--success)">${data.pl} (${data.plPct})</div></div>
          <div class="detail-stat"><div class="detail-stat-label">Allocation</div><div class="detail-stat-value">${data.allocation}</div></div>
          <div class="detail-stat" style="grid-column:span 2"><div class="detail-stat-label">Historical Performance</div><div class="detail-stat-value">${data.history}</div></div>
        </div>`;
      detailPanel.classList.add('open');
    });
  });
  $('#stockDetailClose')?.addEventListener('click', () => detailPanel.classList.remove('open'));

  // ── EMI CALCULATOR ──
  const fmt = v => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(v);
  function calcEMI() {
    const P = parseFloat($('#emiAmount')?.value) || 0;
    const r = (parseFloat($('#emiRate')?.value) || 0) / 12 / 100;
    const n = (parseFloat($('#emiTenure')?.value) || 0) * 12;
    if (!P || !r || !n) return;
    const emi = P * r * Math.pow(1 + r, n) / (Math.pow(1 + r, n) - 1);
    const total = emi * n, interest = total - P;
    const emiEl = $('#emiResultResult'), intEl = $('#emiResultInterest'), totEl = $('#emiResultTotal');
    if (emiEl) emiEl.textContent = fmt(emi);
    if (intEl) intEl.textContent = fmt(interest);
    if (totEl) totEl.textContent = fmt(total);
  }
  ['#emiAmount', '#emiRate', '#emiTenure'].forEach(s => $(s)?.addEventListener('input', calcEMI));
  // Open loan modal from Apply buttons
  $$('.apply-loan-btn').forEach(btn => btn.addEventListener('click', e => { e.stopPropagation(); openModal('applyLoanModal'); }));
  $$('.invest-explore-item[data-loan-type]').forEach(item => item.addEventListener('click', () => openModal('applyLoanModal')));

  // ── TRANSFER METHOD CHIPS ──
  $$('.method-chip').forEach(chip => chip.addEventListener('click', () => { $$('.method-chip').forEach(c => c.classList.remove('active')); chip.classList.add('active'); }));
  $$('.tab-btn').forEach(tb => tb.addEventListener('click', () => { tb.closest('.transfer-type-tabs')?.querySelectorAll('.tab-btn').forEach(t => t.classList.remove('active')); tb.classList.add('active'); }));
  $$('.bill-cat').forEach(bc => bc.addEventListener('click', () => { $$('.bill-cat').forEach(c => c.classList.remove('active')); bc.classList.add('active'); }));
  $('#fetchBill')?.addEventListener('click', () => { const bd = $('#billDetails'); if (bd) bd.style.display = 'block'; });

  // ── TRADING WIDGET ──
  const tfWidget = $('#tradingFloatingWidget'), tfToggle = $('#tfToggle'), tfHeader = $('#tfHeader');
  tfToggle?.addEventListener('click', () => tfWidget?.classList.toggle('collapsed'));
  // Drag
  let isDragging = false, dragX, dragY;
  tfHeader?.addEventListener('mousedown', e => {
    if (e.target.closest('.tf-toggle') || e.target.closest('.tf-lang-select')) return;
    isDragging = true;
    const rect = tfWidget.getBoundingClientRect();
    dragX = e.clientX - rect.left; dragY = e.clientY - rect.top;
    tfWidget.style.transition = 'none';
  });
  document.addEventListener('mousemove', e => {
    if (!isDragging) return;
    tfWidget.style.left = (e.clientX - dragX) + 'px';
    tfWidget.style.top = (e.clientY - dragY) + 'px';
    tfWidget.style.right = 'auto'; tfWidget.style.bottom = 'auto';
  });
  document.addEventListener('mouseup', () => { isDragging = false; if (tfWidget) tfWidget.style.transition = ''; });

  // Trading language
  const tfLangTrans = {
    en: { buy: 'Buy', sell: 'Sell', tf: ['1D', '1W', '1M', '1Y'], title: 'Live Trading' },
    hi: { buy: 'खरीदें', sell: 'बेचें', tf: ['1दि', '1स', '1म', '1वर्ष'], title: 'लाइव ट्रेडिंग' },
    te: { buy: 'కొనండి', sell: 'అమ్మండి', tf: ['1రో', '1వా', '1నె', '1సం'], title: 'లైవ్ ట్రేడింగ్' },
    bi: { buy: 'Buy/खरीदें', sell: 'Sell/बेचें', tf: ['1D', '1W', '1M', '1Y'], title: 'Live Trading/लाइव ट्रेडिंग' }
  };
  $('#tfLangSelect')?.addEventListener('change', function () {
    const t = tfLangTrans[this.value] || tfLangTrans.en;
    const buyBtn = $('.tf-action-buy'), sellBtn = $('.tf-action-sell');
    if (buyBtn) buyBtn.textContent = t.buy;
    if (sellBtn) sellBtn.textContent = t.sell;
    const title = $('.tf-title span');
    if (title) title.textContent = t.title;
    $$('.tf-tf-btn').forEach((btn, i) => { if (t.tf[i]) btn.textContent = t.tf[i]; });
  });
  $$('.tf-tf-btn').forEach(btn => btn.addEventListener('click', () => { $$('.tf-tf-btn').forEach(b => b.classList.remove('active')); btn.classList.add('active'); }));

  // ── AI CHATBOT ──
  const chatMessages = $('#chatbotMessagesFullScreen'), chatInput = $('#chatInputFullScreen'), chatSend = $('#chatSendFullScreen');
  const summaryBody = $('#tabularSummaryBody');
  let chatLang = 'en';

  // Chat language switcher
  $$('.chat-lang-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      $$('.chat-lang-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      chatLang = btn.dataset.lang;
      // Update greeting and placeholder
      const dict = chatLang === 'bi' ? translations.en : translations[chatLang];
      if (dict) {
        const greet = chatMessages?.querySelector('[data-i18n="bot_greeting"]');
        if (greet) {
          if (chatLang === 'bi') greet.textContent = translations.en.bot_greeting + '\n' + translations.hi.bot_greeting;
          else greet.textContent = dict.bot_greeting;
        }
        if (chatInput && dict.chat_placeholder) chatInput.placeholder = dict.chat_placeholder;
        // Update quick buttons
        $$('.chat-quick-btn').forEach(qb => {
          const key = qb.dataset.i18n;
          if (key && dict[key]) {
            if (chatLang === 'bi') qb.textContent = dict[key] + '/' + (translations.hi[key] || '');
            else qb.textContent = dict[key];
          }
        });
      }
    });
  });

  // Keyword detection and responses
  const keywords = {
    balance: { en: ['balance', 'account', 'money'], hi: ['बैलेंस', 'खाता', 'पैसा', 'शेष'], te: ['బ్యాలెన్స్', 'ఖాతా', 'డబ్బు'] },
    portfolio: { en: ['portfolio', 'invest', 'stock', 'mutual'], hi: ['पोर्टफोलियो', 'निवेश', 'शेयर'], te: ['పోర్ట్‌ఫోలియో', 'పెట్టుబడి', 'షేర్'] },
    loan: { en: ['loan', 'emi', 'ऋण'], hi: ['ऋण', 'लोन', 'किस्त'], te: ['రుణం', 'లోన్', 'EMI'] },
    txns: { en: ['transaction', 'recent', 'history'], hi: ['लेनदेन', 'हाल'], te: ['లావాదేవీ', 'చరిత్ర'] },
    spending: { en: ['spend', 'expense', 'budget'], hi: ['खर्च', 'बजट'], te: ['ఖర్చు', 'బడ్జెట్'] }
  };

  const tables = {
    balance: `<div class="summary-table-title">💰 Account Balances</div><table class="summary-table"><thead><tr><th>Account</th><th>Balance</th><th>Change</th></tr></thead><tbody><tr><td>Savings A/C</td><td>₹1,25,430</td><td style="color:var(--success)">+₹12,400</td></tr><tr><td>Current A/C</td><td>₹2,34,567</td><td style="color:var(--success)">+₹34,200</td></tr><tr><td>Fixed Deposit</td><td>₹5,00,000</td><td style="color:var(--success)">7.25% p.a.</td></tr></tbody></table>`,
    portfolio: `<div class="summary-table-title">📊 Portfolio Allocation</div><table class="summary-table"><thead><tr><th>Asset</th><th>Value</th><th>Return</th></tr></thead><tbody><tr><td>Reliance</td><td>₹62,500</td><td style="color:var(--success)">+12.3%</td></tr><tr><td>TCS</td><td>₹57,500</td><td style="color:var(--success)">+5.8%</td></tr><tr><td>Axis MF</td><td>₹45,670</td><td style="color:var(--success)">+18.2%</td></tr><tr><td>HDFC MF</td><td>₹40,000</td><td style="color:var(--success)">+14.5%</td></tr><tr><td>Gold Bond</td><td>₹40,000</td><td style="color:var(--success)">+18.7%</td></tr></tbody></table>`,
    loan: `<div class="summary-table-title">🏦 Loan & EMI Summary</div><table class="summary-table"><thead><tr><th>Loan</th><th>Outstanding</th><th>EMI</th><th>Rate</th></tr></thead><tbody><tr><td>Home Loan</td><td>₹16,00,000</td><td>₹18,750</td><td>8.5%</td></tr><tr><td>Personal</td><td>₹2,50,000</td><td>₹3,700</td><td>11.5%</td></tr></tbody></table>`,
    txns: `<div class="summary-table-title">📋 Recent Transactions</div><table class="summary-table"><thead><tr><th>Description</th><th>Amount</th><th>Date</th></tr></thead><tbody><tr><td>Amazon</td><td style="color:var(--danger)">-₹2,499</td><td>27 Feb</td></tr><tr><td>Salary (TCS)</td><td style="color:var(--success)">+₹85,000</td><td>25 Feb</td></tr><tr><td>Swiggy</td><td style="color:var(--danger)">-₹456</td><td>26 Feb</td></tr><tr><td>Uber</td><td style="color:var(--danger)">-₹320</td><td>26 Feb</td></tr></tbody></table>`,
    spending: `<div class="summary-table-title">💸 Spending Breakdown</div><table class="summary-table"><thead><tr><th>Category</th><th>Amount</th><th>%</th></tr></thead><tbody><tr><td>Shopping</td><td>₹17,498</td><td>54%</td></tr><tr><td>Food</td><td>₹8,500</td><td>26%</td></tr><tr><td>Bills</td><td>₹2,188</td><td>7%</td></tr><tr><td>Transport</td><td>₹320</td><td>1%</td></tr><tr><td>Entertainment</td><td>₹649</td><td>2%</td></tr></tbody></table>`
  };

  function detectIntent(msg) {
    const lower = msg.toLowerCase();
    for (const [intent, langs] of Object.entries(keywords)) {
      for (const words of Object.values(langs)) {
        if (words.some(w => lower.includes(w))) return intent;
      }
    }
    return null;
  }

  async function sendChat() {
    const msg = chatInput?.value.trim();
    if (!msg) return;

    // Append user message
    const userDiv = document.createElement('div');
    userDiv.className = 'chat-msg user';
    userDiv.innerHTML = `<p>${msg}</p><span class="chat-time">Just now</span>`;
    chatMessages.appendChild(userDiv);
    chatInput.value = '';
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Show deliberation pulse
    const pulse = showDeliberationPulse(chatMessages);

    const langMap = {'en': 'english', 'hi': 'hindi', 'te': 'telugu', 'bi': 'english'};
    let data;
    try {
      data = await sendGovernanceChat(msg, 1, langMap[chatLang] || 'english');
    } catch (e) {
      // Fallback to legacy sendChatMessage if governance API unavailable
      try { data = await sendChatMessage(msg, langMap[chatLang] || 'english'); } catch (e2) { data = { response: 'NirvanaX is connecting... Please ensure the backend is running.' }; }
    }

    hideDeliberationPulse();

    // ── Render Verification Panel ──
    if (data.governance) {
      renderVerificationPanel(data.governance, data.council_deliberation);
    }

    const stockMatch = msg.toLowerCase().match(/\b(stock|stocks|share|shares)\b/);
    const investMatch = msg.toLowerCase().match(/\b(invest|investment|portfolio|recommend|suggest|where to invest)\b/);

    if (stockMatch && data.response) {
      const words = msg.split(' ');
      let stock = '';
      for (let i = 0; i < words.length; i++) {
        if (words[i].toLowerCase() === 'about' && words[i+1]) {
          stock = words[i+1].replace(/[^a-zA-Z]/g, '').toUpperCase();
          break;
        }
      }
      if (!stock) stock = words[0].toUpperCase();
      const text = data.response;
      const priceMatch = text.match(/₹([\d,]+\.?\d*)/g);
      const changeMatch = text.match(/([+-]?\d+\.\d+)%/);
      const volumeMatch = text.match(/([\d,]+)\s+shares/);
      if (summaryBody) {
        summaryBody.innerHTML = `
          <div class="summary-table-title">📈 ${stock} Live Data</div>
          <table class="summary-table"><thead><tr><th>Metric</th><th>Value</th></tr></thead>
          <tbody>
            <tr><td>Current Price</td><td>${priceMatch ? priceMatch[0] : 'N/A'}</td></tr>
            <tr><td>Change</td><td style="color:${changeMatch && parseFloat(changeMatch[1]) >= 0 ? 'var(--success)' : 'var(--danger)'}">${changeMatch ? changeMatch[1] + '%' : 'N/A'}</td></tr>
            <tr><td>Volume</td><td>${volumeMatch ? volumeMatch[1] + ' shares' : 'N/A'}</td></tr>
            <tr><td>Status</td><td>${changeMatch && parseFloat(changeMatch[1]) >= 0 ? '📈 Up' : '📉 Down'}</td></tr>
          </tbody></table>
          <div style="margin-top:16px;padding:12px;background:rgba(59,130,246,0.1);border-radius:8px;font-size:13px;color:var(--text-muted)">📊 View live chart in floating trading widget</div>`;
      }
      const symbolMap = {'TCS': 'BSE:TCS', 'RELIANCE': 'BSE:RELIANCE', 'HDFC': 'BSE:HDFCBANK', 'AXIS': 'BSE:AXISBANK', 'INFOSYS': 'BSE:INFY', 'INFY': 'BSE:INFY', 'WIPRO': 'BSE:WIPRO', 'SBIN': 'BSE:SBIN', 'ICICI': 'BSE:ICICIBANK', 'BHARTI': 'BSE:BHARTIARTL', 'ITC': 'BSE:ITC', 'LT': 'BSE:LT', 'IRCTC': 'BSE:IRCTC', 'TATAMOTORS': 'BSE:TATAMOTORS', 'TATA': 'BSE:TATAMOTORS', 'ADANI': 'BSE:ADANIENT', 'ONGC': 'BSE:ONGC', 'COALINDIA': 'BSE:COALINDIA', 'POWERGRID': 'BSE:POWERGRID', 'NTPC': 'BSE:NTPC'};
      const tfChart = document.querySelector('#tradingFloatingWidget .tradingview-widget-container');
      if (tfChart) {
        const symbol = symbolMap[stock] || `BSE:${stock}`;
        tfChart.innerHTML = `<div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-mini-symbol-overview.js" async>{"symbol": "${symbol}","width": "100%","height": "100%","locale": "in","dateRange": "1M","colorTheme": "dark","isTransparent": true,"autosize": true}</script>`;
        const tfWidgetEl = document.getElementById('tradingFloatingWidget');
        if (tfWidgetEl && tfWidgetEl.classList.contains('collapsed')) tfWidgetEl.classList.remove('collapsed');
      }
    } else if (investMatch && data.recommendations) {
      if (summaryBody) {
        let recoRows = '';
        data.recommendations.slice(0, 5).forEach(r => {
          const riskColor = r.risk_level === 'LOW' ? 'var(--success)' : r.risk_level === 'MEDIUM' ? 'var(--warning)' : 'var(--danger)';
          recoRows += `<tr><td>${r.product_name}</td><td>${r.product_type}</td><td style="color:${riskColor}">${r.risk_level}</td><td>${r.suitability_score}/100</td><td>₹${r.min_investment.toLocaleString('en-IN')}</td></tr>`;
        });
        summaryBody.innerHTML = `
          <div class="summary-table-title">📊 Verified Investment Recommendations</div>
          <table class="summary-table"><thead><tr><th>Product</th><th>Type</th><th>Risk</th><th>Score</th><th>Min Invest</th></tr></thead>
          <tbody>${recoRows}</tbody></table>
          <div style="margin-top:16px;padding:12px;background:rgba(16,185,129,0.1);border-radius:8px;font-size:13px;color:var(--text-muted)">✅ Governance-verified · Trust-scored · Bias-audited</div>`;
      }
    } else {
      const intent = detectIntent(msg);
      if (intent && tables[intent] && summaryBody) summaryBody.innerHTML = tables[intent];
    }

    // Append bot response with governance badge
    const botDiv = document.createElement('div');
    botDiv.className = 'chat-msg bot';
    const trustScore = data.governance?.trust_score;
    const riskLevel = data.governance?.risk_level;
    const govBadge = trustScore != null
      ? `<span class="gov-badge">🛡️ Trust: ${trustScore}/100 · ${riskLevel || ''}</span>`
      : '';
    botDiv.innerHTML = `<p>${data.response || data.message}</p>${govBadge}<span class="chat-time">Just now</span>`;
    chatMessages.appendChild(botDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  chatSend?.addEventListener('click', sendChat);
  chatInput?.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); } });
  // Quick buttons
  $$('.chat-quick-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      chatInput.value = btn.textContent;
      sendChat();
    });
  });

  // Auto-resize textarea
  chatInput?.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 250) + 'px';
  });

  // ── TRANSFER AMOUNT UPDATE ──
  const transferAmount = $('#transferAmount'), transferSubmit = $('#transferSubmit');
  transferAmount?.addEventListener('input', () => {
    if (transferSubmit) transferSubmit.textContent = `Transfer ₹${new Intl.NumberFormat('en-IN').format(transferAmount.value || 0)}`;
  });

  // ── Initial greeting time ──
  const hour = new Date().getHours();
  const greetEl = $('[data-i18n="greeting"]');
  if (greetEl) {
    if (hour < 12) greetEl.textContent = 'Good Morning';
    else if (hour < 17) greetEl.textContent = 'Good Afternoon';
    else greetEl.textContent = 'Good Evening';
  }

  // ── CALCULATE EMI ON LOAD ──
  calcEMI();
});



// ══════════════════════════════════════════════════════════
// NIRVANAX — Advisory Console Interaction Logic
// ══════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
  // ── Advisory Console page nav ──
  const advisoryNavLink = document.querySelector('[data-nav="advisory"]');
  if (advisoryNavLink) {
    advisoryNavLink.addEventListener('click', (e) => {
      e.preventDefault();
      // Use existing switchPage if available
      if (typeof switchPage === 'function') {
        switchPage('advisory');
      } else {
        document.querySelectorAll('.page-section').forEach(p => p.classList.remove('active'));
        const target = document.querySelector('[data-page="advisory"]');
        if (target) target.classList.add('active');
        document.querySelectorAll('.nav-links a').forEach(l => l.classList.remove('active'));
        advisoryNavLink.classList.add('active');
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
      loadAuditTrail();
    });
  }

  // ── Advisory Mode Chips ──
  let currentAdvisoryMode = 'full';
  document.querySelectorAll('.mode-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('.mode-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      currentAdvisoryMode = chip.dataset.mode || 'full';
    });
  });

  // ── Advisory Send ──
  const advisoryInput = document.getElementById('advisoryInput');
  const advisorySend = document.getElementById('advisorySend');
  const advisoryMessages = document.getElementById('advisoryMessages');

  async function sendAdvisoryMessage() {
    const query = advisoryInput?.value.trim();
    if (!query || !advisoryMessages) return;

    // Append user message
    const userDiv = document.createElement('div');
    userDiv.className = 'chat-msg user';
    userDiv.innerHTML = `<p>${query}</p><span class="chat-time">Just now</span>`;
    advisoryMessages.appendChild(userDiv);
    advisoryInput.value = '';
    advisoryMessages.scrollTop = advisoryMessages.scrollHeight;

    // Set council to deliberating
    const councilStatus = document.getElementById('councilStatus');
    if (councilStatus) {
      councilStatus.textContent = 'Deliberating...';
      councilStatus.className = 'agent-council-status deliberating';
    }

    // Set all agent cards to active/loading
    ['coordinator', 'market', 'strategy', 'execution', 'risk'].forEach(key => {
      const card = document.getElementById(`agentCard_${key}`);
      const verdict = document.getElementById(`verdict_${key}`);
      const response = document.getElementById(`response_${key}`);
      if (card) card.className = 'agent-card active';
      if (verdict) { verdict.textContent = 'Analyzing...'; verdict.className = 'agent-verdict-badge neutral'; }
      if (response) response.textContent = 'Processing...';
    });

    // Show deliberation pulse in chat
    const pulse = typeof showDeliberationPulse === 'function'
      ? showDeliberationPulse(advisoryMessages)
      : null;

    let result;
    try {
      result = await sendAdvisoryQuery(query, 1, 'english', currentAdvisoryMode);
    } catch (e) {
      // Fallback to legacy chat
      try {
        result = await sendGovernanceChat(query, 1, 'english');
        result.agent_deliberation = result.council_deliberation || {};
      } catch (e2) {
        result = {
          primary_response: 'NirvanaX Advisory Console is connecting. Please ensure the backend is running on port 8000.',
          governance: null, agent_deliberation: {}
        };
      }
    }

    if (pulse) pulse.remove();

    // Render agent council panel
    if (result.governance) {
      renderAdvisoryConsole(result);
    }

    // Append bot response with trust badge
    const botDiv = document.createElement('div');
    botDiv.className = 'chat-msg bot';
    const trustScore = result.governance?.trust_score;
    const riskLevel = result.governance?.risk_level;
    const consensusAction = result.governance?.consensus?.action;
    const govBadge = trustScore != null
      ? `<span class="gov-badge">🛡️ Trust: ${trustScore}/100 · ${riskLevel || ''} · ${consensusAction || ''}</span>`
      : '';
    botDiv.innerHTML = `<p>${result.primary_response || result.response || ''}</p>${govBadge}<span class="chat-time">Just now</span>`;
    advisoryMessages.appendChild(botDiv);
    advisoryMessages.scrollTop = advisoryMessages.scrollHeight;

    // Refresh audit trail
    setTimeout(loadAuditTrail, 500);
  }

  advisorySend?.addEventListener('click', sendAdvisoryMessage);
  advisoryInput?.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendAdvisoryMessage(); }
  });
  advisoryInput?.addEventListener('input', () => {
    if (advisoryInput) {
      advisoryInput.style.height = 'auto';
      advisoryInput.style.height = Math.min(advisoryInput.scrollHeight, 120) + 'px';
    }
  });

  // ── Nav advisory link style ──
  const navAdvisoryLink = document.querySelector('.nav-advisory-link');
  if (navAdvisoryLink) {
    navAdvisoryLink.style.cssText = 'background:linear-gradient(135deg,rgba(99,102,241,0.15),rgba(79,70,229,0.1));border:1px solid rgba(99,102,241,0.3);border-radius:8px;padding:4px 10px;color:#6366f1;font-weight:700;';
  }
});


// ══════════════════════════════════════════════════════════
// NIRVANAX — Financial Advisor (Google ADK) UI Logic
// ══════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {

  // ── State ──
  const advisorState = {
    reports: { analysis: '', strategies: '', execution: '', risk: '' },
    currentReport: 'analysis',
    step: 'INIT',
  };

  // ── Nav link ──
  const advisorNavLink = document.querySelector('[data-nav="advisor"]');
  if (advisorNavLink) {
    advisorNavLink.style.cssText = 'background:linear-gradient(135deg,rgba(16,185,129,0.12),rgba(5,150,105,0.08));border:1px solid rgba(16,185,129,0.25);border-radius:8px;padding:4px 10px;color:#10b981;font-weight:700;';
    advisorNavLink.addEventListener('click', (e) => {
      e.preventDefault();
      document.querySelectorAll('.page-section').forEach(p => p.classList.remove('active'));
      const target = document.querySelector('[data-page="advisor"]');
      if (target) target.classList.add('active');
      document.querySelectorAll('.nav-links a').forEach(l => l.classList.remove('active'));
      advisorNavLink.classList.add('active');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // ── Workflow step updater ──
  function updateWorkflowStep(step) {
    const stepMap = {
      'INIT': 0,
      'DATA_ANALYSIS': 1, 'AWAITING_RISK_PROFILE': 1,
      'TRADING_ANALYSIS': 2, 'AWAITING_EXECUTION_PREFS': 2,
      'EXECUTION_PLANNING': 3, 'RISK_EVALUATION': 4,
      'COMPLETE': 4,
    };
    const currentIdx = stepMap[step] || 0;
    const badge = document.getElementById('advisorStepBadge');
    const stepLabels = ['Ready', 'Data Analysis', 'Strategies', 'Execution', 'Risk Eval'];
    if (badge) badge.textContent = `Step: ${stepLabels[currentIdx] || step}`;

    for (let i = 1; i <= 4; i++) {
      const el = document.getElementById(`wfStep${i}`);
      const status = document.getElementById(`wfStatus${i}`);
      if (!el || !status) continue;
      if (i < currentIdx) {
        el.className = 'advisor-workflow-step complete';
        status.textContent = '✓ Done';
        status.className = 'wf-step-status complete';
      } else if (i === currentIdx) {
        el.className = 'advisor-workflow-step active';
        status.textContent = 'Active';
        status.className = 'wf-step-status active';
      } else {
        el.className = 'advisor-workflow-step';
        status.textContent = 'Pending';
        status.className = 'wf-step-status';
      }
    }
  }

  // ── Agent status updater ──
  function setAgentStatus(agent, status) {
    const el = document.getElementById(`agentStatus_${agent}`);
    if (!el) return;
    const map = { idle: 'Idle', running: 'Running...', complete: '✓ Done', error: 'Error' };
    el.textContent = map[status] || status;
    el.className = `advisor-agent-status ${status}`;
  }

  // ── Report viewer ──
  window.showAdvisorReport = function(type) {
    document.querySelectorAll('[id^="reportTab_"]').forEach(t => t.classList.remove('active'));
    const tab = document.getElementById(`reportTab_${type}`);
    if (tab) tab.classList.add('active');
    advisorState.currentReport = type;
    const content = document.getElementById('advisorReportContent');
    if (!content) return;
    const report = advisorState.reports[type];
    if (report) {
      content.innerHTML = renderMarkdown(report);
    } else {
      content.innerHTML = `<div style="color:rgba(148,163,184,0.4);font-size:12px;padding:20px 0;">
        ${type.charAt(0).toUpperCase() + type.slice(1)} report not yet generated. Complete the advisory workflow to view.
      </div>`;
    }
  };

  // ── Reset session ──
  window.resetAdvisorSession = async function() {
    try { await resetAdvisorSessionAPI(1); } catch (e) {}
    advisorState.reports = { analysis: '', strategies: '', execution: '', risk: '' };
    advisorState.step = 'INIT';
    updateWorkflowStep('INIT');
    ['data', 'trading', 'execution', 'risk'].forEach(a => setAgentStatus(a, 'idle'));
    const msgs = document.getElementById('advisorChatMessages');
    if (msgs) {
      msgs.innerHTML = `<div class="chat-msg bot">
        <p>🏛️ Session reset. Welcome back to <strong>NirvanaX Financial Advisor</strong>. Provide a stock ticker to begin a new analysis.</p>
        <span class="chat-time">Just now</span>
      </div>`;
    }
    showAdvisorReport('analysis');
  };

  // ── Send message ──
  const advisorInput = document.getElementById('advisorInput');
  const advisorSendBtn = document.getElementById('advisorSendBtn');
  const advisorMessages = document.getElementById('advisorChatMessages');

  async function sendAdvisorMsg() {
    const msg = advisorInput?.value.trim();
    if (!msg || !advisorMessages) return;

    // Append user message
    const userDiv = document.createElement('div');
    userDiv.className = 'chat-msg user';
    userDiv.innerHTML = `<p>${msg}</p><span class="chat-time">Just now</span>`;
    advisorMessages.appendChild(userDiv);
    advisorInput.value = '';
    advisorMessages.scrollTop = advisorMessages.scrollHeight;

    // Show typing indicator
    const pulse = typeof showDeliberationPulse === 'function'
      ? showDeliberationPulse(advisorMessages)
      : null;

    // Update agent statuses based on current step
    const step = advisorState.step;
    if (step === 'INIT') setAgentStatus('data', 'running');
    else if (step === 'AWAITING_RISK_PROFILE') setAgentStatus('trading', 'running');
    else if (step === 'AWAITING_EXECUTION_PREFS') {
      setAgentStatus('execution', 'running');
      setAgentStatus('risk', 'running');
    }

    let result;
    try {
      result = await sendAdvisorMessage(msg, 1);
    } catch (e) {
      if (pulse) pulse.remove();
      const errDiv = document.createElement('div');
      errDiv.className = 'chat-msg bot';
      errDiv.innerHTML = `<p>⚠️ Unable to connect to NirvanaX backend. Please ensure the server is running on port 8000.</p><span class="chat-time">Just now</span>`;
      advisorMessages.appendChild(errDiv);
      advisorMessages.scrollTop = advisorMessages.scrollHeight;
      return;
    }

    if (pulse) pulse.remove();

    // Update workflow state
    advisorState.step = result.step || 'INIT';
    updateWorkflowStep(result.step);

    // Update agent statuses and store reports
    if (result.show_analysis && result.agent_output?.report) {
      advisorState.reports.analysis = result.agent_output.report;
      setAgentStatus('data', 'complete');
      showAdvisorReport('analysis');
    }
    if (result.show_strategies && result.agent_output?.strategies_report) {
      advisorState.reports.strategies = result.agent_output.strategies_report;
      setAgentStatus('trading', 'complete');
    }
    if (result.show_execution) {
      const execOut = result.agent_output?.execution;
      if (execOut?.execution_plan) {
        advisorState.reports.execution = execOut.execution_plan;
        setAgentStatus('execution', 'complete');
      }
      const riskOut = result.agent_output?.risk;
      if (riskOut?.risk_evaluation) {
        advisorState.reports.risk = riskOut.risk_evaluation;
        setAgentStatus('risk', 'complete');
        showAdvisorReport('risk');
      }
    }

    // Build bot message
    const botDiv = document.createElement('div');
    botDiv.className = 'chat-msg bot';
    let responseHtml = `<p>${(result.response || '').replace(/\n/g, '<br>')}</p>`;

    // Add final recommendation badge
    if (result.final_recommendation) {
      const recMap = {
        'PROCEED': { cls: 'proceed', icon: '✅' },
        'PROCEED WITH CAUTION': { cls: 'caution', icon: '⚠️' },
        'DO NOT PROCEED': { cls: 'reject', icon: '🚫' },
      };
      const rec = recMap[result.final_recommendation] || { cls: 'caution', icon: '⚠️' };
      responseHtml += `<div class="final-rec-badge ${rec.cls}">${rec.icon} ${result.final_recommendation}</div>`;
    }

    responseHtml += `<span class="chat-time">Just now</span>`;
    botDiv.innerHTML = responseHtml;
    advisorMessages.appendChild(botDiv);
    advisorMessages.scrollTop = advisorMessages.scrollHeight;
  }

  advisorSendBtn?.addEventListener('click', sendAdvisorMsg);
  advisorInput?.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendAdvisorMsg(); }
  });
  advisorInput?.addEventListener('input', () => {
    if (advisorInput) {
      advisorInput.style.height = 'auto';
      advisorInput.style.height = Math.min(advisorInput.scrollHeight, 100) + 'px';
    }
  });

  // ── Quick action buttons ──
  document.querySelectorAll('.advisor-quick-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      if (advisorInput) advisorInput.value = btn.dataset.msg || btn.textContent;
      sendAdvisorMsg();
    });
  });

  // ── Init report viewer ──
  showAdvisorReport('analysis');
});
