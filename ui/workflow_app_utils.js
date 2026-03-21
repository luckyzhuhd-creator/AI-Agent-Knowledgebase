(function (globalScope) {
  const statusConfig = {
    runStatuses: new Set(["idle", "pending", "running", "paused", "done", "error", "unknown"]),
    stepStatuses: new Set(["pending", "running", "done", "error"]),
    statusAliases: {
      success: "done",
      failed: "error",
    },
  };

  function safeText(value, fallback = "-") {
    const text = String(value ?? "").trim();
    return text || fallback;
  }

  function safeNumber(value, fallback = 0) {
    const n = Number(value);
    return Number.isFinite(n) ? n : fallback;
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function toSafeHref(href) {
    try {
      const url = new URL(String(href ?? ""), globalScope.location ? globalScope.location.origin : "http://localhost");
      if (url.protocol === "http:" || url.protocol === "https:") {
        return url.href;
      }
    } catch (e) {}
    return "#";
  }

  function normalizeStatus(value, allowed, fallback) {
    const raw = safeText(value, fallback).toLowerCase();
    const normalized = statusConfig.statusAliases[raw] || raw;
    return allowed.has(normalized) ? normalized : fallback;
  }

  function normalizeStepStatus(value) {
    return normalizeStatus(value, statusConfig.stepStatuses, "pending");
  }

  function normalizeRunStatus(value) {
    return normalizeStatus(value, statusConfig.runStatuses, "unknown");
  }

  function setStatusConfig(config = {}) {
    const runStatuses = Array.isArray(config.run_statuses) ? config.run_statuses : [];
    const stepStatuses = Array.isArray(config.step_statuses) ? config.step_statuses : [];
    const aliases = config.status_aliases && typeof config.status_aliases === "object" ? config.status_aliases : {};
    if (runStatuses.length > 0) {
      statusConfig.runStatuses = new Set(runStatuses.map(item => safeText(item, "").toLowerCase()).filter(Boolean));
    }
    if (stepStatuses.length > 0) {
      statusConfig.stepStatuses = new Set(stepStatuses.map(item => safeText(item, "").toLowerCase()).filter(Boolean));
    }
    statusConfig.statusAliases = Object.fromEntries(
      Object.entries(aliases).map(([k, v]) => [safeText(k, "").toLowerCase(), safeText(v, "").toLowerCase()]).filter(([k, v]) => k && v)
    );
    if (Object.keys(statusConfig.statusAliases).length === 0) {
      statusConfig.statusAliases = { success: "done", failed: "error" };
    }
  }

  const api = {
    safeText,
    safeNumber,
    escapeHtml,
    toSafeHref,
    normalizeStepStatus,
    normalizeRunStatus,
    setStatusConfig,
  };

  globalScope.WorkflowAppUtils = api;
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
})(typeof window !== "undefined" ? window : globalThis);
