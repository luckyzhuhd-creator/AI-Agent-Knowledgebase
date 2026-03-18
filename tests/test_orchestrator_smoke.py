from agents.orchestrator import Orchestrator
from agents.writer_agent import RUN_STATUS_SUCCESS
import agents.orchestrator as orch_module


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
