from pathlib import Path

from agents.analysis_agent import AnalysisAgent
import agents.analysis_agent as analysis_module


def test_analysis_agent_handles_empty_sources(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    Path("02_Research").mkdir(parents=True, exist_ok=True)

    def fake_prompt(topic, sources):
        return f"TOPIC={topic}\nSOURCES={len(sources)}"

    monkeypatch.setattr(analysis_module, "generate_prompt", fake_prompt)

    urls = AnalysisAgent().run([], "Empty Topic")
    assert urls == []

    content = Path("02_Research/notebooklm_input.txt").read_text()
    assert "TOPIC=Empty Topic" in content
    assert "SOURCES=0" in content
