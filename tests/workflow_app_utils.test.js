const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");

const utils = require(path.resolve(__dirname, "../ui/workflow_app_utils.js"));

test("toSafeHref blocks dangerous protocols", () => {
  assert.equal(utils.toSafeHref("javascript:alert(1)"), "#");
  assert.equal(utils.toSafeHref("data:text/html,abc"), "#");
  assert.equal(utils.toSafeHref("https://example.com/a"), "https://example.com/a");
});

test("normalizeRunStatus supports aliases and fallback", () => {
  utils.setStatusConfig({
    run_statuses: ["idle", "running", "paused", "done", "error", "unknown"],
    step_statuses: ["pending", "running", "done", "error"],
    status_aliases: { success: "done", failed: "error" },
  });
  assert.equal(utils.normalizeRunStatus("success"), "done");
  assert.equal(utils.normalizeRunStatus("FAILED"), "error");
  assert.equal(utils.normalizeRunStatus("not-valid"), "unknown");
});

test("normalizeStepStatus rejects unknown values", () => {
  assert.equal(utils.normalizeStepStatus("running"), "running");
  assert.equal(utils.normalizeStepStatus("success"), "done");
  assert.equal(utils.normalizeStepStatus("invalid"), "pending");
});
