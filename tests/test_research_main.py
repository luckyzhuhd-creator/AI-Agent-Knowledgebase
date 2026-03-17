import agents.research as research_module
from agents.pipeline_error import PipelineError


def test_main_returns_pipeline_error_exit_code_and_writes_failure_metadata(monkeypatch):
    captured = {}

    class FakeOrchestrator:
        def run(self, topic, run_id=None):
            raise PipelineError("SOURCE_FETCH_FAILED", "fetch failed", exit_code=5)

    class FakeWriterAgent:
        def write_failure_run(self, topic, run_id, error_code, error_message, duration_ms=0):
            captured["topic"] = topic
            captured["run_id"] = run_id
            captured["error_code"] = error_code
            captured["error_message"] = error_message
            captured["duration_ms"] = duration_ms
            return {"ok": True}

    monkeypatch.setattr(research_module, "Orchestrator", FakeOrchestrator)
    monkeypatch.setattr(research_module, "WriterAgent", FakeWriterAgent)
    monkeypatch.setattr(research_module.sys, "argv", ["research.py", "AI", "Topic"])

    exit_code = research_module.main()

    assert exit_code == 5
    assert captured["topic"] == "AI Topic"
    assert captured["error_code"] == "SOURCE_FETCH_FAILED"
    assert "fetch failed" in captured["error_message"]
    assert isinstance(captured["run_id"], str)
    assert captured["duration_ms"] >= 0


def test_main_returns_unexpected_error_code_and_writes_failure_metadata(monkeypatch):
    captured = {}

    class FakeOrchestrator:
        def run(self, topic, run_id=None):
            raise RuntimeError("boom")

    class FakeWriterAgent:
        def write_failure_run(self, topic, run_id, error_code, error_message, duration_ms=0):
            captured["error_code"] = error_code
            captured["error_message"] = error_message
            return {"ok": True}

    monkeypatch.setattr(research_module, "Orchestrator", FakeOrchestrator)
    monkeypatch.setattr(research_module, "WriterAgent", FakeWriterAgent)
    monkeypatch.setattr(research_module.sys, "argv", ["research.py", "AI"])

    exit_code = research_module.main()

    assert exit_code == 2
    assert captured["error_code"] == "UNEXPECTED_ERROR"
    assert "boom" in captured["error_message"]