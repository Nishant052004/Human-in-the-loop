// HAULT Human-in-the-Loop DevOps Command Suite - Frontend Application Logic

let currentTab = 'console';
let currentPipelineResult = null;
let currentActiveAssetTab = 'docker';
let currentModalAssetTab = 'docker';
let selectedApprovalId = null;
let selectedVisionFile = null;

// Chart.js instances
let chartQuality = null;
let chartResponse = null;
let chartCost = null;
let chartDecisions = null;

document.addEventListener('DOMContentLoaded', () => {
  // Initialize Lucide icons
  if (window.lucide) lucide.createIcons();

  // Setup Vision image dropzone
  setupVisionDropzone();

  // Load system status and default counts
  refreshSystemStatus();

  // Load preset by default
  loadPreset('fastapi');

  // DB Menu toggle
  const dbBtn = document.getElementById('btn-db-menu');
  const dbDropdown = document.getElementById('db-menu-dropdown');
  if (dbBtn && dbDropdown) {
    dbBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      dbDropdown.classList.toggle('hidden');
    });
    document.addEventListener('click', () => {
      dbDropdown.classList.add('hidden');
    });
  }
});

// ==========================================
// NAVIGATION & TABS
// ==========================================
function switchTab(tabId) {
  currentTab = tabId;
  document.querySelectorAll('.tab-view').forEach(el => el.classList.add('hidden'));
  document.querySelectorAll('.nav-tab').forEach(el => el.classList.remove('nav-tab-active'));

  const view = document.getElementById(`view-${tabId}`);
  const btn = document.getElementById(`tab-btn-${tabId}`);

  if (view) view.classList.remove('hidden');
  if (btn) btn.classList.add('nav-tab-active');

  if (tabId === 'queue') {
    loadApprovalsQueue();
  } else if (tabId === 'memory') {
    loadPreferences();
    loadKnowledgeBase();
  } else if (tabId === 'analytics') {
    loadAnalytics();
  } else if (tabId === 'blockchain') {
    loadBlockchainLedger();
  }

  if (window.lucide) lucide.createIcons();
}

function switchAssetTab(assetType) {
  currentActiveAssetTab = assetType;
  const types = ['docker', 'k8s', 'cicd'];
  types.forEach(t => {
    const v = document.getElementById(`asset-view-${t}`);
    const b = document.getElementById(`btn-tab-${t}`);
    if (t === assetType) {
      if (v) v.classList.remove('hidden');
      if (b) {
        b.className = "px-3.5 py-1.5 rounded-lg text-xs font-bold font-mono bg-teal-500/20 text-teal-400 border border-teal-500/40";
      }
    } else {
      if (v) v.classList.add('hidden');
      if (b) {
        b.className = "px-3.5 py-1.5 rounded-lg text-xs font-bold font-mono text-slate-400 hover:text-slate-200 border border-transparent";
      }
    }
  });
}

function switchModalCodeTab(tabType) {
  currentModalAssetTab = tabType;
  const tabs = ['docker', 'k8s', 'cicd'];
  tabs.forEach(t => {
    const v = document.getElementById(`mcode-view-${t}`);
    const b = document.getElementById(`mcode-tab-${t}`);
    if (t === tabType) {
      if (v) v.classList.remove('hidden');
      if (b) b.className = "px-3 py-1 rounded text-xs font-mono font-bold bg-teal-500/20 text-teal-400 border border-teal-500/40";
    } else {
      if (v) v.classList.add('hidden');
      if (b) b.className = "px-3 py-1 rounded text-xs font-mono font-bold text-slate-400 hover:text-slate-200 border border-transparent";
    }
  });
}

function switchMemorySubTab(subTab) {
  const pView = document.getElementById('subview-prefs');
  const rView = document.getElementById('subview-rag');
  const pBtn = document.getElementById('subtab-btn-prefs');
  const rBtn = document.getElementById('subtab-btn-rag');

  if (subTab === 'prefs') {
    pView.classList.remove('hidden');
    rView.classList.add('hidden');
    pBtn.className = "px-4 py-2 rounded-lg text-xs font-bold font-mono bg-teal-500/20 text-teal-400 border border-teal-500/40";
    rBtn.className = "px-4 py-2 rounded-lg text-xs font-bold font-mono text-slate-400 hover:text-slate-200 border border-transparent";
    loadPreferences();
  } else {
    pView.classList.add('hidden');
    rView.classList.remove('hidden');
    rBtn.className = "px-4 py-2 rounded-lg text-xs font-bold font-mono bg-teal-500/20 text-teal-400 border border-teal-500/40";
    pBtn.className = "px-4 py-2 rounded-lg text-xs font-bold font-mono text-slate-400 hover:text-slate-200 border border-transparent";
    loadKnowledgeBase();
  }
}

// ==========================================
// PRESET REQUIREMENTS
// ==========================================
function loadPreset(presetKey) {
  const input = document.getElementById('input-desc');
  if (presetKey === 'fastapi') {
    input.value = "Python FastAPI app running on port 8000, requires a PostgreSQL database, health checks on /health, and build workflow on pull requests.";
  } else if (presetKey === 'nodejs') {
    input.value = "NodeJS Express REST microservice running on port 3000, requires Redis caching, yarn package manager, and Docker multi-stage build.";
  } else if (presetKey === 'go') {
    input.value = "Go 1.20 authentication API service running on port 8080, minimal alpine container, internal routing, metrics on /metrics.";
  }
}

// ==========================================
// VISION DROPZONE SETUP
// ==========================================
function setupVisionDropzone() {
  const dropzone = document.getElementById('vision-dropzone');
  const fileInput = document.getElementById('input-image');
  const preview = document.getElementById('vision-preview');
  const placeholder = document.getElementById('vision-placeholder');
  const previewContainer = document.getElementById('vision-preview-container');

  if (!dropzone || !fileInput) return;

  dropzone.addEventListener('click', (e) => {
    if (e.target.tagName !== 'BUTTON') fileInput.click();
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files && fileInput.files[0]) {
      handleVisionFile(fileInput.files[0]);
    }
  });

  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('border-teal-500', 'bg-teal-500/10');
  });

  dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('border-teal-500', 'bg-teal-500/10');
  });

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('border-teal-500', 'bg-teal-500/10');
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleVisionFile(e.dataTransfer.files[0]);
    }
  });

  function handleVisionFile(file) {
    selectedVisionFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
      preview.src = e.target.result;
      placeholder.classList.add('hidden');
      previewContainer.classList.remove('hidden');
      showToast("Architecture diagram attached for vision planner.", "info");
    };
    reader.readAsDataURL(file);
  }
}

function removeVisionImage(e) {
  if (e) e.stopPropagation();
  selectedVisionFile = null;
  document.getElementById('input-image').value = '';
  document.getElementById('vision-preview').src = '';
  document.getElementById('vision-placeholder').classList.remove('hidden');
  document.getElementById('vision-preview-container').classList.add('hidden');
}

// ==========================================
// GITHUB REPO INSPECTION
// ==========================================
async function inspectGitHubRepo() {
  const repoInput = document.getElementById('input-repo');
  const repo = repoInput.value.trim();
  if (!repo) {
    showToast("Please enter a GitHub repository (e.g. pallets/flask).", "error");
    return;
  }

  const btn = document.getElementById('btn-inspect-repo');
  btn.disabled = true;
  btn.innerHTML = `<i data-lucide="loader-2" class="w-3.5 h-3.5 animate-spin"></i> Reading...`;
  if (window.lucide) lucide.createIcons();

  try {
    const res = await fetch('/api/github/readme', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repo })
    });
    const data = await res.json();
    if (data.success) {
      document.getElementById('repo-status-pill').classList.remove('hidden');
      showToast(`Repository README loaded into planner context.`, "success");
    } else {
      showToast(data.detail || "Failed to inspect repository.", "error");
    }
  } catch (err) {
    showToast("Error inspecting repository: " + err.message, "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i data-lucide="search" class="w-3.5 h-3.5"></i> Inspect`;
    if (window.lucide) lucide.createIcons();
  }
}

// ==========================================
// TRIGGER MULTI-AGENT PIPELINE
// ==========================================
async function triggerPipeline() {
  const desc = document.getElementById('input-desc').value.trim();
  if (!desc) {
    showToast("Please specify project requirements.", "error");
    return;
  }

  const btn = document.getElementById('btn-run-pipeline');
  const progressContainer = document.getElementById('pipeline-progress-container');
  const progressStatus = document.getElementById('pipeline-progress-status');
  const resultsContainer = document.getElementById('pipeline-results-container');

  btn.disabled = true;
  btn.classList.add('opacity-75');
  progressContainer.classList.remove('hidden');
  resultsContainer.classList.add('hidden');

  // Step indicator simulation
  let step = 1;
  const stepInterval = setInterval(() => {
    if (step <= 6) {
      const stepEl = document.getElementById(`step-${step}`);
      if (stepEl) {
        stepEl.className = "p-2.5 rounded-lg bg-teal-500/20 border border-teal-500/50 text-teal-300 font-bold";
      }
      if (step === 1) progressStatus.textContent = "Querying RAG & Preference Memory...";
      if (step === 2) progressStatus.textContent = "Planner Agent analyzing architecture...";
      if (step === 3) progressStatus.textContent = "Coding Agent writing Dockerfile, K8s & CI/CD...";
      if (step === 4) progressStatus.textContent = "Critic Agent performing security check...";
      if (step === 5) progressStatus.textContent = "Sandbox executing pre-flight linting...";
      if (step === 6) progressStatus.textContent = "Scorer evaluating risk & routing...";
      step++;
    }
  }, 1200);

  const formData = new FormData();
  formData.append('project_description', desc);

  const repo = document.getElementById('input-repo').value.trim();
  if (repo) formData.append('repo_name', repo);

  const audioInput = document.getElementById('input-audio');
  if (audioInput && audioInput.files && audioInput.files[0]) {
    formData.append('voice_pref', "EXPOSE internal port. Prefer lightweight alpine build. Restrict non-root context.");
  }

  if (selectedVisionFile) {
    formData.append('image', selectedVisionFile);
  }

  try {
    const res = await fetch('/api/pipeline/run', {
      method: 'POST',
      body: formData
    });
    const result = await res.json();
    clearInterval(stepInterval);

    if (result.success && result.data) {
      currentPipelineResult = result.data;
      currentPipelineResult.project_name = desc.substring(0, 50);

      renderPipelineResults(result.data);
      showToast("Multi-Agent Pipeline finished successfully!", "success");
      refreshSystemStatus();
    } else {
      showToast(result.detail || "Pipeline execution failed.", "error");
    }
  } catch (err) {
    clearInterval(stepInterval);
    showToast("Pipeline error: " + err.message, "error");
  } finally {
    btn.disabled = false;
    btn.classList.remove('opacity-75');
    progressContainer.classList.add('hidden');
    // Reset steps
    for (let i = 1; i <= 6; i++) {
      const s = document.getElementById(`step-${i}`);
      if (s) s.className = "p-2.5 rounded-lg bg-slate-800/60 border border-slate-700/60 text-slate-400";
    }
  }
}

// ==========================================
// RENDER PIPELINE RESULTS
// ==========================================
function renderPipelineResults(res) {
  const container = document.getElementById('pipeline-results-container');
  container.classList.remove('hidden');

  // Explainable Quality Scores
  setGauge('conf', res.confidence_score);
  setGauge('comp', res.completeness_score);
  setGauge('sec', res.security_score);
  setGauge('read', res.readability_score);
  setGauge('shield', 100 - (res.hallucination_score || 0));

  // Dynamic 3-Tier Escalation Banner
  const conf = res.confidence_score;
  const risk = res.risk_level;
  const banner = document.getElementById('escalation-banner');
  const badge = document.getElementById('escalation-badge');
  const label = document.getElementById('escalation-level-label');
  const msg = document.getElementById('escalation-message');
  const iconBox = document.getElementById('escalation-icon-box');

  let reviewerLevel = "Junior/Senior Review";

  if (conf >= 90 && risk === "Low") {
    reviewerLevel = "Auto-Approved";
    banner.className = "rounded-2xl p-5 border border-emerald-500/40 bg-emerald-500/10 flex flex-col sm:flex-row sm:items-center justify-between gap-4";
    iconBox.className = "w-12 h-12 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0";
    badge.className = "px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider font-mono bg-emerald-500/20 text-emerald-300 border border-emerald-500/40";
    badge.textContent = "🟢 AUTO-APPROVED";
    label.textContent = "Tier 1: High Confidence (≥90%), Low Risk (≤20%)";
    msg.textContent = "Autonomous deployment permitted. Configurations satisfy all security guardrails without requiring manual intervention.";
  } else if (conf >= 70 || risk === "Medium") {
    reviewerLevel = "Junior/Senior Review";
    banner.className = "rounded-2xl p-5 border border-amber-500/40 bg-amber-500/10 flex flex-col sm:flex-row sm:items-center justify-between gap-4";
    iconBox.className = "w-12 h-12 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center shrink-0";
    badge.className = "px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider font-mono bg-amber-500/20 text-amber-300 border border-amber-500/40";
    badge.textContent = "🟡 HUMAN REVIEW REQUIRED";
    label.textContent = "Tier 2: Moderate Confidence (70–89%) or Medium Risk";
    msg.textContent = "Queued for audit verification. Review base image specifications and cluster service routings before sign-off.";
  } else {
    reviewerLevel = "Domain Expert";
    banner.className = "rounded-2xl p-5 border border-rose-500/40 bg-rose-500/10 flex flex-col sm:flex-row sm:items-center justify-between gap-4";
    iconBox.className = "w-12 h-12 rounded-xl bg-rose-500/20 text-rose-400 flex items-center justify-center shrink-0";
    badge.className = "px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider font-mono bg-rose-500/20 text-rose-300 border border-rose-500/40";
    badge.textContent = "🔴 EXPERT ESCALATION";
    label.textContent = "Tier 3: Low Confidence (<70%) or High Risk (>50%)";
    msg.textContent = "Escalated directly to Principal Security Architects. Potential privilege boundary or unpinned dependencies detected.";
  }

  currentPipelineResult.calculated_reviewer_level = reviewerLevel;

  // Sandbox simulation logs
  const sbLogs = document.getElementById('sandbox-logs');
  sbLogs.textContent = res.simulation_logs || "Simulation checks executed.";
  const sbBadge = document.getElementById('sandbox-badge');
  if (res.simulation_passed) {
    sbBadge.className = "px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-emerald-500/20 text-emerald-400 border border-emerald-500/40";
    sbBadge.textContent = "PASSED";
  } else {
    sbBadge.className = "px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-rose-500/20 text-rose-400 border border-rose-500/40";
    sbBadge.textContent = "FAILED";
  }

  // AI Help Request notice
  const helpNotice = document.getElementById('needs-help-notice');
  const helpText = document.getElementById('needs-help-text');
  if (res.needs_help_reason) {
    helpNotice.classList.remove('hidden');
    helpText.textContent = res.needs_help_reason;
  } else {
    helpNotice.classList.add('hidden');
  }

  // Code files
  document.getElementById('code-dockerfile').textContent = res.dockerfile || "";
  document.getElementById('code-k8s').textContent = res.kubernetes_yaml || "";
  document.getElementById('code-cicd').textContent = res.cicd_yaml || "";
  document.getElementById('code-pipeline-logs').textContent = res.pipeline_log || "";

  // Highlight Prism
  if (window.Prism) Prism.highlightAll();
  if (window.lucide) lucide.createIcons();

  // Scroll to results smoothly
  container.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function setGauge(name, value) {
  const v = Math.min(100, Math.max(0, Math.round(value || 0)));
  const textEl = document.getElementById(`score-${name}`);
  const barEl = document.getElementById(`bar-${name}`);
  if (textEl) textEl.textContent = `${v}%`;
  if (barEl) barEl.style.width = `${v}%`;
}

// Copy Code
function copyCurrentAssetCode() {
  if (!currentPipelineResult) return;
  let code = "";
  if (currentActiveAssetTab === 'docker') code = currentPipelineResult.dockerfile;
  if (currentActiveAssetTab === 'k8s') code = currentPipelineResult.kubernetes_yaml;
  if (currentActiveAssetTab === 'cicd') code = currentPipelineResult.cicd_yaml;

  navigator.clipboard.writeText(code).then(() => {
    showToast("Code copied to clipboard!", "success");
  });
}

// Download File
function downloadCurrentAssetCode() {
  if (!currentPipelineResult) return;
  let filename = "Dockerfile";
  let content = currentPipelineResult.dockerfile;

  if (currentActiveAssetTab === 'k8s') {
    filename = "kubernetes.yaml";
    content = currentPipelineResult.kubernetes_yaml;
  } else if (currentActiveAssetTab === 'cicd') {
    filename = "ci-cd.yml";
    content = currentPipelineResult.cicd_yaml;
  }

  const blob = new Blob([content], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

// ==========================================
// HITL ACTIONS: QUEUE & INSTANT APPROVE
// ==========================================
async function queueCurrentPipelineResult() {
  if (!currentPipelineResult) return;

  const payload = {
    project_name: currentPipelineResult.project_name || "New Infrastructure Project",
    risk_level: currentPipelineResult.risk_level || "Low",
    confidence_score: currentPipelineResult.confidence_score || 90.0,
    reviewer_level: currentPipelineResult.calculated_reviewer_level || "Junior/Senior Review",
    dockerfile: currentPipelineResult.dockerfile,
    kubernetes_yaml: currentPipelineResult.kubernetes_yaml,
    cicd_yaml: currentPipelineResult.cicd_yaml,
    explanation: currentPipelineResult.explanation || "Generated via HAULT Agent Console.",
    completeness: currentPipelineResult.completeness_score,
    security: currentPipelineResult.security_score,
    readability: currentPipelineResult.readability_score,
    hallucination: currentPipelineResult.hallucination_score
  };

  try {
    const res = await fetch('/api/approvals', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.success) {
      showToast("Project added to review queue!", "success");
      refreshSystemStatus();
    }
  } catch (err) {
    showToast("Failed to queue project: " + err.message, "error");
  }
}

async function instantApproveCurrentResult() {
  if (!currentPipelineResult) return;

  const payload = {
    project_name: currentPipelineResult.project_name || "Instant Project",
    risk_level: currentPipelineResult.risk_level || "Low",
    confidence_score: currentPipelineResult.confidence_score || 95.0,
    dockerfile: currentPipelineResult.dockerfile,
    kubernetes_yaml: currentPipelineResult.kubernetes_yaml,
    cicd_yaml: currentPipelineResult.cicd_yaml,
    explanation: currentPipelineResult.explanation || "Instant developer sign-off.",
    evidence: currentPipelineResult.evidence || "Direct commit",
    completeness: currentPipelineResult.completeness_score,
    security: currentPipelineResult.security_score,
    readability: currentPipelineResult.readability_score,
    hallucination: currentPipelineResult.hallucination_score
  };

  try {
    const res = await fetch('/api/approvals/instant-approve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.success) {
      showToast(`Deployment signed! Blockchain Hash: ${data.audit_hash.substring(0, 16)}...`, "success");
      refreshSystemStatus();
      // Prompt download
      if (data.pdf_download_url) {
        window.open(data.pdf_download_url, '_blank');
      }
    }
  } catch (err) {
    showToast("Error approving deployment: " + err.message, "error");
  }
}

// ==========================================
// AUDITOR APPROVAL QUEUE
// ==========================================
let allApprovals = [];
let currentQueueFilter = 'all';

async function loadApprovalsQueue() {
  const grid = document.getElementById('approvals-grid');
  const empty = document.getElementById('queue-empty-state');
  grid.innerHTML = `<div class="col-span-full py-12 text-center text-xs text-slate-400 font-mono"><i data-lucide="loader-2" class="w-6 h-6 animate-spin mx-auto mb-2 text-teal-400"></i>Loading approvals...</div>`;
  if (window.lucide) lucide.createIcons();

  try {
    const res = await fetch('/api/approvals');
    const data = await res.json();
    allApprovals = data.approvals || [];
    renderApprovalsGrid();
  } catch (err) {
    showToast("Failed to load approvals: " + err.message, "error");
  }
}

function filterQueue(status) {
  currentQueueFilter = status;
  ['all', 'pending', 'approved', 'rejected'].forEach(s => {
    const b = document.getElementById(`qfilter-${s}`);
    if (b) {
      b.className = (s === status.toLowerCase() || (s === 'all' && status === 'all') || (s === 'pending' && status === 'Pending Review'))
        ? "px-3 py-1 rounded bg-teal-500/20 text-teal-300 font-medium"
        : "px-3 py-1 rounded text-slate-400 hover:text-white";
    }
  });
  renderApprovalsGrid();
}

function searchQueue(query) {
  const q = query.toLowerCase().trim();
  renderApprovalsGrid(q);
}

function renderApprovalsGrid(filterText = "") {
  const grid = document.getElementById('approvals-grid');
  const empty = document.getElementById('queue-empty-state');

  let filtered = allApprovals;
  if (currentQueueFilter !== 'all') {
    filtered = filtered.filter(a => a.status === currentQueueFilter);
  }
  if (filterText) {
    filtered = filtered.filter(a => (a.project_name || "").toLowerCase().includes(filterText));
  }

  if (filtered.length === 0) {
    grid.innerHTML = "";
    empty.classList.remove('hidden');
    return;
  }

  empty.classList.add('hidden');
  grid.innerHTML = filtered.map(app => {
    const isApproved = app.status === 'Approved';
    const isRejected = app.status === 'Rejected';
    const statusClass = isApproved ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' :
                        isRejected ? 'bg-rose-500/20 text-rose-400 border-rose-500/30' :
                        'bg-amber-500/20 text-amber-400 border-amber-500/30';

    return `
      <div class="glass-panel rounded-2xl p-5 flex flex-col justify-between space-y-4 hover:border-teal-500/40 transition">
        <div>
          <div class="flex items-center justify-between mb-2">
            <span class="text-[10px] font-mono px-2 py-0.5 rounded-full border ${statusClass}">${app.status}</span>
            <span class="text-[10px] text-slate-500 font-mono">${app.timestamp || ""}</span>
          </div>
          <h4 class="text-sm font-bold text-white font-mono truncate" title="${app.project_name}">${app.project_name}</h4>
          <p class="text-xs text-slate-400 mt-1 line-clamp-2">${app.explanation || "No explanation recorded."}</p>
        </div>

        <div class="pt-3 border-t border-slate-800 space-y-3">
          <div class="flex justify-between text-xs font-mono">
            <span class="text-slate-400">Confidence: <b class="text-teal-400">${app.confidence_score}%</b></span>
            <span class="text-slate-400">Risk: <b class="text-slate-200">${app.risk_score}</b></span>
          </div>
          <div class="text-[11px] text-slate-500 font-mono">
            Required: <span class="text-slate-300 font-semibold">${app.reviewer_level || "Review"}</span>
          </div>
          <div class="flex gap-2">
            <button onclick="openAuditorModal(${app.id})" class="flex-1 py-2 bg-teal-600/20 hover:bg-teal-600/30 text-teal-300 border border-teal-500/40 text-xs font-bold font-mono rounded-xl transition flex items-center justify-center gap-1.5">
              <i data-lucide="edit-3" class="w-3.5 h-3.5"></i> Audit & Edit
            </button>
            <a href="/api/report/${app.id}/pdf" target="_blank" class="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 rounded-xl" title="Download Signed PDF">
              <i data-lucide="file-text" class="w-4 h-4"></i>
            </a>
          </div>
        </div>
      </div>
    `;
  }).join('');

  if (window.lucide) lucide.createIcons();
}

// ==========================================
// AUDITOR WORKSPACE MODAL
// ==========================================
async function openAuditorModal(appId) {
  selectedApprovalId = appId;
  const modal = document.getElementById('modal-auditor');
  modal.classList.remove('hidden');

  try {
    const res = await fetch(`/api/approvals/${appId}`);
    const data = await res.json();

    document.getElementById('modal-project-title').textContent = data.project_name || "Project Review";
    document.getElementById('modal-project-meta').textContent = `ID #${data.id} • ${data.status} • Logged at ${data.timestamp}`;
    document.getElementById('modal-required-level').textContent = data.reviewer_level || "Standard";
    document.getElementById('modal-conf-risk').textContent = `${data.confidence_score}% Conf / Risk: ${data.risk_score}`;
    document.getElementById('modal-explanation').textContent = data.explanation || "Ready for human audit.";

    document.getElementById('modal-edit-docker').value = data.docker_code || "";
    document.getElementById('modal-edit-k8s').value = data.k8s_code || "";
    document.getElementById('modal-edit-cicd').value = data.cicd_code || "";
    document.getElementById('modal-correction-reason').value = "";
    document.getElementById('modal-pdf-download-link').href = `/api/report/${data.id}/pdf`;

    switchModalCodeTab('docker');
    if (window.lucide) lucide.createIcons();
  } catch (err) {
    showToast("Error loading project audit details: " + err.message, "error");
  }
}

function closeAuditorModal() {
  document.getElementById('modal-auditor').classList.add('hidden');
  selectedApprovalId = null;
}

async function submitAuditorAction(action) {
  if (!selectedApprovalId) return;

  const role = document.getElementById('modal-persona-select').value;
  const dockerCode = document.getElementById('modal-edit-docker').value;
  const k8sCode = document.getElementById('modal-edit-k8s').value;
  const cicdCode = document.getElementById('modal-edit-cicd').value;
  const reason = document.getElementById('modal-correction-reason').value.trim();

  const payload = {
    action,
    reviewer_role: role,
    docker_code: dockerCode,
    k8s_code: k8sCode,
    cicd_code: cicdCode,
    reason
  };

  try {
    const res = await fetch(`/api/approvals/${selectedApprovalId}/action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (data.success) {
      if (action === 'approve') {
        showToast(`Deployment approved! Hash: ${data.audit_hash.substring(0, 16)}...`, "success");
        if (data.preference_extracted) {
          showToast(`🧠 Preference Learned: ${data.preference_extracted.pref_key} = ${data.preference_extracted.pref_value}`, "info");
        }
      } else {
        showToast("Deployment rejected and sealed to blockchain.", "error");
      }
      closeAuditorModal();
      loadApprovalsQueue();
      refreshSystemStatus();
    } else {
      showToast(data.detail || "Action failed.", "error");
    }
  } catch (err) {
    showToast("Error processing auditor action: " + err.message, "error");
  }
}

// ==========================================
// PREFERENCE MEMORY
// ==========================================
async function loadPreferences() {
  const tbody = document.getElementById('preferences-tbody');
  tbody.innerHTML = `<tr><td colspan="6" class="p-4 text-center text-slate-500 font-mono">Loading learned rules...</td></tr>`;

  try {
    const res = await fetch('/api/preferences');
    const data = await res.json();
    const prefs = data.preferences || [];

    if (prefs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="p-6 text-center text-slate-500">No preference rules in memory yet. Edit code during audits to trigger learning.</td></tr>`;
      return;
    }

    tbody.innerHTML = prefs.map(p => `
      <tr class="hover:bg-slate-800/40 font-mono text-xs">
        <td class="p-3.5 text-slate-500">#${p.id}</td>
        <td class="p-3.5 font-bold text-teal-300">${p.pref_key}</td>
        <td class="p-3.5 text-slate-200 bg-slate-900/60 rounded px-2">${p.pref_value}</td>
        <td class="p-3.5 text-slate-400 font-sans text-xs">${p.description || ""}</td>
        <td class="p-3.5 text-slate-500 text-[11px]">${p.timestamp || ""}</td>
        <td class="p-3.5 text-right">
          <button onclick="deletePreference(${p.id})" class="text-rose-400 hover:text-rose-300 p-1" title="Delete Rule">
            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
          </button>
        </td>
      </tr>
    `).join('');

    if (window.lucide) lucide.createIcons();
  } catch (err) {
    showToast("Failed to load preferences: " + err.message, "error");
  }
}

function openAddPreferenceModal() {
  document.getElementById('modal-add-pref').classList.remove('hidden');
}
function closeAddPreferenceModal() {
  document.getElementById('modal-add-pref').classList.add('hidden');
}

async function submitNewPreference() {
  const key = document.getElementById('new-pref-key').value.trim();
  const val = document.getElementById('new-pref-value').value.trim();
  const desc = document.getElementById('new-pref-desc').value.trim();

  if (!key || !val) {
    showToast("Please enter rule key and value.", "error");
    return;
  }

  try {
    const res = await fetch('/api/preferences', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pref_key: key, pref_value: val, description: desc })
    });
    const data = await res.json();
    if (data.success) {
      showToast("Custom rule injected into AI memory!", "success");
      closeAddPreferenceModal();
      loadPreferences();
      refreshSystemStatus();
    }
  } catch (err) {
    showToast("Failed to save preference: " + err.message, "error");
  }
}

async function deletePreference(prefId) {
  try {
    const res = await fetch(`/api/preferences/${prefId}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.success) {
      showToast("Rule removed from memory.", "info");
      loadPreferences();
      refreshSystemStatus();
    }
  } catch (err) {
    showToast("Failed to delete rule: " + err.message, "error");
  }
}

// ==========================================
// RAG KNOWLEDGE BASE
// ==========================================
async function loadKnowledgeBase() {
  const grid = document.getElementById('kb-grid');
  grid.innerHTML = `<div class="col-span-full py-8 text-center text-xs text-slate-500 font-mono">Loading RAG knowledge base...</div>`;

  try {
    const res = await fetch('/api/knowledge-base');
    const data = await res.json();
    const items = data.knowledge_base || [];

    if (items.length === 0) {
      grid.innerHTML = `<div class="col-span-full py-8 text-center text-slate-500">No RAG templates recorded yet. Approving deployments populates templates.</div>`;
      return;
    }

    grid.innerHTML = items.map(kb => `
      <div class="glass-panel rounded-2xl p-5 flex flex-col justify-between space-y-3">
        <div>
          <div class="flex items-center justify-between mb-2">
            <span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
              Rating: ${kb.rating}%
            </span>
            <span class="text-[10px] text-slate-500 font-mono">${kb.timestamp || ""}</span>
          </div>
          <h4 class="text-sm font-bold text-white font-mono">${kb.project_name}</h4>
          <p class="text-xs text-slate-400 mt-1 line-clamp-2">${kb.project_description || ""}</p>
        </div>
        <button onclick="inspectRagTemplate(${kb.id})" class="w-full py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono font-bold rounded-xl transition flex items-center justify-center gap-1.5 border border-slate-700">
          <i data-lucide="eye" class="w-3.5 h-3.5"></i> Inspect Code Template
        </button>
      </div>
    `).join('');

    if (window.lucide) lucide.createIcons();
  } catch (err) {
    showToast("Failed to load knowledge base: " + err.message, "error");
  }
}

async function inspectRagTemplate(kbId) {
  const modal = document.getElementById('modal-view-rag');
  modal.classList.remove('hidden');

  try {
    const res = await fetch(`/api/knowledge-base/${kbId}`);
    const data = await res.json();

    document.getElementById('rag-modal-title').textContent = data.project_name || "Template";
    const fullCode = `# --- Dockerfile ---\n${data.docker_code}\n\n# --- Kubernetes Manifest ---\n${data.k8s_code}\n\n# --- CI/CD Actions ---\n${data.cicd_code}`;
    const codeEl = document.getElementById('rag-modal-code');
    codeEl.textContent = fullCode;
    if (window.Prism) Prism.highlightElement(codeEl);
  } catch (err) {
    showToast("Error inspecting template: " + err.message, "error");
  }
}

function closeRagModal() {
  document.getElementById('modal-view-rag').classList.add('hidden');
}

// ==========================================
// TELEMETRY & ANALYTICS CHARTS
// ==========================================
async function loadAnalytics() {
  try {
    const res = await fetch('/api/analytics');
    const data = await res.json();

    // KPI Cards
    const kpi = data.kpi || {};
    document.getElementById('kpi-total-runs').textContent = kpi.total_runs || 0;
    document.getElementById('kpi-success-rate').textContent = `${kpi.success_rate || 0}%`;
    document.getElementById('kpi-approved-count').textContent = `${kpi.approved_runs || 0} approved`;
    document.getElementById('kpi-corrections').textContent = kpi.correction_count || 0;
    document.getElementById('kpi-saved-hours').textContent = `${kpi.saved_hours || 0} hrs`;

    // Render Charts
    renderAnalyticsCharts(data);

    // Feedback history table
    const fbTbody = document.getElementById('feedback-tbody');
    const fb = data.feedback_history || [];
    if (fb.length === 0) {
      fbTbody.innerHTML = `<tr><td colspan="5" class="p-4 text-center text-slate-500">No human corrections logged yet.</td></tr>`;
    } else {
      fbTbody.innerHTML = fb.map(f => `
        <tr class="hover:bg-slate-800/40 font-mono text-xs">
          <td class="p-3 text-white font-bold">${f.project_name}</td>
          <td class="p-3 text-slate-400 font-mono max-w-xs truncate" title="${f.original_docker}">${f.original_docker.substring(0, 40)}...</td>
          <td class="p-3 text-teal-300 font-mono max-w-xs truncate" title="${f.corrected_docker}">${f.corrected_docker.substring(0, 40)}...</td>
          <td class="p-3 text-slate-300 font-sans text-xs">${f.reason}</td>
          <td class="p-3 text-slate-500 text-[11px]">${f.timestamp}</td>
        </tr>
      `).join('');
    }
  } catch (err) {
    showToast("Failed to load analytics: " + err.message, "error");
  }
}

function renderAnalyticsCharts(data) {
  const series = data.metrics_series || [];
  const labels = series.map((s, idx) => s.timestamp ? s.timestamp.substring(5, 16) : `Run ${idx+1}`);

  // Chart 1: Quality & Hallucination Trend
  const ctxQuality = document.getElementById('chart-quality-trend');
  if (ctxQuality) {
    if (chartQuality) chartQuality.destroy();
    chartQuality = new Chart(ctxQuality, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Accuracy Index (%)',
            data: series.map(s => s.accuracy_score || 90),
            borderColor: '#10B981',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            tension: 0.3,
            fill: true
          },
          {
            label: 'Hallucination Risk (%)',
            data: series.map(s => s.hallucination_score || 5),
            borderColor: '#F43F5E',
            backgroundColor: 'transparent',
            tension: 0.3
          }
        ]
      },
      options: chartDefaultOptions()
    });
  }

  // Chart 2: Response Speed
  const ctxResp = document.getElementById('chart-response-time');
  if (ctxResp) {
    if (chartResponse) chartResponse.destroy();
    chartResponse = new Chart(ctxResp, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Response Time (s)',
          data: series.map(s => s.response_time || 5),
          backgroundColor: '#06B6D4',
          borderRadius: 6
        }]
      },
      options: chartDefaultOptions()
    });
  }

  // Chart 3: AI Cost
  const ctxCost = document.getElementById('chart-token-cost');
  if (ctxCost) {
    if (chartCost) chartCost.destroy();
    let cumulative = 0;
    const costData = series.map(s => {
      cumulative += (s.cost || 0.0005);
      return Math.round(cumulative * 10000) / 10000;
    });
    chartCost = new Chart(ctxCost, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Cumulative Cost ($)',
          data: costData,
          borderColor: '#10B981',
          backgroundColor: 'rgba(16, 185, 129, 0.15)',
          fill: true,
          tension: 0.3
        }]
      },
      options: chartDefaultOptions()
    });
  }

  // Chart 4: Decisions Split
  const ctxDec = document.getElementById('chart-decisions');
  if (ctxDec) {
    if (chartDecisions) chartDecisions.destroy();
    const dec = data.decisions || { approved: 1, rejected: 0, pending: 0 };
    chartDecisions = new Chart(ctxDec, {
      type: 'doughnut',
      data: {
        labels: ['Approved', 'Rejected', 'Pending'],
        datasets: [{
          data: [dec.approved, dec.rejected, dec.pending],
          backgroundColor: ['#10B981', '#F43F5E', '#F59E0B'],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: '#94A3B8', font: { family: 'Fira Code', size: 11 } } }
        }
      }
    });
  }
}

function chartDefaultOptions() {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: '#94A3B8', font: { family: 'Fira Code', size: 11 } } }
    },
    scales: {
      x: {
        grid: { color: 'rgba(255, 255, 255, 0.05)' },
        ticks: { color: '#64748B', font: { family: 'Fira Code', size: 10 } }
      },
      y: {
        grid: { color: 'rgba(255, 255, 255, 0.05)' },
        ticks: { color: '#64748B', font: { family: 'Fira Code', size: 10 } }
      }
    }
  };
}

// ==========================================
// BLOCKCHAIN AUDIT LEDGER
// ==========================================
async function loadBlockchainLedger() {
  const container = document.getElementById('blockchain-list');
  container.innerHTML = `<div class="py-12 text-center text-xs text-slate-500 font-mono"><i data-lucide="loader-2" class="w-6 h-6 animate-spin mx-auto mb-2 text-teal-400"></i>Syncing blockchain ledger...</div>`;
  if (window.lucide) lucide.createIcons();

  try {
    const res = await fetch('/api/blockchain');
    const data = await res.json();
    const blocks = data.blocks || [];

    container.innerHTML = blocks.map((b, idx) => {
      const isGenesis = b.block_index === 0;
      return `
        <div class="glass-panel rounded-2xl p-5 border ${isGenesis ? 'border-teal-500/40 bg-teal-500/5' : 'border-slate-800'} space-y-3">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
            <div class="flex items-center space-x-2">
              <span class="w-7 h-7 rounded-lg ${isGenesis ? 'bg-teal-500/20 text-teal-400' : 'bg-slate-800 text-slate-300'} font-bold font-mono text-xs flex items-center justify-center">
                #${b.block_index}
              </span>
              <span class="text-sm font-bold font-mono text-white">${isGenesis ? 'Genesis Block (Root of Trust)' : 'Audit Transaction Block'}</span>
            </div>
            <span class="text-xs font-mono text-slate-500">${b.timestamp}</span>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
            <div class="p-2.5 rounded-lg bg-[#080D1A] border border-slate-800/80">
              <span class="text-slate-500 block text-[10px] uppercase">SHA-256 Current Hash</span>
              <span class="text-teal-400 break-all">${b.block_hash}</span>
            </div>
            <div class="p-2.5 rounded-lg bg-[#080D1A] border border-slate-800/80">
              <span class="text-slate-500 block text-[10px] uppercase">Previous Block Link</span>
              <span class="text-slate-400 break-all">${b.prev_hash}</span>
            </div>
          </div>

          <div class="pt-2">
            <span class="text-[10px] font-mono text-slate-500 uppercase block mb-1">Payload Content (JSON)</span>
            <div class="code-box p-3 text-[11px] text-slate-300 overflow-x-auto">
              <pre><code>${JSON.stringify(b.data, null, 2)}</code></pre>
            </div>
          </div>
        </div>
      `;
    }).join('');

    if (window.lucide) lucide.createIcons();
  } catch (err) {
    showToast("Failed to load blockchain: " + err.message, "error");
  }
}

async function verifyChainIntegrity() {
  const btn = document.getElementById('btn-verify-chain');
  const alertBox = document.getElementById('chain-verify-alert');

  btn.disabled = true;
  btn.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> Auditing hashes...`;
  if (window.lucide) lucide.createIcons();

  try {
    const res = await fetch('/api/blockchain/verify', { method: 'POST' });
    const data = await res.json();

    alertBox.classList.remove('hidden');
    if (data.is_valid) {
      alertBox.className = "rounded-xl p-4 border border-emerald-500/40 bg-emerald-500/10 text-emerald-200 text-xs";
      alertBox.innerHTML = `
        <div class="flex items-center space-x-2 font-bold font-mono text-emerald-300 mb-1">
          <i data-lucide="shield-check" class="w-5 h-5 text-emerald-400"></i>
          <span>CHAIN INTEGRITY VERIFIED: SECURE</span>
        </div>
        <p class="text-slate-300">All ${data.total_blocks} cryptographic blocks recalculated and confirmed against genesis root. Zero unauthorized modifications detected.</p>
      `;
      showToast("Blockchain cryptographic integrity verified!", "success");
    } else {
      alertBox.className = "rounded-xl p-4 border border-rose-500/40 bg-rose-500/10 text-rose-200 text-xs";
      alertBox.innerHTML = `
        <div class="flex items-center space-x-2 font-bold font-mono text-rose-400 mb-1">
          <i data-lucide="alert-triangle" class="w-5 h-5"></i>
          <span>INTEGRITY WARNING: TAMPER DETECTED</span>
        </div>
        <p class="text-slate-300">Cryptographic hash mismatch found. Certain records were edited out of chain consensus.</p>
      `;
      showToast("Chain verification failed: Tamper detected!", "error");
    }
    if (window.lucide) lucide.createIcons();
  } catch (err) {
    showToast("Error verifying blockchain: " + err.message, "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i data-lucide="shield-check" class="w-4 h-4"></i> VERIFY CHAIN INTEGRITY`;
    if (window.lucide) lucide.createIcons();
  }
}

// ==========================================
// SYSTEM STATUS TICKER & UTILITIES
// ==========================================
async function refreshSystemStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    const stats = data.stats || {};

    const bBlocks = document.getElementById('badge-blocks');
    const bPrefs = document.getElementById('badge-prefs');
    const bKb = document.getElementById('badge-kb');
    const qCount = document.getElementById('queue-count-badge');

    if (bBlocks) bBlocks.textContent = `Blocks: ${stats.blockchain_blocks || 0}`;
    if (bPrefs) bPrefs.textContent = `Rules: ${stats.preferences || 0}`;
    if (bKb) bKb.textContent = `RAG: ${stats.knowledge_base || 0}`;
    if (qCount) qCount.textContent = `${stats.approvals || 0}`;
  } catch (err) {
    console.warn("Status refresh notice:", err);
  }
}

async function repopulateMockData() {
  try {
    const res = await fetch('/api/database/repopulate', { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      showToast("Mock dataset and blockchain genesis restored!", "success");
      refreshSystemStatus();
      if (currentTab === 'queue') loadApprovalsQueue();
      if (currentTab === 'memory') { loadPreferences(); loadKnowledgeBase(); }
      if (currentTab === 'analytics') loadAnalytics();
      if (currentTab === 'blockchain') loadBlockchainLedger();
    }
  } catch (err) {
    showToast("Failed to restore mock data: " + err.message, "error");
  }
}

async function confirmClearDatabase() {
  if (confirm("Are you sure you want to purge all records from the database?")) {
    try {
      const res = await fetch('/api/database/clear', { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        showToast("Database successfully cleared.", "info");
        refreshSystemStatus();
        if (currentTab === 'queue') loadApprovalsQueue();
        if (currentTab === 'memory') { loadPreferences(); loadKnowledgeBase(); }
        if (currentTab === 'analytics') loadAnalytics();
        if (currentTab === 'blockchain') loadBlockchainLedger();
      }
    } catch (err) {
      showToast("Error clearing database: " + err.message, "error");
    }
  }
}

// ==========================================
// TOAST NOTIFICATION UTILITY
// ==========================================
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  let iconName = 'info';
  if (type === 'success') iconName = 'check-circle';
  if (type === 'error') iconName = 'alert-triangle';

  toast.innerHTML = `
    <i data-lucide="${iconName}" class="w-4 h-4 shrink-0"></i>
    <span>${message}</span>
  `;

  container.appendChild(toast);
  if (window.lucide) lucide.createIcons();

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}
