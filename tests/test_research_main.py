import json
import logging

import agents.research as research_module
from agents.pipeline_error import DEPENDENCY_MISSING, PipelineError, SOURCE_FETCH_FAILED, SSL_CERTIFICATE_VERIFY_FAILED, UNEXPECTED_ERROR


def test_main_returns_pipeline_error_exit_code_and_writes_failure_metadata(monkeypatch):
    captured = {}

    class FakeOrchestrator:
        def run(self, topic, run_id=None):
            raise PipelineError(SOURCE_FETCH_FAILED, "fetch failed")

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

    assert exit_code == PipelineError.EXIT_CODE_BY_ERROR_CODE[SOURCE_FETCH_FAILED]
    assert captured["topic"] == "AI Topic"
    assert captured["error_code"] == SOURCE_FETCH_FAILED
    assert "fetch failed" in captured["error_message"]
    assert isinstance(captured["run_id"], str)
    assert captured["duration_ms"] >= 0


def test_main_passes_same_run_id_to_orchestrator_and_failure_writer(monkeypatch):
    captured = {}

    class FakeOrchestrator:
        def run(self, topic, run_id=None):
            captured["orchestrator_run_id"] = run_id
            raise PipelineError(SOURCE_FETCH_FAILED, "fetch failed")

    class FakeWriterAgent:
        def write_failure_run(self, topic, run_id, error_code, error_message, duration_ms=0):
            captured["writer_run_id"] = run_id
            return {"ok": True}

    monkeypatch.setattr(research_module, "Orchestrator", FakeOrchestrator)
    monkeypatch.setattr(research_module, "WriterAgent", FakeWriterAgent)
    monkeypatch.setattr(research_module.sys, "argv", ["research.py", "AI"])

    exit_code = research_module.main()

    assert exit_code == PipelineError.EXIT_CODE_BY_ERROR_CODE[SOURCE_FETCH_FAILED]
    assert isinstance(captured["orchestrator_run_id"], str)
    assert captured["orchestrator_run_id"]
    assert captured["orchestrator_run_id"] == captured["writer_run_id"]


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

    assert exit_code == PipelineError.EXIT_CODE_BY_ERROR_CODE[UNEXPECTED_ERROR]
    assert captured["error_code"] == UNEXPECTED_ERROR
    assert "boom" in captured["error_message"]


def test_configure_logging_sets_json_formatter_when_enabled(monkeypatch):
    monkeypatch.setenv("LOG_FORMAT", "json")
    root_logger = logging.getLogger()
    old_handlers = root_logger.handlers[:]

    try:
        research_module.configure_logging()
        assert root_logger.handlers
        assert isinstance(root_logger.handlers[0].formatter, research_module.JsonFormatter)
    finally:
        root_logger.handlers.clear()
        for handler in old_handlers:
            root_logger.addHandler(handler)


def test_pipeline_error_exit_code_mapping_covers_standard_codes():
    assert PipelineError.EXIT_CODE_BY_ERROR_CODE[DEPENDENCY_MISSING] == 3
    assert PipelineError.EXIT_CODE_BY_ERROR_CODE[SSL_CERTIFICATE_VERIFY_FAILED] == 4
    assert PipelineError.EXIT_CODE_BY_ERROR_CODE[SOURCE_FETCH_FAILED] == 5
    assert PipelineError.EXIT_CODE_BY_ERROR_CODE[UNEXPECTED_ERROR] == 2


def test_pipeline_error_uses_fallback_exit_code_for_unknown_code():
    error = PipelineError("UNKNOWN_ERROR", "x")
    assert error.exit_code == 2


def test_json_formatter_includes_error_context_fields():
    formatter = research_module.JsonFormatter()
    record = logging.makeLogRecord(
        {
            "name": "agents.research",
            "levelno": logging.ERROR,
            "levelname": "ERROR",
            "msg": "Pipeline failed",
            "args": (),
            "run_id": "run-1",
            "topic": "AI",
            "error_code": SOURCE_FETCH_FAILED,
        }
    )

    payload = json.loads(formatter.format(record))

    assert payload["run_id"] == "run-1"
    assert payload["topic"] == "AI"
    assert payload["error_code"] == SOURCE_FETCH_FAILED