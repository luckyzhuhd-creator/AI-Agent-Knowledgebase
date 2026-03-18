import json
from pathlib import Path

from agents.writer_agent import RUN_SCHEMA_VERSION, RUN_STATUS_FAILED, RUN_STATUS_SUCCESS, WriterAgent


def test_writer_agent_writes_artifacts(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    payload = WriterAgent().write(
        "AI Agent Framework",
        "# title\n\ncontent",
        ["https://a.com", "https://b.com"],
    )

    md = Path(payload["artifacts"]["markdown"])
    js = Path(payload["artifacts"]["json"])
    run = Path(payload["artifacts"]["run"])

    assert md.exists()
    assert js.exists()
    assert run.exists()

    run_data = json.loads(run.read_text(encoding="utf-8"))
    assert run_data["schema_version"] == RUN_SCHEMA_VERSION
    assert isinstance(run_data["run_id"], str)
    assert run_data["run_id"]
    assert run_data["status"] == RUN_STATUS_SUCCESS
    assert run_data["duration_ms"] >= 0
    assert run_data["error_code"] == ""
    assert run_data["error_message"] == ""
    assert run_data["topic"] == "AI Agent Framework"
    assert run_data["source_count"] == 2
    assert run_data["artifacts"]["markdown"].endswith("ai_agent_framework.md")
    assert run_data["artifacts"]["json"].endswith("ai_agent_framework.json")
    assert run_data["artifacts"]["run"].endswith("ai_agent_framework.run.json")


def test_writer_agent_writes_failure_run_metadata(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    payload = WriterAgent().write_failure_run(
        topic="Failure Topic",
        run_id="run-123",
        error_code="SOURCE_FETCH_FAILED",
        error_message="timeout",
        duration_ms=42,
    )

    run = Path(payload["artifacts"]["run"])
    assert run.exists()

    run_data = json.loads(run.read_text(encoding="utf-8"))
    assert run_data["schema_version"] == RUN_SCHEMA_VERSION
    assert run_data["run_id"] == "run-123"
    assert run_data["status"] == RUN_STATUS_FAILED
    assert run_data["duration_ms"] == 42
    assert run_data["error_code"] == "SOURCE_FETCH_FAILED"
    assert run_data["error_message"] == "timeout"
    assert run_data["source_count"] == 0
