import pytest

from agents.pipeline_error import DEPENDENCY_MISSING, PipelineError, SOURCE_FETCH_FAILED, SSL_CERTIFICATE_VERIFY_FAILED
from agents.research_agent import ResearchAgent
import agents.research_agent as research_module


def test_research_agent_raises_runtime_error_when_yt_dlp_missing(monkeypatch):
    def fake_search_youtube(_topic):
        raise ModuleNotFoundError("No module named 'yt_dlp'", name="yt_dlp")

    monkeypatch.setattr(research_module, "search_youtube", fake_search_youtube)

    with pytest.raises(PipelineError, match="Missing dependency: yt-dlp") as exc_info:
        ResearchAgent().run("AI Agent Framework")

    assert exc_info.value.code == DEPENDENCY_MISSING
    assert exc_info.value.exit_code == PipelineError.EXIT_CODE_BY_ERROR_CODE[DEPENDENCY_MISSING]


def test_research_agent_raises_runtime_error_when_ssl_verification_failed(monkeypatch):
    def fake_search_youtube(_topic):
        raise RuntimeError("[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed")

    monkeypatch.setattr(research_module, "search_youtube", fake_search_youtube)

    with pytest.raises(PipelineError, match="YouTube SSL verification failed") as exc_info:
        ResearchAgent().run("AI Agent Framework")

    assert exc_info.value.code == SSL_CERTIFICATE_VERIFY_FAILED
    assert exc_info.value.exit_code == PipelineError.EXIT_CODE_BY_ERROR_CODE[SSL_CERTIFICATE_VERIFY_FAILED]


def test_research_agent_raises_runtime_error_when_source_fetch_failed(monkeypatch):
    def fake_search_youtube(_topic):
        raise RuntimeError("gateway timeout")

    monkeypatch.setattr(research_module, "search_youtube", fake_search_youtube)

    with pytest.raises(PipelineError, match="Failed to fetch sources") as exc_info:
        ResearchAgent().run("AI Agent Framework")

    assert exc_info.value.code == SOURCE_FETCH_FAILED
    assert exc_info.value.exit_code == PipelineError.EXIT_CODE_BY_ERROR_CODE[SOURCE_FETCH_FAILED]
