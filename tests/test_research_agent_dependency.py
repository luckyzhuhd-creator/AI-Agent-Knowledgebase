import pytest

from agents.research_agent import ResearchAgent
import agents.research_agent as research_module


def test_research_agent_raises_runtime_error_when_yt_dlp_missing(monkeypatch):
    def fake_search_youtube(_topic):
        raise ModuleNotFoundError("No module named 'yt_dlp'", name="yt_dlp")

    monkeypatch.setattr(research_module, "search_youtube", fake_search_youtube)

    with pytest.raises(RuntimeError, match="Missing dependency: yt-dlp"):
        ResearchAgent().run("AI Agent Framework")
