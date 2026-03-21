const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");

const utils = require(path.resolve(__dirname, "../ui/workflow_app_utils.js"));

test("escapeHtml neutralizes inline script payload", () => {
  const payload = '<img src=x onerror=alert("xss")><script>alert(1)</script>';
  const escaped = utils.escapeHtml(payload);
  assert.equal(escaped.includes("<script>"), false);
  assert.equal(escaped.includes("&lt;script&gt;"), true);
  assert.equal(escaped.includes("onerror="), true);
});

test("toSafeHref rejects javascript and data URL", () => {
  assert.equal(utils.toSafeHref("javascript:alert(1)"), "#");
  assert.equal(utils.toSafeHref("data:text/html;base64,PHNjcmlwdD4="), "#");
});

test("normalize status falls back for invalid states", () => {
  utils.setStatusConfig({
    run_statuses: ["idle", "running", "paused", "done", "error", "unknown"],
    step_statuses: ["pending", "running", "done", "error"],
    status_aliases: { success: "done", failed: "error" },
  });
  assert.equal(utils.normalizeRunStatus("rooted"), "unknown");
  assert.equal(utils.normalizeStepStatus("__proto__"), "pending");
});
