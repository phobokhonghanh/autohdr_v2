// AutoHDR Dashboard - Frontend (v4 — SSE + localStorage persistence + GA4)

// Use Vite env variables with fallbacks
const API_BASE = import.meta.env?.VITE_API_BASE || "http://100.122.90.44:8000";
const STORAGE_KEY = import.meta.env?.VITE_STORAGE_KEY || "autohdr_active_job";

// --- Google Analytics Helper ---
function trackEvent(eventName, params = {}) {
  if (typeof gtag === 'function') {
    gtag('event', eventName, params);
  }
}

let selectedFiles = [];
let eventSource = null;

document.querySelector('#app').innerHTML = `
<div class="container">
    <header>
        <h1>Auto download <span class="version">v1</span></h1> 
        <a href="">by tuitenPhở</a>
    </header>

    <nav class="tabs">
        <button class="tab-btn active" data-tab="main">Home</button>
        <button class="tab-btn" data-tab="results">Results</button>
    </nav>

    <main class="content">
        <!-- TAB 1: SETUP + LOGS (side by side) -->
        <section id="main" class="tab-pane active">
            <div class="split-layout">
                <!-- LEFT: Setup & Upload -->
                <div class="split-left">
                    <form id="upload-form">
                        <div class="card">
                            <h3>Authentication</h3>
                            <div class="form-group">
                                <label for="cookie">Cookie (first time)</label>
                                <textarea id="cookie" placeholder="Paste your full cookie string here..."></textarea>
                            </div>
                            <div class="form-divider">OR</div>
                            <div class="form-group">
                                <label for="email">Email (subsequent runs)</label>
                                <input type="email" id="email" placeholder="user@example.com">
                            </div>
                        </div>

                        <div class="card">
                            <h3>Upload</h3>
                            <div class="form-group">
                                <label for="address">Project name</label>
                                <input type="text" id="address" placeholder="e.g. project_1" required>
                            </div>
                            <div class="form-group">
                                <label>Images</label>
                                <div id="drop-zone" class="drop-zone">
                                    <span class="drop-zone__prompt">Drop files here or click to upload</span>
                                    <input type="file" name="files" id="file-input" multiple accept="image/*" class="drop-zone__input">
                                </div>
                                <ul id="file-list" class="file-list"></ul>
                            </div>
                        </div>

                        <button type="submit" id="submit-btn" class="btn-primary">Start Processing</button>
                    </form>
                </div>

                <!-- RIGHT: Processing Logs -->
                <div class="split-right">
                    <div class="card log-container">
                        <div class="log-header">
                            <h3 class="log-title">Logs</h3>
                            <div class="log-meta">
                                <button id="clear-logs-btn" class="btn-clear" title="Clear Logs">Clear</button>
                                <span id="job-status" class="status-badge status-idle">Idle</span>
                                <span id="job-id-display"></span>
                            </div>
                        </div>
                        <div id="log-output" class="log-output">
                            <p class="log-placeholder">Waiting for processing to start...</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- TAB 2: RESULTS -->
        <section id="results" class="tab-pane">
            <div class="card">
                <h3>Processed Photos</h3>
                <div id="results-grid" class="results-grid">
                    <p class="results-placeholder">No results yet.</p>
                </div>
            </div>
        </section>
    </main>
</div>
`;

// --- Tab Switching ---
const tabs = document.querySelectorAll(".tab-btn");
const panes = document.querySelectorAll(".tab-pane");

tabs.forEach(tab => {
  tab.addEventListener("click", () => {
    const target = tab.dataset.tab;
    tabs.forEach(t => t.classList.remove("active"));
    panes.forEach(p => p.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById(target).classList.add("active");
  });
});

// --- File Upload Handling ---
const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const fileList = document.getElementById("file-list");

dropZone.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", (e) => {
  handleFiles(e.target.files);
});

dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("drop-zone--over");
});

["dragleave", "dragend"].forEach(type => {
  dropZone.addEventListener(type, () => {
    dropZone.classList.remove("drop-zone--over");
  });
});

dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("drop-zone--over");
  handleFiles(e.dataTransfer.files);
});

function handleFiles(files) {
  selectedFiles = Array.from(files);
  updateFileList();
}

function updateFileList() {
  fileList.innerHTML = "";
  selectedFiles.forEach(file => {
    const li = document.createElement("li");
    li.innerHTML = `<span>${file.name}</span> <span>${(file.size / 1024).toFixed(1)} KB</span>`;
    fileList.appendChild(li);
  });
}

// --- DOM refs ---
const logOutput = document.getElementById("log-output");
const statusBadge = document.getElementById("job-status");
const jobIdDisplay = document.getElementById("job-id-display");
const resultsGrid = document.getElementById("results-grid");
const clearLogsBtn = document.getElementById("clear-logs-btn");
const uploadForm = document.getElementById("upload-form");
const submitBtn = document.getElementById("submit-btn");

// --- Clear Logs ---
clearLogsBtn.addEventListener("click", () => {
  logOutput.innerHTML = '<p class="log-placeholder">Logs cleared.</p>';
});

// ========================
// localStorage Persistence
// ========================

function saveJobState(jobId, status, results, downloadedFiles) {
  const state = { jobId, status, results: results || [], downloadedFiles: downloadedFiles || [] };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function loadJobState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

function clearJobState() {
  localStorage.removeItem(STORAGE_KEY);
}

function markFileDownloaded(filename) {
  const state = loadJobState();
  if (!state) return;
  if (!state.downloadedFiles.includes(filename)) {
    state.downloadedFiles.push(filename);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }
}

// ========================
// SSE Streaming
// ========================

function connectSSE(jobId, offset = 0) {
  // Close any existing SSE connection
  if (eventSource) {
    eventSource.close();
    eventSource = null;
  }

  jobIdDisplay.textContent = jobId.substring(0, 8) + "...";
  statusBadge.className = "status-badge status-processing";
  statusBadge.textContent = "Processing";

  // Disable form submission while job is active
  submitBtn.disabled = true;
  submitBtn.textContent = "Job in progress...";

  eventSource = new EventSource(`${API_BASE}/api/stream/${jobId}?offset=${offset}`);

  eventSource.addEventListener("log", (e) => {
    try {
      const data = JSON.parse(e.data);
      appendLogLine(data.line);
    } catch (err) {
      console.error("SSE log parse error:", err);
    }
  });

  eventSource.addEventListener("status", (e) => {
    try {
      const data = JSON.parse(e.data);
      handleStatusChange(jobId, data);
    } catch (err) {
      console.error("SSE status parse error:", err);
    }
  });

  eventSource.onerror = (err) => {
    console.warn("SSE connection error, will retry automatically...", err);
    // EventSource auto-reconnects by default.
    // If it closes permanently (e.g., server down), fall back to one-shot check.
    if (eventSource.readyState === EventSource.CLOSED) {
      console.warn("SSE closed permanently, falling back to status check.");
      fallbackStatusCheck(jobId);
    }
  };
}

function appendLogLine(line) {
  // Remove placeholder if present
  const placeholder = logOutput.querySelector(".log-placeholder");
  if (placeholder) placeholder.remove();

  const isAtBottom = logOutput.scrollHeight - logOutput.scrollTop <= logOutput.clientHeight + 100;

  const match = line.match(/^<(\w+):\s*([\d\?]+):\s*(.*)>$/);
  const div = document.createElement("div");
  div.className = "log-line";

  if (match) {
    const [_, level, step, msg] = match;
    const levelClass = `log-level-${level.toLowerCase()}`;
    div.innerHTML = `
      <span class="log-step">Step ${step}</span>
      <span class="log-level ${levelClass}">${level}</span>
      <span class="log-msg">${msg}</span>
    `;
  } else {
    div.textContent = line;
  }

  logOutput.appendChild(div);

  if (isAtBottom) {
    logOutput.scrollTop = logOutput.scrollHeight;
  }
}

function handleStatusChange(jobId, data) {
  if (data.status === "completed") {
    if (eventSource) { eventSource.close(); eventSource = null; }
    statusBadge.className = "status-badge status-completed";
    statusBadge.textContent = "Completed";
    submitBtn.disabled = false;
    submitBtn.textContent = "Start Processing";

    // Track job completion in GA
    trackEvent('job_completed', {
      event_category: 'pipeline',
      results_count: (data.results || []).length,
    });

    // Clear sensitive inputs
    document.getElementById("cookie").value = "";
    fileInput.value = "";
    selectedFiles = [];
    fileList.innerHTML = "";

    // Save state and download
    const results = data.results || [];
    saveJobState(jobId, "completed", results, []);
    showResults(results);
    triggerDownloads(results);

    // Auto-switch to results tab
    document.querySelector('[data-tab="results"]').click();

  } else if (data.status === "failed") {
    if (eventSource) { eventSource.close(); eventSource = null; }
    statusBadge.className = "status-badge status-failed";
    statusBadge.textContent = "Failed";
    submitBtn.disabled = false;
    submitBtn.textContent = "Start Processing";
    clearJobState();

    logOutput.innerHTML += `<div class="log-line" style="color:#ef4444; margin-top: 10px; font-weight: bold;">
        Pipeline failed: ${data.error}
        <button onclick="location.reload()" class="btn-retry" style="margin-left: 10px;">Retry</button>
    </div>`;

  } else if (data.status === "processing") {
    saveJobState(jobId, "processing", [], []);
  }
}

async function fallbackStatusCheck(jobId) {
  try {
    const res = await fetch(`${API_BASE}/api/status/${jobId}`);
    if (!res.ok) { clearJobState(); return; }
    const data = await res.json();
    handleStatusChange(jobId, data);

    // Reload full logs
    if (data.logs) {
      logOutput.innerHTML = "";
      data.logs.forEach(line => appendLogLine(line));
    }
  } catch (err) {
    console.error("Fallback status check failed:", err);
  }
}

// ========================
// Form Submission
// ========================

uploadForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  // Block if active job exists
  const existing = loadJobState();
  if (existing && (existing.status === "processing" || existing.status === "pending")) {
    alert("A job is already in progress. Please wait for it to complete.");
    return;
  }

  const cookie = document.getElementById("cookie").value;
  const email = document.getElementById("email").value;
  const address = document.getElementById("address").value;

  if (selectedFiles.length === 0) {
    alert("Please select at least one image!");
    return;
  }

  const formData = new FormData();
  formData.append("address", address);
  if (cookie) formData.append("cookie", cookie);
  if (email) formData.append("email", email);

  selectedFiles.forEach(file => {
    formData.append("files", file);
  });

  submitBtn.disabled = true;
  submitBtn.textContent = "Uploading...";
  logOutput.innerHTML = "";

  try {
    const response = await fetch(`${API_BASE}/api/process`, {
      method: "POST",
      body: formData
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Server error");
    }

    const data = await response.json();

    // Track form submission in GA
    trackEvent('job_submitted', {
      event_category: 'pipeline',
      files_count: selectedFiles.length,
      address: document.getElementById('address').value,
    });

    // Save to localStorage and connect SSE
    saveJobState(data.job_id, "pending", [], []);
    connectSSE(data.job_id);

  } catch (err) {
    alert("Error: " + err.message);
    submitBtn.disabled = false;
    submitBtn.textContent = "Start Processing";
  }
});

// ========================
// Results & Downloads
// ========================

function showResults(results) {
  if (!results || results.length === 0) return;

  resultsGrid.innerHTML = results.map(url => {
    // Handle relative URLs from backend
    const absoluteUrl = url.startsWith('/') ? `${API_BASE}${url}` : url;
    const filename = absoluteUrl.split('/').pop().split('?')[0];
    return `
            <div class="result-item">
                <div class="result-img-placeholder">📸</div>
                <div class="result-info">
                    <div class="result-filename">${filename}</div>
                    <a href="${absoluteUrl}" target="_blank" class="download-link" data-filename="${filename}">Download</a>
                </div>
            </div>
        `;
  }).join("");
}

async function triggerDownloads(results) {
  if (!results || results.length === 0) return;

  // Track download event in GA
  trackEvent('download_triggered', {
    event_category: 'download',
    files_count: results.length,
  });

  for (const url of results) {
    const absoluteUrl = url.startsWith('/') ? `${API_BASE}${url}` : url;
    const filename = absoluteUrl.split('/').pop().split('?')[0];

    try {
      // Use Blob approach to force download of cross-origin assets
      const response = await fetch(absoluteUrl);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);

      const a = document.createElement("a");
      a.href = blobUrl;
      a.setAttribute("download", filename);
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(blobUrl);

      markFileDownloaded(filename);
      console.log(`Download triggered for: ${filename}`);

      // Small delay between multiple downloads
      if (results.length > 1) {
        await new Promise(resolve => setTimeout(resolve, 300));
      }
    } catch (err) {
      console.error(`Download failed for ${absoluteUrl}:`, err);
      // Fallback: simple link (browser might still open images in new tab)
      window.open(absoluteUrl, '_blank');
    }
  }
}

// ========================
// Page Load: Reconnection
// ========================

async function checkPreviousJob() {
  const state = loadJobState();
  if (!state || !state.jobId) return;

  // Case 1: Job was processing — check if still active
  if (state.status === "processing" || state.status === "pending") {
    try {
      const res = await fetch(`${API_BASE}/api/status/${state.jobId}`);
      if (!res.ok) {
        // Job no longer exists on server
        clearJobState();
        return;
      }

      const data = await res.json();

      if (data.status === "processing" || data.status === "pending") {
        // Still running — reconnect SSE and show existing logs
        logOutput.innerHTML = "";
        const logs = data.logs || [];
        logs.forEach(line => appendLogLine(line));
        connectSSE(state.jobId, logs.length);
      } else if (data.status === "completed") {
        // Completed while we were away
        handleCompletedWhileAway(state, data);
      } else if (data.status === "failed") {
        clearJobState();
      }
    } catch (err) {
      console.error("Error checking previous job:", err);
      clearJobState();
    }
    return;
  }

  // Case 2: Job was completed — check downloads
  if (state.status === "completed") {
    handleCompletedWhileAway(state, { results: state.results });
  }
}

function handleCompletedWhileAway(state, data) {
  const results = data.results || state.results || [];
  const downloaded = state.downloadedFiles || [];

  // Find files not yet downloaded
  const remaining = results.filter(url => {
    const filename = url.split('/').pop().split('?')[0];
    return !downloaded.includes(filename);
  });

  if (remaining.length === 0) {
    // All downloaded — silently clear
    clearJobState();
    return;
  }

  // Ask user if they want to download remaining files
  statusBadge.className = "status-badge status-completed";
  statusBadge.textContent = "Completed";
  showResults(results);

  const msg = `Your previous job completed with ${remaining.length} file(s) not yet downloaded. Download now?`;
  if (confirm(msg)) {
    triggerDownloads(remaining);
    document.querySelector('[data-tab="results"]').click();
  }

  // Update state as completed with full results
  saveJobState(state.jobId, "completed", results, downloaded);
}

// Run on page load
checkPreviousJob();
