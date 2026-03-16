from agents.research_agent import ResearchAgent
import agents.research_agent as research_module
import tools.youtube_search as youtube_search_module


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


def test_search_youtube_uses_env_configuration(monkeypatch):
    captured = {}

    class FakeYoutubeDL:
        def __init__(self, opts):
            captured["opts"] = opts

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def extract_info(self, query, download=False):
            captured["query"] = query
            captured["download"] = download
            return {"entries": [{"title": "v1", "url": "https://example.com/v1"}]}

    monkeypatch.setenv("YOUTUBE_MAX_RESULTS", "7")
    monkeypatch.setenv("YOUTUBE_TIMEOUT_SECONDS", "25")
    monkeypatch.setenv("YOUTUBE_RETRIES", "4")
    monkeypatch.setattr(youtube_search_module.yt_dlp, "YoutubeDL", FakeYoutubeDL)

    result = youtube_search_module.search_youtube("AI Agent")

    assert captured["query"] == "ytsearch7:AI Agent"
    assert captured["download"] is False
    assert captured["opts"]["socket_timeout"] == 25
    assert captured["opts"]["retries"] == 4
    assert result == [{"title": "v1", "url": "https://example.com/v1"}]
