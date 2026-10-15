/**
 * LocalBiz AI – script.js
 * Handles: health check, form validation, AI generation, demo mode,
 *          copy buttons, download, regenerate, toast notifications.
 */

"use strict";

const demoModeOnly = document.body.dataset.demoModeOnly === "true";

/* ════════════════════════════════════════════════
   STATE
   ════════════════════════════════════════════════ */
const State = {
  lastFormData:  null,   // last submitted form payload
  lastResult:    null,   // last generated result object
  demoMode:      demoModeOnly,  // whether demo mode is active
  ollamaOnline:  false,  // whether Ollama responded OK
  generating:    false,  // request in flight
};

/* ════════════════════════════════════════════════
   DOM REFS
   ════════════════════════════════════════════════ */
const $ = id => document.getElementById(id);
const qs = sel => document.querySelector(sel);

const bizForm        = $("biz-form");
const generateBtn    = $("generate-btn");
const demoModeBtn    = $("demo-mode-btn");
const demoBanner     = $("demo-banner");
const demoOffBtn     = $("demo-off-btn");
const ollamaErrCard  = $("ollama-error-card");
const useDemoBtn     = $("use-demo-btn");
const useDemoBtn2    = $("use-demo-btn-2");
const retryHealthBtn = $("retry-health-btn");
const retryBtn       = $("retry-btn");
const regenerateBtn  = $("regenerate-btn");
const downloadBtn    = $("download-btn");
const statusDot      = $("ollama-status");
const toast          = $("toast");

// Panels
const emptyState    = $("empty-state");
const loadingState  = $("loading-state");
const errorState    = $("error-state");
const resultsState  = $("results-state");

// Error panel elements
const errorTitle    = $("error-title");
const errorMessage  = $("error-message");
const errorSteps    = $("error-steps");

// Result elements
const resultChips      = $("result-chips");
const demoResultBadge  = $("demo-result-badge");
const elapsedBadge     = $("elapsed-badge");
const captionText      = $("caption-text");
const shortDescText    = $("short-desc-text");
const hashtagsEl       = $("hashtags-text");
const ctaText          = $("cta-text");
const whatsappText     = $("whatsapp-text");

// Character count
const descInput  = $("description");
const descCount  = $("desc-count");

/* ════════════════════════════════════════════════
   UTILITIES
   ════════════════════════════════════════════════ */

/** Show one panel, hide the others */
function showPanel(panel) {
  [emptyState, loadingState, errorState, resultsState].forEach(p => {
    if (p) p.classList.toggle("hidden", p !== panel);
  });
}

/** Display a toast notification */
let toastTimer;
function showToast(msg, type = "info", duration = 3000) {
  toast.textContent = msg;
  toast.className   = `toast ${type}`;
  toast.classList.remove("hidden");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.add("hidden"), duration);
}

/** Collect form data into a plain object */
function collectFormData() {
  const fd  = new FormData(bizForm);
  const obj = {};
  fd.forEach((v, k) => { obj[k] = v.trim(); });
  obj.demo_mode = State.demoMode;
  return obj;
}

/** Validate form; return { valid, errors } */
function validateForm(data) {
  const errors = {};
  if (!data.business_name)   errors.business_name   = "Business name is required.";
  if (!data.product_name)    errors.product_name    = "Product / service name is required.";
  if (!data.description)     errors.description     = "Description is required.";
  if (!data.target_audience) errors.target_audience = "Target audience is required.";
  return { valid: Object.keys(errors).length === 0, errors };
}

/** Mark field errors in the UI */
function applyFieldErrors(errors) {
  clearFieldErrors();
  Object.entries(errors).forEach(([field, msg]) => {
    const el  = document.getElementById(field);
    const err = document.getElementById(`err-${field}`);
    if (el)  el.classList.add("error-input");
    if (err) err.textContent = msg;
  });
  // Scroll to first error
  const firstErrField = document.querySelector(".error-input");
  if (firstErrField) firstErrField.scrollIntoView({ behavior: "smooth", block: "center" });
}

function clearFieldErrors() {
  document.querySelectorAll(".error-input").forEach(el => el.classList.remove("error-input"));
  document.querySelectorAll(".field-error").forEach(el => el.textContent = "");
}

/* ════════════════════════════════════════════════
   HEALTH CHECK
   ════════════════════════════════════════════════ */

async function checkOllamaHealth() {
  statusDot.className = "status-dot status-checking";
  try {
    const res  = await fetch("/health");
    const data = await res.json();
    State.ollamaOnline = data.ollama_running && data.model_available;

    if (data.ollama_running && data.model_available) {
      statusDot.className = "status-dot status-ok";
      statusDot.title     = `Ollama OK · Model: ${data.model_name}`;
      ollamaErrCard.classList.add("hidden");
    } else if (data.ollama_running && !data.model_available) {
      statusDot.className = "status-dot status-error";
      statusDot.title     = `Ollama running but model '${data.model_name}' not found`;
      showOllamaError([
        `Run: ollama pull ${data.model_name}`,
        "Then refresh this page",
      ]);
    } else {
      statusDot.className = "status-dot status-error";
      statusDot.title     = "Ollama not running";
      showOllamaError(null);
    }
  } catch (_) {
    statusDot.className = "status-dot status-error";
    statusDot.title     = "Could not reach the Flask server";
  }
}

function showOllamaError(extraSteps) {
  ollamaErrCard.classList.remove("hidden");
  if (extraSteps) {
    const list  = $("setup-steps-list");
    extraSteps.forEach(s => {
      const li       = document.createElement("li");
      li.textContent = s;
      list.appendChild(li);
    });
  }
}

/* ════════════════════════════════════════════════
   DEMO MODE
   ════════════════════════════════════════════════ */

function enableDemoMode() {
  State.demoMode = true;
  demoBanner.classList.remove("hidden");
  ollamaErrCard.classList.add("hidden");
  showToast("🧪 Demo Mode enabled — no Ollama needed!", "info");
}

function disableDemoMode() {
  State.demoMode = false;
  demoBanner.classList.add("hidden");
  showToast("Demo Mode off.", "info");
}

/* ════════════════════════════════════════════════
   RENDER RESULTS
   ════════════════════════════════════════════════ */

function renderHashtags(text) {
  hashtagsEl.innerHTML = "";
  const tags = text.trim().split(/\s+/).filter(t => t.startsWith("#"));
  if (tags.length === 0) {
    hashtagsEl.textContent = text;
    return;
  }
  tags.forEach(tag => {
    const span       = document.createElement("span");
    span.className   = "hashtag-tag";
    span.textContent = tag;
    span.title       = "Click to copy";
    span.style.cursor = "pointer";
    span.addEventListener("click", () => {
      copyToClipboard(tag);
      showToast(`Copied ${tag}`, "success", 1500);
    });
    hashtagsEl.appendChild(span);
  });
}

function renderChips(data) {
  resultChips.innerHTML = "";
  const chips = [
    data.platform,
    data.language,
    data.tone,
  ].filter(Boolean);
  chips.forEach(c => {
    const span     = document.createElement("span");
    span.className = "result-chip";
    span.textContent = c;
    resultChips.appendChild(span);
  });
}

function renderResults(result, formData, { demo = false, elapsed = null } = {}) {
  State.lastResult   = result;
  State.lastFormData = formData;

  // Chips
  renderChips(formData);

  // Demo badge
  demoResultBadge.classList.toggle("hidden", !demo);

  // Elapsed
  if (elapsed && !demo) {
    elapsedBadge.textContent = `⏱ Generated in ${elapsed}s`;
    elapsedBadge.classList.remove("hidden");
  } else {
    elapsedBadge.classList.add("hidden");
  }

  // Caption
  captionText.textContent    = result.caption || "";

  // Short description
  shortDescText.textContent  = result.short_description || "";

  // Hashtags (special cloud rendering)
  renderHashtags(result.hashtags || "");

  // CTA
  ctaText.textContent        = result.call_to_action || "";

  // WhatsApp
  whatsappText.textContent   = result.whatsapp_message || "";

  showPanel(resultsState);

  // Animate cards in
  resultsState.querySelectorAll(".result-card").forEach((card, i) => {
    card.style.animationDelay = `${i * 0.06}s`;
  });
}

/* ════════════════════════════════════════════════
   GENERATE
   ════════════════════════════════════════════════ */

async function generate(formData) {
  if (State.generating) return;
  State.generating = true;

  showPanel(loadingState);
  generateBtn.disabled = true;
  generateBtn.querySelector(".btn-text").textContent = "Generating…";

  try {
    const res  = await fetch("/generate", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(formData),
    });
    const data = await res.json();

    if (res.status === 422) {
      // Validation errors from server (shouldn't normally happen as we validate client-side too)
      applyFieldErrors(data.errors || {});
      showPanel(emptyState);
      return;
    }

    if (!data.success) {
      // Show error panel
      errorTitle.textContent   = "Generation Failed";
      errorMessage.textContent = data.error || "An unknown error occurred.";
      if (data.setup_steps && data.setup_steps.length) {
        errorSteps.innerHTML = "";
        data.setup_steps.forEach(step => {
          const li = document.createElement("li");
          li.textContent = step;
          errorSteps.appendChild(li);
        });
        errorSteps.classList.remove("hidden");
      } else {
        errorSteps.classList.add("hidden");
      }
      showPanel(errorState);
      return;
    }

    renderResults(data.result, formData, { demo: data.demo, elapsed: data.elapsed });
    showToast(data.demo ? "🧪 Demo content ready!" : "✨ Content generated!", "success");

  } catch (err) {
    errorTitle.textContent   = "Network Error";
    errorMessage.textContent = "Could not connect to the server. Make sure Flask is running (python app.py).";
    errorSteps.classList.add("hidden");
    showPanel(errorState);
  } finally {
    State.generating = false;
    generateBtn.disabled = false;
    generateBtn.querySelector(".btn-text").textContent = "Generate with AI";
  }
}

/* ════════════════════════════════════════════════
   COPY TO CLIPBOARD
   ════════════════════════════════════════════════ */

async function copyToClipboard(text) {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
    } else {
      // Fallback for http (non-secure) contexts
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.opacity  = "0";
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    }
    return true;
  } catch (_) {
    return false;
  }
}

function setupCopyButtons() {
  document.querySelectorAll(".copy-btn").forEach(btn => {
    btn.addEventListener("click", async () => {
      const targetId = btn.dataset.target;
      const target   = $(targetId);
      if (!target) return;

      // For hashtag cloud get plain text
      let text;
      if (targetId === "hashtags-text") {
        text = Array.from(target.querySelectorAll(".hashtag-tag"))
                    .map(t => t.textContent)
                    .join(" ");
        if (!text) text = target.textContent;
      } else {
        text = target.textContent || target.innerText;
      }

      const ok = await copyToClipboard(text.trim());
      if (ok) {
        btn.classList.add("copied");
        const icon = btn.querySelector(".copy-icon");
        if (icon) icon.textContent = "✅";
        btn.querySelector("span:last-child")
           ? (btn.querySelectorAll("span")[1].textContent = "Copied!")
           : null;
        showToast("Copied to clipboard! ✅", "success", 2000);
        setTimeout(() => {
          btn.classList.remove("copied");
          if (icon) icon.textContent = "📋";
          const spans = btn.querySelectorAll("span");
          if (spans[1]) spans[1].textContent = "Copy";
        }, 2000);
      } else {
        showToast("Copy failed — please copy manually.", "error");
      }
    });
  });
}

/* ════════════════════════════════════════════════
   DOWNLOAD
   ════════════════════════════════════════════════ */

async function downloadContent() {
  if (!State.lastResult || !State.lastFormData) {
    showToast("No content to download yet.", "error");
    return;
  }
  try {
    const res = await fetch("/download", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({
        result: State.lastResult,
        meta:   State.lastFormData,
      }),
    });
    if (!res.ok) throw new Error("Download failed");

    const blob     = await res.blob();
    const url      = URL.createObjectURL(blob);
    const a        = document.createElement("a");
    const filename = res.headers.get("Content-Disposition")
                        ?.match(/filename="?([^"]+)"?/)?.[1]
                    || "localbiz_ai_content.txt";
    a.href     = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast("⬇️ File downloaded!", "success");
  } catch (err) {
    showToast("Download failed. Try again.", "error");
  }
}

/* ════════════════════════════════════════════════
   CHARACTER COUNTER
   ════════════════════════════════════════════════ */

function setupCharCounter() {
  if (!descInput || !descCount) return;
  const maxLen = parseInt(descInput.getAttribute("maxlength") || "500", 10);
  function update() {
    const len = descInput.value.length;
    descCount.textContent = `${len} / ${maxLen}`;
    descCount.style.color = len > maxLen * 0.85
      ? "var(--clr-accent-2)"
      : "var(--clr-text-dim)";
  }
  descInput.addEventListener("input", update);
  update();
}

/* ════════════════════════════════════════════════
   FORM SUBMIT
   ════════════════════════════════════════════════ */

function setupForm() {
  bizForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearFieldErrors();

    const data = collectFormData();
    const { valid, errors } = validateForm(data);

    if (!valid) {
      applyFieldErrors(errors);
      return;
    }

    await generate(data);
  });
}

/* ════════════════════════════════════════════════
   EVENT LISTENERS
   ════════════════════════════════════════════════ */

function setupEventListeners() {
  // Demo mode on
  demoModeBtn?.addEventListener("click", () => {
    enableDemoMode();
    const data = collectFormData();
    const { valid, errors } = validateForm(data);
    if (!valid) { applyFieldErrors(errors); return; }
    generate(data);
  });

  // Demo banner off
  demoOffBtn?.addEventListener("click", () => {
    disableDemoMode();
    showPanel(emptyState);
  });

  // Use demo from Ollama error card
  useDemoBtn?.addEventListener("click", () => {
    ollamaErrCard.classList.add("hidden");
    enableDemoMode();
  });

  // Use demo from error panel
  useDemoBtn2?.addEventListener("click", () => {
    enableDemoMode();
    if (State.lastFormData) {
      generate({ ...State.lastFormData, demo_mode: true });
    } else {
      showPanel(emptyState);
    }
  });

  // Retry health check
  retryHealthBtn?.addEventListener("click", () => {
    ollamaErrCard.classList.add("hidden");
    checkOllamaHealth();
  });

  // Retry generate
  retryBtn?.addEventListener("click", () => {
    if (State.lastFormData) generate(State.lastFormData);
    else showPanel(emptyState);
  });

  // Regenerate
  regenerateBtn?.addEventListener("click", () => {
    if (State.lastFormData) generate(State.lastFormData);
  });

  // Download
  downloadBtn?.addEventListener("click", downloadContent);

  // Copy buttons
  setupCopyButtons();

  // Clear field error on input
  bizForm?.querySelectorAll(".field-input").forEach(input => {
    input.addEventListener("input", () => {
      input.classList.remove("error-input");
      const errEl = document.getElementById(`err-${input.id}`);
      if (errEl) errEl.textContent = "";
    });
  });
}

/* ════════════════════════════════════════════════
   INIT
   ════════════════════════════════════════════════ */

document.addEventListener("DOMContentLoaded", () => {
  setupForm();
  setupCharCounter();
  setupEventListeners();

  if (demoModeOnly) {
    demoBanner.classList.remove("hidden");
    statusDot.classList.add("hidden");
    ollamaErrCard.classList.add("hidden");
  } else {
    checkOllamaHealth();
    setInterval(checkOllamaHealth, 30_000);
  }
});
