from pathlib import Path
from agents.analysis_agent import AnalysisAgent
import agents.analysis_agent as analysis_module


def test_analysis_agent_extracts_urls_and_writes_prompt(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    Path("02_Research").mkdir(parents=True, exist_ok=True)

    def fake_prompt(topic, sources):
        return f"TOPIC={topic}\nSOURCES={len(sources)}"

    monkeypatch.setattr(analysis_module, "generate_prompt", fake_prompt)

    sources = [
        {"title": "a", "url": "https://a.com", "platform": "youtube", "score": 0.0},
        {"title": "b", "url": "  https://b.com  ", "platform": "youtube", "score": 0.0},
        {"title": "invalid", "url": "", "platform": "youtube", "score": 0.0},
        123,
    ]

    urls = AnalysisAgent().run(sources, "T")
    assert urls == ["https://a.com", "https://b.com"]

    content = Path("02_Research/notebooklm_input.txt").read_text()
    assert "TOPIC=T" in content
    assert "SOURCES=2" in content
