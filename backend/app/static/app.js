const API = "";

// ---------- Tabs ----------
document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.dataset.tab).classList.add("active");
  });
});

// ---------- Tab 1: Custom Solver ----------
let currentCaptchaId = null;
let currentImageB64 = null;

document.getElementById("btn-generate").addEventListener("click", async () => {
  const res = await fetch(`${API}/api/generate`, { method: "POST" });
  const data = await res.json();
  currentCaptchaId = data.captcha_id;
  currentImageB64 = data.image_base64;
  document.getElementById("captcha-img").src = `data:image/png;base64,${data.image_base64}`;
  document.getElementById("btn-solve").disabled = false;
  document.getElementById("solver-result").textContent = "";
  document.getElementById("solver-result").className = "result-box";
});

document.getElementById("btn-solve").addEventListener("click", async () => {
  if (!currentCaptchaId) return;
  const res = await fetch(`${API}/api/solve/${currentCaptchaId}?image_base64=${encodeURIComponent(currentImageB64)}`, {
    method: "POST",
  });
  const data = await res.json();
  const box = document.getElementById("solver-result");
  box.className = "result-box " + (data.success ? "ok" : "fail");
  box.textContent = JSON.stringify(data, null, 2);
});

// ---------- Tab 2: Provider Verification ----------
let siteKeys = {};

async function loadSiteKeysAndRenderWidgets() {
  const res = await fetch(`${API}/api/site-keys`);
  siteKeys = await res.json();

  const waitFor = (checkFn, cb, tries = 50) => {
    if (checkFn()) return cb();
    if (tries <= 0) return console.warn("Widget script did not load in time");
    setTimeout(() => waitFor(checkFn, cb, tries - 1), 200);
  };

  waitFor(
    () => window.grecaptcha && window.grecaptcha.render,
    () => grecaptcha.render("recaptcha-widget", { sitekey: siteKeys.recaptcha_site_key })
  );
  waitFor(
    () => window.hcaptcha && window.hcaptcha.render,
    () => hcaptcha.render("hcaptcha-widget", { sitekey: siteKeys.hcaptcha_site_key })
  );
  waitFor(
    () => window.turnstile && window.turnstile.render,
    () => turnstile.render("#turnstile-widget", { sitekey: siteKeys.turnstile_site_key })
  );
}
loadSiteKeysAndRenderWidgets();

function getTokenFor(provider) {
  try {
    if (provider === "recaptcha") return grecaptcha.getResponse();
    if (provider === "hcaptcha") return hcaptcha.getResponse();
    if (provider === "turnstile") return turnstile.getResponse();
  } catch (e) {
    return null;
  }
  return null;
}

async function postVerify(provider, token) {
  const res = await fetch(`${API}/api/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider, token }),
  });
  const data = await res.json();
  const box = document.getElementById("verify-result");
  box.className = "result-box " + (data.success ? "ok" : "fail");
  box.textContent = JSON.stringify(data, null, 2);
}

document.querySelectorAll(".verify-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const provider = btn.dataset.provider;
    const token = getTokenFor(provider);
    postVerify(provider, token || null);
  });
});

document.getElementById("btn-verify-missing").addEventListener("click", () => postVerify("recaptcha", null));
document.getElementById("btn-verify-garbage").addEventListener("click", () => postVerify("recaptcha", "not-a-real-token"));

// ---------- Tab 3: Batch ----------
document.getElementById("btn-batch-run").addEventListener("click", async () => {
  const count = parseInt(document.getElementById("batch-count").value, 10) || 20;
  const box = document.getElementById("batch-result");
  box.textContent = "Running...";
  const res = await fetch(`${API}/api/batch-run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ count }),
  });
  const data = await res.json();
  box.className = "result-box ok";
  box.textContent =
    `Accuracy: ${(data.accuracy * 100).toFixed(1)}%  (${data.correct}/${data.ran})\n` +
    `Avg processing time: ${data.avg_processing_time_ms} ms\n\n` +
    JSON.stringify(data.results.slice(0, 10), null, 2) +
    (data.results.length > 10 ? `\n... (${data.results.length - 10} more)` : "");
});

// ---------- Tab 4: Dashboard ----------
async function loadStats() {
  const res = await fetch(`${API}/api/stats`);
  const data = await res.json();
  const grid = document.getElementById("stats-grid");
  grid.innerHTML = "";
  const cards = [
    ["Total Attempts", data.total_attempts],
    ["Successful", data.successful],
    ["Failed", data.failed],
    ["Success Rate", `${(data.success_rate * 100).toFixed(1)}%`],
    ["Avg Time (ms)", data.avg_processing_time_ms],
    ["Avg OCR Confidence", data.avg_confidence ?? "n/a"],
    ["Est. Cost (USD)", `$${data.total_estimated_cost_usd.toFixed(4)}`],
    ["Verification Attempts", data.verification_attempts],
    ["Verification Success Rate", `${(data.verification_success_rate * 100).toFixed(1)}%`],
  ];
  for (const [label, value] of cards) {
    const div = document.createElement("div");
    div.className = "stat-card";
    div.innerHTML = `<div class="label">${label}</div><div class="value">${value}</div>`;
    grid.appendChild(div);
  }
  const byType = document.createElement("div");
  byType.className = "stat-card";
  byType.style.gridColumn = "1 / -1";
  byType.innerHTML = `<div class="label">By Challenge Type</div><pre style="margin-top:8px;white-space:pre-wrap;">${JSON.stringify(data.by_challenge_type, null, 2)}</pre>`;
  grid.appendChild(byType);
}
document.getElementById("btn-refresh-stats").addEventListener("click", loadStats);
document.getElementById("btn-reset-stats").addEventListener("click", async () => {
  await fetch(`${API}/api/stats/reset`, { method: "POST" });
  loadStats();
});

// ---------- Tab 5: Dataset insights ----------
document.getElementById("btn-load-dataset").addEventListener("click", async () => {
  const box = document.getElementById("dataset-result");
  box.textContent = "Loading...";
  try {
    const res = await fetch(`${API}/api/dataset/captcha-distribution`);
    const data = await res.json();
    box.className = "result-box ok";
    box.textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    box.className = "result-box fail";
    box.textContent = "Could not load dataset report: " + e;
  }
});
