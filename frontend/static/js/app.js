// PhishGuard - Main JS
const $ = id => document.getElementById(id);
const $$ = s => document.querySelectorAll(s);

let currentUrl = '';
let imageFile = null;
let qrFile = null;

// ── Page navigation ──────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  $$('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      $$('.nav-btn').forEach(b => b.classList.remove('active'));
      $$('.page').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      $(`page-${btn.dataset.page}`).classList.add('active');
      if (btn.dataset.page === 'history') loadHistory();
    });
  });

  // Scan tabs
  $$('.scan-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      $$('.scan-tab').forEach(t => t.classList.remove('active'));
      $$('.tab-panel').forEach(p => p.classList.remove('active'));
      tab.classList.add('active');
      $(`tab-${tab.dataset.tab}`).classList.add('active');
      hideResults();
    });
  });

  // Scan buttons
  $('btn-scan-url').addEventListener('click', scanUrl);
  $('btn-scan-email').addEventListener('click', scanEmail);
  $('btn-scan-screenshot').addEventListener('click', scanScreenshot);
  $('btn-scan-image').addEventListener('click', scanImage);
  $('btn-scan-qr').addEventListener('click', scanQr);
  $('btn-new-scan').addEventListener('click', hideResults);
  $('btn-report').addEventListener('click', reportUrl);
  $('btn-clear').addEventListener('click', clearHistory);

  // File uploads
  setupUpload('image-dropzone', 'image-file', 'image-preview-wrap', 'image-preview-img', f => { imageFile = f; });
  setupUpload('qr-dropzone', 'qr-file', 'qr-preview-wrap', 'qr-preview-img', f => { qrFile = f; });
  $('image-remove').addEventListener('click', () => { imageFile = null; resetUpload('image-dropzone','image-preview-wrap','image-file'); });
  $('qr-remove').addEventListener('click', () => { qrFile = null; resetUpload('qr-dropzone','qr-preview-wrap','qr-file'); });

  // Enter key on inputs
  $('url-input').addEventListener('keydown', e => { if(e.key==='Enter') scanUrl(); });
  $('screenshot-input').addEventListener('keydown', e => { if(e.key==='Enter') scanScreenshot(); });
});

// ── Upload helpers ────────────────────────────────────────────────────────────
function setupUpload(zoneId, inputId, previewWrapId, previewImgId, onFile) {
  const zone = $(zoneId), input = $(inputId);
  zone.addEventListener('click', () => input.click());
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('drag-over'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
  zone.addEventListener('drop', e => {
    e.preventDefault(); zone.classList.remove('drag-over');
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f, zone, previewWrapId, previewImgId, onFile);
  });
  input.addEventListener('change', () => {
    if (input.files[0]) handleFile(input.files[0], zone, previewWrapId, previewImgId, onFile);
  });
}

function handleFile(file, zone, previewWrapId, previewImgId, onFile) {
  onFile(file);
  const reader = new FileReader();
  reader.onload = e => {
    $(previewImgId).src = e.target.result;
    zone.classList.add('hidden');
    $(previewWrapId).classList.remove('hidden');
  };
  reader.readAsDataURL(file);
}

function resetUpload(zoneId, previewWrapId, inputId) {
  $(zoneId).classList.remove('hidden');
  $(previewWrapId).classList.add('hidden');
  $(inputId).value = '';
}

// ── Scan functions ────────────────────────────────────────────────────────────
async function scanUrl() {
  const url = $('url-input').value.trim();
  if (!url) { shake($('url-input')); return; }
  currentUrl = url;

  
  const rep = await postJSON('/api/check_reported', { url });
  if (rep.is_reported) {
    $('reported-banner').classList.remove('hidden');
  } else {
    $('reported-banner').classList.add('hidden');
  }

  const doScreenshot = $('url-screenshot-toggle').checked;
  if (doScreenshot) {
    setLoading(true, 'Scanning URL and capturing screenshot...');
    try {
      const [urlRes, ssRes] = await Promise.all([
        postJSON('/api/scan/url', { url }),
        postJSON('/api/scan/screenshot', { url })
      ]);
      renderResults({ url_result: urlRes, screenshot_result: ssRes, url }, 'url+ss');
    } catch(e) { showError(e.message); } finally { setLoading(false); }
  } else {
    setLoading(true, 'Analyzing URL with XGBoost and WHOIS...');
    try {
      const data = await postJSON('/api/scan/url', { url });
      renderResults(data, 'url');
    } catch(e) { showError(e.message); } finally { setLoading(false); }
  }
}

async function scanEmail() {
  const text = $('email-input').value.trim();
  if (!text) { shake($('email-input')); return; }
  setLoading(true, 'Processing email through RoBERTa...');
  try {
    const data = await postJSON('/api/scan/email', { text });
    renderResults(data, 'email');
  } catch(e) { showError(e.message); } finally { setLoading(false); }
}

async function scanScreenshot() {
  const url = $('screenshot-input').value.trim();
  if (!url) { shake($('screenshot-input')); return; }
  currentUrl = url;
  setLoading(true, 'Capturing screenshot and running LLaVA analysis...');
  try {
    const data = await postJSON('/api/scan/screenshot', { url });
    renderResults(data, 'screenshot');
  } catch(e) { showError(e.message); } finally { setLoading(false); }
}

async function scanImage() {
  if (!imageFile) { shake($('image-dropzone')); return; }
  setLoading(true, 'Sending image to LLaVA for visual analysis...');
  try {
    const fd = new FormData();
    fd.append('file', imageFile);
    const resp = await fetch('/api/scan/image', { method: 'POST', body: fd });
    const data = await resp.json();
    if (data.error) throw new Error(data.error);
    renderResults(data, 'image');
  } catch(e) { showError(e.message); } finally { setLoading(false); }
}

async function scanQr() {
  if (!qrFile) { shake($('qr-dropzone')); return; }
  setLoading(true, 'Decoding QR and scanning URL...');
  try {
    const fd = new FormData();
    fd.append('file', qrFile);
    const resp = await fetch('/api/scan/qr', { method: 'POST', body: fd });
    const data = await resp.json();
    if (data.error) throw new Error(data.error);
    currentUrl = data.qr_url || '';
    renderResults(data, 'qr');
  } catch(e) { showError(e.message); } finally { setLoading(false); }
}

// ── Render Results ────────────────────────────────────────────────────────────
function renderResults(data, type) {
  $('results-section').classList.remove('hidden');
  $('results-section').scrollIntoView({ behavior: 'smooth', block: 'start' });

  let score = null, verdict = 'unknown', label = '—', sub = '';
  let scores = [], whois = null, screenshotB64 = null, finalUrl = null, hasRedirect = false, llavaText = null;

  if (type === 'url') {
    score = data.url_score;
    verdict = data.label || classify(score);
    label = verdict;
    whois = data.whois;
    scores = [
      { label: 'URL Score', score: data.url_score },
      { label: 'WHOIS Score', score: data.whois?.whois_score }
    ];
  } else if (type === 'url+ss') {
    const ur = data.url_result, sr = data.screenshot_result;
    score = ur.url_score;
    verdict = ur.label || classify(score);
    label = verdict;
    whois = ur.whois;
    screenshotB64 = sr?.screenshot_base64;
    finalUrl = sr?.final_url;
    hasRedirect = sr?.has_redirect;
    llavaText = sr?.llava_response;
    scores = [
      { label: 'URL Score', score: ur.url_score },
      { label: 'WHOIS Score', score: ur.whois?.whois_score },
      { label: 'Image Score', score: sr?.image_score }
    ];
  } else if (type === 'email') {
    score = data.email_score;
    verdict = data.label || classify(score);
    label = verdict;
    scores = [
      {
        label: 'Phishing Score',
        score: data.email_score,
        
        clsOverride: getScoreCls(data.email_score),   
        forceRed: true   
      },
      {
        label: 'Confidence',
        score: data.confidence,
        
        clsOverride: 'safe',
        verdictOverride: 'MODEL CERTAINTY'
      }
    ];
  } else if (type === 'screenshot') {
    score = data.image_score;
    verdict = classify(score);
    label = verdict;
    screenshotB64 = data.screenshot_base64;
    finalUrl = data.final_url;
    hasRedirect = data.has_redirect;
    llavaText = data.llava_response;
    scores = [{ label: 'Image Score', score: data.image_score }];
  } else if (type === 'image') {
    score = data.image_score;
    verdict = classify(score);
    label = verdict;
    screenshotB64 = data.screenshot_base64;
    llavaText = data.llava_response;
    scores = [{ label: 'Image Score', score: data.image_score }];
  } else if (type === 'qr') {
    score = data.url_score;
    verdict = data.label || classify(score);
    label = verdict;
    whois = data.whois;
    sub = data.qr_url ? `Decoded URL: ${data.qr_url}` : '';
    scores = [
      { label: 'URL Score', score: data.url_score },
      { label: 'WHOIS Score', score: data.whois?.whois_score }
    ];
  }

  const cls = normVerdict(verdict);

  
  const card = $('verdict-card');
  card.className = `verdict-card ${cls}`;
  const icons = { safe: '✓', suspicious: '?', phishing: '⚠', unknown: '·' };
  const iconWrap = $('verdict-icon-wrap');
  iconWrap.className = `verdict-icon-wrap ${cls}`;
  iconWrap.textContent = icons[cls] || '?';
  const vmain = $('verdict-main');
  vmain.className = `verdict-main ${cls}`;
  vmain.textContent = label.toUpperCase();
  $('verdict-sub').textContent = sub;

  
  const pct = score != null ? Math.round(score * 100) : null;
  $('ring-pct').textContent = pct != null ? pct + '%' : '—';
  const ring = $('score-ring');
  const circumference = 276.46;
  const offset = pct != null ? circumference - (pct / 100) * circumference : circumference;
  const ringColor = cls === 'phishing' ? '#c0392b' : cls === 'suspicious' ? '#f59e0b' : '#2d6a4f';
  ring.style.strokeDashoffset = circumference;
  ring.style.stroke = ringColor;
  setTimeout(() => { ring.style.strokeDashoffset = offset; }, 50);

  
  const reportBtn = $('btn-report');
  if (currentUrl) {
    reportBtn.classList.remove('hidden');
    reportBtn.classList.remove('reported');
    reportBtn.textContent = 'Report as Spam';
  } else {
    reportBtn.classList.add('hidden');
  }

  
  renderScoreCards(scores.filter(s => s.score != null));

  
  renderDetails(whois, data, type);

  
  if (screenshotB64) {
    $('screenshot-card').classList.remove('hidden');
    $('sc-img').src = `data:image/png;base64,${screenshotB64}`;
    if (hasRedirect && finalUrl) {
      $('redirect-badge').classList.remove('hidden');
      $('sc-meta').classList.remove('hidden');
      $('sc-meta').textContent = `Redirected to: ${finalUrl}`;
    } else {
      $('redirect-badge').classList.add('hidden');
      $('sc-meta').classList.add('hidden');
    }
    if (llavaText && llavaText !== 'null') {
      $('llava-box').classList.remove('hidden');
      $('llava-text').textContent = llavaText;
    } else {
      $('llava-box').classList.add('hidden');
    }
  } else {
    $('screenshot-card').classList.add('hidden');
  }
}

// ── Score Cards ───────────────────────────────────────────────────────────────

function renderScoreCards(scores) {
  const grid = $('scores-grid');
  grid.innerHTML = '';
  scores.forEach(({ label, score, clsOverride, verdictOverride, forceRed }) => {
    if (score == null) return;

    const pct = (score * 100).toFixed(1);
    const autoC = getScoreCls(score);

    
    const barCls = forceRed ? 'phishing' : (clsOverride || autoC);
    const valCls = forceRed ? 'phishing' : (clsOverride || autoC);
    const lblCls = clsOverride || autoC;  

    const verdictText = verdictOverride || (
      lblCls === 'phishing'   ? 'HIGH THREAT'  :
      lblCls === 'suspicious' ? 'SUSPICIOUS'   :
      forceRed                ? 'LOW THREAT'   : 
      'CLEAR'
    );

    const div = document.createElement('div');
    div.className = 'score-card';
    div.innerHTML = `
      <div class="sc-lbl">${label}</div>
      <div class="sc-val ${valCls}">${pct}%</div>
      <div class="sc-bar-bg"><div class="sc-bar ${barCls}" data-w="${pct}"></div></div>
      <div class="sc-verdict ${lblCls}">${verdictText}</div>`;
    grid.appendChild(div);
    setTimeout(() => { div.querySelector('.sc-bar').style.width = pct + '%'; }, 60);
  });
}

function renderDetails(whois, data, type) {
  const grid = $('details-grid');
  grid.innerHTML = '';

  if (whois) {
    const rows = [
      { k: 'Domain', v: whois.domain || '—' },
      { k: 'Registrar', v: whois.registrar || '—' },
      { k: 'Created', v: whois.creation_date ? whois.creation_date.split('T')[0] : '—' },
      { k: 'Age (days)', v: whois.age_days != null ? whois.age_days : '—', cls: whois.is_young_domain ? 'bad' : 'good' },
      { k: 'Young Domain', v: whois.is_young_domain ? 'YES — Suspicious' : 'No', cls: whois.is_young_domain ? 'bad' : 'good' },
    ];
    if (whois.error) rows.push({ k: 'WHOIS Error', v: whois.error, cls: 'warn' });
    grid.appendChild(makeDetailCard('Domain Intelligence (WHOIS)', rows));
  }

  if (data.features_used) {
    const f = data.features_used;
    grid.appendChild(makeDetailCard('URL Feature Analysis', [
      { k: 'URL Length', v: f.url_length },
      { k: 'HTTPS', v: f.has_https ? 'Yes' : 'No', cls: f.has_https ? 'good' : 'bad' },
      { k: 'Has IP Address', v: f.has_ip ? 'Yes' : 'No', cls: f.has_ip ? 'bad' : 'good' },
      { k: 'Subdomains', v: f.num_subdomains },
      { k: 'Entropy', v: f.url_entropy?.toFixed(3) },
      { k: 'Suspicious Words', v: f.has_suspicious_words ? 'Yes' : 'No', cls: f.has_suspicious_words ? 'bad' : 'good' },
      { k: 'Has @ Symbol', v: f.has_at ? 'Yes' : 'No', cls: f.has_at ? 'bad' : 'good' },
    ]));
  }

  // URL+SS combined
  if (type === 'url+ss' && data.url_result) {
    const f = data.url_result.features_used;
    if (f) {
      grid.appendChild(makeDetailCard('URL Feature Analysis', [
        { k: 'URL Length', v: f.url_length },
        { k: 'HTTPS', v: f.has_https ? 'Yes' : 'No', cls: f.has_https ? 'good' : 'bad' },
        { k: 'Has IP Address', v: f.has_ip ? 'Yes' : 'No', cls: f.has_ip ? 'bad' : 'good' },
        { k: 'Subdomains', v: f.num_subdomains },
        { k: 'Entropy', v: f.url_entropy?.toFixed(3) },
        { k: 'Suspicious Words', v: f.has_suspicious_words ? 'Yes' : 'No', cls: f.has_suspicious_words ? 'bad' : 'good' },
      ]));
    }
  }

  if (data.qr_url) {
    grid.appendChild(makeDetailCard('QR Code Decoded', [
      { k: 'Extracted URL', v: data.qr_url }
    ]));
  }
}

function makeDetailCard(title, rows) {
  const card = document.createElement('div');
  card.className = 'detail-card';
  card.innerHTML = `<div class="dc-title">${title}</div>` +
    rows.map(r => `<div class="dc-row"><span class="dc-key">${r.k}</span><span class="dc-val ${r.cls||''}">${trunc(String(r.v||'—'),32)}</span></div>`).join('');
  return card;
}

// ── Report as Spam ────────────────────────────────────────────────────────────
async function reportUrl() {
  if (!currentUrl) return;
  try {
    await postJSON('/api/report', { url: currentUrl });
    const btn = $('btn-report');
    btn.textContent = 'Reported ✓';
    btn.classList.add('reported');
    btn.disabled = true;
  } catch(e) { alert('Failed to report: ' + e.message); }
}

// ── History ───────────────────────────────────────────────────────────────────
async function loadHistory() {
  try {
    const history = await fetch('/api/history').then(r => r.json());
    const list = $('history-list');
    if (!history.length) {
      list.innerHTML = '<div class="empty-state">No scan history yet. Run your first scan above.</div>';
      return;
    }
    list.innerHTML = history.map(entry => {
      const r = entry.result || {};
      let score = r.url_score ?? r.email_score ?? r.image_score ?? null;
      if (!score && r.verdict) score = r.verdict.final_score;
      const label = r.label || (r.verdict?.verdict) || classify(score);
      const cls = normVerdict(label);
      const pct = score != null ? (score * 100).toFixed(0) + '%' : '—';
      const time = new Date(entry.timestamp).toLocaleString();
      return `<div class="history-item">
        <div class="hist-dot ${cls}"></div>
        <div class="hist-main">
          <div class="hist-target">${esc(entry.target)}</div>
          <div class="hist-meta">${time}</div>
        </div>
        <span class="hist-type">${entry.type.toUpperCase()}</span>
        <div class="hist-score ${cls}">${pct}</div>
      </div>`;
    }).join('');
  } catch(e) {
    $('history-list').innerHTML = '<div class="empty-state">Failed to load history.</div>';
  }
}

async function clearHistory() {
  if (!confirm('Clear all scan history?')) return;
  await postJSON('/api/history/clear', {});
  loadHistory();
}

// ── UI Helpers ────────────────────────────────────────────────────────────────
function setLoading(on, msg) {
  const el = $('loading');
  if (on) {
    $('loading-label').textContent = msg || 'Analyzing...';
    el.classList.remove('hidden');
    $('results-section').classList.add('hidden');
    $$('.btn-primary').forEach(b => b.disabled = true);
  } else {
    el.classList.add('hidden');
    $$('.btn-primary').forEach(b => b.disabled = false);
  }
}

function hideResults() {
  $('results-section').classList.add('hidden');
  $('loading').classList.add('hidden');
  $('reported-banner').classList.add('hidden');
}

function showError(msg) {
  $('results-section').classList.remove('hidden');
  const card = $('verdict-card');
  card.className = 'verdict-card phishing';
  $('verdict-icon-wrap').className = 'verdict-icon-wrap phishing';
  $('verdict-icon-wrap').textContent = '✗';
  $('verdict-main').className = 'verdict-main phishing';
  $('verdict-main').textContent = 'ERROR';
  $('verdict-sub').textContent = msg;
  $('scores-grid').innerHTML = '';
  $('details-grid').innerHTML = '';
  $('screenshot-card').classList.add('hidden');
  $('ring-pct').textContent = '—';
  $('btn-report').classList.add('hidden');
}

function shake(el) {
  el.style.animation = 'none';
  el.offsetHeight;
  el.style.animation = 'shake 0.4s ease';
  setTimeout(() => el.style.animation = '', 500);
}

// ── Utility ───────────────────────────────────────────────────────────────────
function classify(score) {
  if (score == null) return 'unknown';
  if (score >= 0.75) return 'phishing';
  if (score >= 0.5) return 'suspicious';
  return 'safe';
}
function normVerdict(v) {
  if (!v) return 'unknown';
  v = v.toLowerCase();
  if (v === 'phishing') return 'phishing';
  if (v === 'suspicious') return 'suspicious';
  if (v === 'safe') return 'safe';
  return 'unknown';
}
function getScoreCls(s) {
  if (s == null) return 'na';
  if (s >= 0.75) return 'phishing';
  if (s >= 0.5) return 'suspicious';
  return 'safe';
}
function trunc(s, n) { return s && s.length > n ? s.slice(0, n) + '…' : (s || '—'); }
function esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

async function postJSON(url, body) {
  const r = await fetch(url, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body) });
  const d = await r.json();
  if (d.error) throw new Error(d.error);
  return d;
}


const st = document.createElement('style');
st.textContent = '@keyframes shake{0%,100%{transform:translateX(0)}25%{transform:translateX(-8px)}75%{transform:translateX(8px)}}';
document.head.appendChild(st);