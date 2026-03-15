from agents.research_agent import ResearchAgent
import agents.research_agent as research_module


def test_research_agent_run_returns_search_results(monkeypatch):
    def fake_search_youtube(topic):
        return [{"title": "t1", "url": "https://example.com/1"}]

    monkeypatch.setattr(research_module, "search_youtube", fake_search_youtube)

    result = ResearchAgent().run("AI Agent Framework")
    assert result == [
        {
            "title": "t1",
            "url": "https://example.com/1",
            "platform": "youtube",
            "score": 0.0,
        }
    ]
