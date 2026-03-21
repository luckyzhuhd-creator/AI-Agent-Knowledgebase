import pytest
from pathlib import Path

from agents.orchestrator import Orchestrator
from agents.writer_agent import RUN_STATUS_SUCCESS
import agents.orchestrator as orch_module
import ui.workflow_server as workflow_server


@pytest.fixture(autouse=True)
def reset_workflow_server_state():
    with workflow_server.STATE.lock:
        workflow_server.STATE.process = None
        workflow_server.STATE.status = "idle"
        workflow_server.STATE.topic = ""
        workflow_server.STATE.logs = []
        workflow_server.STATE.run_id = ""
        workflow_server.STATE.error_code = ""
        workflow_server.STATE.started_at = 0.0
        workflow_server.STATE.paused = False
        workflow_server.STATE.exit_code = None
        workflow_server.STATE.result = {}
        workflow_server.STATE.last_payload = {}
    yield
    with workflow_server.STATE.lock:
        workflow_server.STATE.process = None
        workflow_server.STATE.status = "idle"
        workflow_server.STATE.topic = ""
        workflow_server.STATE.logs = []
        workflow_server.STATE.run_id = ""
        workflow_server.STATE.error_code = ""
        workflow_server.STATE.started_at = 0.0
        workflow_server.STATE.paused = False
        workflow_server.STATE.exit_code = None
        workflow_server.STATE.result = {}
        workflow_server.STATE.last_payload = {}


def test_orchestrator_run_calls_pipeline_in_order(monkeypatch):
    calls = []

    class FakeResearchAgent:
        def run(self, topic):
            calls.append(("research", topic))
            return [{"url": "https://x.com"}]

    class FakeAnalysisAgent:
        def run(self, sources, topic):
            calls.append(("analysis", sources, topic))
            return ["https://x.com"]

    class FakeKnowledgeAgent:
        def build(self, topic, urls):
            calls.append(("knowledge", topic, urls))
            return "note"

    class FakeWriterAgent:
        def write(self, topic, content, urls, **kwargs):
            calls.append(("writer", topic, content, urls, kwargs))
            return {
                "artifacts": {
                    "markdown": "02_Research/ai_agent_framework.md",
                    "json": "02_Research/ai_agent_framework.json",
                    "run": "02_Research/ai_agent_framework.run.json",
                }
            }

    monkeypatch.setattr(orch_module, "ResearchAgent", FakeResearchAgent)
    monkeypatch.setattr(orch_module, "AnalysisAgent", FakeAnalysisAgent)
    monkeypatch.setattr(orch_module, "KnowledgeAgent", FakeKnowledgeAgent)
    monkeypatch.setattr(orch_module, "WriterAgent", FakeWriterAgent)

    Orchestrator().run("AI Agent Framework")

    assert calls[0] == ("research", "AI Agent Framework")
    assert calls[1][0] == "analysis"
    assert calls[2] == ("knowledge", "AI Agent Framework", ["https://x.com"])
    assert calls[3][0:4] == ("writer", "AI Agent Framework", "note", ["https://x.com"])
    assert "run_id" in calls[3][4]
    assert calls[3][4]["status"] == RUN_STATUS_SUCCESS
    assert isinstance(calls[3][4]["duration_ms"], int)
    assert calls[3][4]["sources"] == [{"url": "https://x.com"}]


def test_orchestrator_create_skills_contains_all_stages():
    orchestrator = Orchestrator()
    registry = orchestrator.create_skills("AI Agent Framework", "run-1", 0.0)

    assert list(registry.keys()) == ["research", "analysis", "knowledge", "writer"]


def test_orchestrator_run_super_skill_supports_stage_subset(monkeypatch):
    calls = []

    class FakeResearchAgent:
        def run(self, topic):
            calls.append(("research", topic))
            return [{"url": "https://x.com"}]

    class FakeAnalysisAgent:
        def run(self, sources, topic):
            calls.append(("analysis", sources, topic))
            return ["https://x.com"]

    class FakeKnowledgeAgent:
        def build(self, topic, urls):
            calls.append(("knowledge", topic, urls))
            return "note"

    class FakeWriterAgent:
        def write(self, topic, content, urls, **kwargs):
            calls.append(("writer", topic, content, urls, kwargs))
            return {"artifacts": {"markdown": "02_Research/x.md"}}

    monkeypatch.setattr(orch_module, "ResearchAgent", FakeResearchAgent)
    monkeypatch.setattr(orch_module, "AnalysisAgent", FakeAnalysisAgent)
    monkeypatch.setattr(orch_module, "KnowledgeAgent", FakeKnowledgeAgent)
    monkeypatch.setattr(orch_module, "WriterAgent", FakeWriterAgent)

    context = Orchestrator().run_super_skill("AI Agent Framework", stages=["research", "analysis", "knowledge"])

    assert [item[0] for item in calls] == ["research", "analysis", "knowledge"]
    assert context["urls"] == ["https://x.com"]
    assert context["note"] == "note"
    assert context["run_payload"] is None


def test_orchestrator_run_super_skill_rejects_unknown_stage():
    with pytest.raises(ValueError, match="Unknown stages: unknown"):
        Orchestrator().run_super_skill("AI Agent Framework", stages=["research", "unknown"])


def test_orchestrator_run_tolerates_none_writer_payload(monkeypatch):
    class FakeResearchAgent:
        def run(self, topic):
            return [{"url": "https://x.com"}]

    class FakeAnalysisAgent:
        def run(self, sources, topic):
            return ["https://x.com"]

    class FakeKnowledgeAgent:
        def build(self, topic, urls):
            return "note"

    class FakeWriterAgent:
        def write(self, topic, content, urls, **kwargs):
            return None

    monkeypatch.setattr(orch_module, "ResearchAgent", FakeResearchAgent)
    monkeypatch.setattr(orch_module, "AnalysisAgent", FakeAnalysisAgent)
    monkeypatch.setattr(orch_module, "KnowledgeAgent", FakeKnowledgeAgent)
    monkeypatch.setattr(orch_module, "WriterAgent", FakeWriterAgent)

    Orchestrator().run("AI Agent Framework")


def test_workflow_server_can_transition_matrix():
    assert workflow_server.can_transition("idle", "running") is True
    assert workflow_server.can_transition("running", "paused") is True
    assert workflow_server.can_transition("paused", "running") is True
    assert workflow_server.can_transition("running", "running") is False
    assert workflow_server.can_transition("unknown", "running") is False


def test_workflow_server_parse_line_extracts_run_id_and_error_code():
    workflow_server.parse_line("Pipeline started run_id=abc123 code=SOURCE_FETCH_FAILED")

    with workflow_server.STATE.lock:
        assert workflow_server.STATE.run_id == "abc123"
        assert workflow_server.STATE.error_code == "SOURCE_FETCH_FAILED"


def test_workflow_server_compute_steps_done_has_full_progress():
    steps, progress = workflow_server.compute_steps("", "done")

    assert progress == 100
    assert all(step["status"] == "done" for step in steps)


def test_workflow_server_start_run_rejects_invalid_transition(monkeypatch):
    with workflow_server.STATE.lock:
        workflow_server.STATE.process = None
        workflow_server.STATE.status = "running"

    code, payload = workflow_server.start_run({"topic": "AI Agent Framework"})

    assert code == 409
    assert "invalid state transition" in payload["error"]


def test_workflow_server_retry_current_step_uses_recovery_payload(monkeypatch):
    with workflow_server.STATE.lock:
        workflow_server.STATE.process = None
        workflow_server.STATE.status = "idle"
        workflow_server.STATE.last_payload = {}

    monkeypatch.setattr(workflow_server, "load_recovery", lambda: {"payload": {"topic": "AI Agent Framework"}})

    captured = {}

    def fake_start_run(payload):
        captured["payload"] = payload
        return 200, {"ok": True}

    monkeypatch.setattr(workflow_server, "start_run", fake_start_run)

    code, response = workflow_server.retry_current_step()

    assert code == 200
    assert response["ok"] is True
    assert captured["payload"]["topic"] == "AI Agent Framework"


def test_workflow_server_retry_current_step_prefers_last_payload(monkeypatch):
    with workflow_server.STATE.lock:
        workflow_server.STATE.process = None
        workflow_server.STATE.status = "idle"
        workflow_server.STATE.last_payload = {"topic": "FromLastPayload"}

    monkeypatch.setattr(workflow_server, "load_recovery", lambda: {"payload": {"topic": "FromRecovery"}})

    captured = {}

    def fake_start_run(payload):
        captured["payload"] = payload
        return 200, {"ok": True}

    monkeypatch.setattr(workflow_server, "start_run", fake_start_run)

    code, response = workflow_server.retry_current_step()

    assert code == 200
    assert response["ok"] is True
    assert captured["payload"]["topic"] == "FromLastPayload"


def test_workflow_server_get_state_returns_recovery_fields(monkeypatch):
    with workflow_server.STATE.lock:
        workflow_server.STATE.status = "idle"
        workflow_server.STATE.topic = "AI Agent Framework"
        workflow_server.STATE.logs = []
        workflow_server.STATE.run_id = "run-x"
        workflow_server.STATE.error_code = ""
        workflow_server.STATE.last_payload = {"topic": "AI Agent Framework"}
        workflow_server.STATE.result = {}

    monkeypatch.setattr(workflow_server, "save_recovery", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        workflow_server,
        "load_recovery",
        lambda: {"last_step": "analysis", "status": "error", "payload": {"topic": "AI Agent Framework"}},
    )

    state = workflow_server.get_state()

    assert state["recovery"]["can_retry"] is True
    assert state["recovery"]["last_step"] == "analysis"
    assert state["recovery"]["checkpoint_status"] == "error"


def test_workflow_server_retry_current_step_rejects_when_running():
    with workflow_server.STATE.lock:
        workflow_server.STATE.process = object()
        workflow_server.STATE.status = "running"

    code, payload = workflow_server.retry_current_step()

    assert code == 409
    assert payload["error"] == "process is running"


def test_workflow_server_retry_current_step_rejects_without_payload(monkeypatch):
    with workflow_server.STATE.lock:
        workflow_server.STATE.process = None
        workflow_server.STATE.status = "idle"
        workflow_server.STATE.last_payload = {}

    monkeypatch.setattr(workflow_server, "load_recovery", lambda: {})

    code, payload = workflow_server.retry_current_step()

    assert code == 409
    assert payload["error"] == "no recovery payload"


def test_workflow_server_get_state_running_disables_retry(monkeypatch):
    with workflow_server.STATE.lock:
        workflow_server.STATE.status = "running"
        workflow_server.STATE.topic = "AI Agent Framework"
        workflow_server.STATE.logs = []
        workflow_server.STATE.run_id = "run-y"
        workflow_server.STATE.error_code = ""
        workflow_server.STATE.last_payload = {"topic": "AI Agent Framework"}
        workflow_server.STATE.result = {}

    monkeypatch.setattr(workflow_server, "save_recovery", lambda *args, **kwargs: None)
    monkeypatch.setattr(workflow_server, "load_recovery", lambda: {"payload": {"topic": "AI Agent Framework"}})

    state = workflow_server.get_state()

    assert state["status"] == "running"
    assert state["recovery"]["can_retry"] is False


def test_workflow_server_reset_run_saves_idle_recovery(monkeypatch):
    captured = {}

    def fake_save_recovery(topic, payload, status, steps):
        captured["topic"] = topic
        captured["payload"] = payload
        captured["status"] = status
        captured["steps"] = steps

    monkeypatch.setattr(workflow_server, "save_recovery", fake_save_recovery)

    with workflow_server.STATE.lock:
        workflow_server.STATE.process = None
        workflow_server.STATE.status = "error"
        workflow_server.STATE.topic = "AI Agent Framework"
        workflow_server.STATE.logs = ["x"]
        workflow_server.STATE.run_id = "run-z"
        workflow_server.STATE.error_code = "SOURCE_FETCH_FAILED"
        workflow_server.STATE.started_at = 1.0
        workflow_server.STATE.paused = True
        workflow_server.STATE.exit_code = 1
        workflow_server.STATE.result = {"status": "failed"}

    code, payload = workflow_server.reset_run()

    assert code == 200
    assert payload["ok"] is True
    assert captured["topic"] == ""
    assert captured["payload"] == {}
    assert captured["status"] == "idle"
    assert captured["steps"] == []


def test_workflow_server_start_run_sets_last_payload(monkeypatch):
    class FakeProc:
        def __init__(self):
            self.pid = 12345
            self.stdout = []

    class FakeThread:
        def __init__(self, target=None, daemon=None):
            self.target = target
            self.daemon = daemon

        def start(self):
            return None

    monkeypatch.setattr(workflow_server.subprocess, "Popen", lambda *args, **kwargs: FakeProc())
    monkeypatch.setattr(workflow_server.threading, "Thread", FakeThread)
    monkeypatch.setattr(workflow_server, "save_recovery", lambda *args, **kwargs: None)

    with workflow_server.STATE.lock:
        workflow_server.STATE.process = None
        workflow_server.STATE.status = "idle"

    code, payload = workflow_server.start_run({"topic": "AI Agent Framework", "max_results": 8, "timeout_seconds": 30, "retries": 2})

    assert code == 200
    assert payload["ok"] is True
    with workflow_server.STATE.lock:
        assert workflow_server.STATE.status == "running"
        assert workflow_server.STATE.last_payload["topic"] == "AI Agent Framework"
        assert workflow_server.STATE.last_payload["max_results"] == 8


def test_workflow_server_finalize_process_marks_done_and_saves_recovery(monkeypatch):
    class FakeProc:
        def wait(self):
            return 0

    captured = {}

    def fake_save_recovery(topic, payload, status, steps):
        captured["topic"] = topic
        captured["payload"] = payload
        captured["status"] = status
        captured["steps"] = steps

    with workflow_server.STATE.lock:
        workflow_server.STATE.process = FakeProc()
        workflow_server.STATE.status = "running"
        workflow_server.STATE.topic = "AI Agent Framework"
        workflow_server.STATE.logs = ["Research completed"]
        workflow_server.STATE.error_code = ""
        workflow_server.STATE.last_payload = {"topic": "AI Agent Framework"}

    monkeypatch.setattr(workflow_server, "read_run_result", lambda topic: {"status": "ok"})
    monkeypatch.setattr(workflow_server, "normalize_result_contract", lambda topic, result: result)
    monkeypatch.setattr(workflow_server, "save_recovery", fake_save_recovery)

    workflow_server.finalize_process()

    with workflow_server.STATE.lock:
        assert workflow_server.STATE.status == "done"
        assert workflow_server.STATE.exit_code == 0
        assert workflow_server.STATE.process is None
        assert workflow_server.STATE.paused is False
        assert workflow_server.STATE.result["status"] == "ok"
    assert captured["status"] == "done"


def test_workflow_server_finalize_process_sets_unexpected_error_on_failure(monkeypatch):
    class FakeProc:
        def wait(self):
            return 1

    with workflow_server.STATE.lock:
        workflow_server.STATE.process = FakeProc()
        workflow_server.STATE.status = "running"
        workflow_server.STATE.topic = "AI Agent Framework"
        workflow_server.STATE.logs = ["Prepare NotebookLM sources"]
        workflow_server.STATE.error_code = ""
        workflow_server.STATE.last_payload = {"topic": "AI Agent Framework"}

    monkeypatch.setattr(workflow_server, "read_run_result", lambda topic: {})
    monkeypatch.setattr(workflow_server, "normalize_result_contract", lambda topic, result: result)
    monkeypatch.setattr(workflow_server, "save_recovery", lambda *args, **kwargs: None)

    workflow_server.finalize_process()

    with workflow_server.STATE.lock:
        assert workflow_server.STATE.status == "error"
        assert workflow_server.STATE.exit_code == 1
        assert workflow_server.STATE.error_code == "UNEXPECTED_ERROR"
        assert workflow_server.STATE.process is None


def test_workflow_server_start_run_requires_topic():
    code, payload = workflow_server.start_run({"topic": "   "})

    assert code == 400
    assert payload["error"] == "topic is required"


def test_workflow_server_finalize_process_keeps_idle_status(monkeypatch):
    class FakeProc:
        def wait(self):
            return 1

    with workflow_server.STATE.lock:
        workflow_server.STATE.process = FakeProc()
        workflow_server.STATE.status = "idle"
        workflow_server.STATE.topic = "AI Agent Framework"
        workflow_server.STATE.logs = []
        workflow_server.STATE.error_code = ""
        workflow_server.STATE.last_payload = {"topic": "AI Agent Framework"}

    monkeypatch.setattr(workflow_server, "read_run_result", lambda topic: {})
    monkeypatch.setattr(workflow_server, "normalize_result_contract", lambda topic, result: result)
    monkeypatch.setattr(workflow_server, "save_recovery", lambda *args, **kwargs: None)

    workflow_server.finalize_process()

    with workflow_server.STATE.lock:
        assert workflow_server.STATE.status == "idle"
        assert workflow_server.STATE.process is None


def test_workflow_server_get_state_prefers_computed_last_step(monkeypatch):
    with workflow_server.STATE.lock:
        workflow_server.STATE.status = "running"
        workflow_server.STATE.topic = "AI Agent Framework"
        workflow_server.STATE.logs = []
        workflow_server.STATE.last_payload = {"topic": "AI Agent Framework"}
        workflow_server.STATE.result = {}

    monkeypatch.setattr(workflow_server, "compute_steps", lambda *_args, **_kwargs: ([{"id": "research", "status": "running"}], 0))
    monkeypatch.setattr(workflow_server, "save_recovery", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        workflow_server,
        "load_recovery",
        lambda: {"last_step": "analysis", "status": "error", "payload": {"topic": "AI Agent Framework"}},
    )

    state = workflow_server.get_state()

    assert state["recovery"]["last_step"] == "research"


def test_workflow_server_get_artifact_content_returns_filename(monkeypatch, tmp_path):
    md_file = tmp_path / "02_Research" / "a.md"
    md_file.parent.mkdir(parents=True, exist_ok=True)
    md_file.write_text("# title", encoding="utf-8")

    monkeypatch.setattr(workflow_server, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        workflow_server,
        "get_history_runs",
        lambda: [
            {
                "run_id": "run-1",
                "topic": "A",
                "artifacts": {"markdown": "02_Research/a.md"},
            }
        ],
    )

    code, payload = workflow_server.get_artifact_content("run-1")

    assert code == 200
    assert payload["content"] == "# title"
    assert payload["filename"] == "a.md"


def test_workflow_server_get_artifact_content_rejects_outside_project(monkeypatch, tmp_path):
    outside = tmp_path.parent / "outside.md"
    outside.write_text("x", encoding="utf-8")

    monkeypatch.setattr(workflow_server, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        workflow_server,
        "get_history_runs",
        lambda: [
            {
                "run_id": "run-2",
                "topic": "B",
                "artifacts": {"markdown": "../outside.md"},
            }
        ],
    )

    code, payload = workflow_server.get_artifact_content("run-2")

    assert code == 400
    assert payload["error"] == "invalid artifact path"


def test_workflow_server_get_artifact_content_rejects_invalid_run_id():
    code, payload = workflow_server.get_artifact_content("../bad")

    assert code == 400
    assert payload["error"] == "invalid run_id"


def test_workflow_server_sanitize_markdown_preview_escapes_html_and_blocks_js_links():
    content = '# Title\n<script>alert("x")</script>\n[Click](javascript:alert(1))\n[Good](https://example.com)'

    sanitized = workflow_server.sanitize_markdown_preview(content)

    assert "<script>" not in sanitized
    assert "&lt;script&gt;" in sanitized
    assert "[Click](#)" in sanitized
    assert "[Good](https://example.com)" in sanitized


def test_workflow_server_get_artifact_content_contains_preview_content(monkeypatch, tmp_path):
    md_file = tmp_path / "02_Research" / "safe.md"
    md_file.parent.mkdir(parents=True, exist_ok=True)
    md_file.write_text("[Click](javascript:alert(1))", encoding="utf-8")

    monkeypatch.setattr(workflow_server, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        workflow_server,
        "get_history_runs",
        lambda: [{"run_id": "run-3", "topic": "C", "artifacts": {"markdown": "02_Research/safe.md"}}],
    )

    code, payload = workflow_server.get_artifact_content("run-3")

    assert code == 200
    assert payload["content"] == "[Click](javascript:alert(1))"
    assert payload["preview_content"] == "[Click](#)"


def test_workflow_server_get_ui_config_returns_unified_status_config():
    config = workflow_server.get_ui_config()

    assert "done" in config["run_statuses"]
    assert "error" in config["run_statuses"]
    assert "done" in config["step_statuses"]
    assert config["status_aliases"]["success"] == "done"
    assert config["link_protocols"] == ["http", "https"]


def test_workflow_server_get_state_normalizes_legacy_status_alias():
    with workflow_server.STATE.lock:
        workflow_server.STATE.status = "success"
        workflow_server.STATE.topic = "AI Agent Framework"
        workflow_server.STATE.logs = []
        workflow_server.STATE.last_payload = {"topic": "AI Agent Framework"}
        workflow_server.STATE.result = {}

    state = workflow_server.get_state()

    assert state["status"] == "done"
