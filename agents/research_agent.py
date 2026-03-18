import logging

from agents.pipeline_error import DEPENDENCY_MISSING, SSL_CERTIFICATE_VERIFY_FAILED, SOURCE_FETCH_FAILED, UNEXPECTED_ERROR, PipelineError           
from agents.source_contract import normalize_sources
from tools.youtube_search import search_youtube


logger = logging.getLogger(__name__)


class ResearchAgent:

    def run(self, topic):

        logger.info("Researching topic=%s", topic)

        try:
            raw_sources = search_youtube(topic)
        except ModuleNotFoundError as exc:
            if exc.name == "yt_dlp":
                raise PipelineError(
                    code=DEPENDENCY_MISSING,
                    message="Missing dependency: yt-dlp. Install with './.venv/bin/python -m pip install yt-dlp'.",
                ) from exc
            raise
        except Exception as exc:
            error_text = str(exc)
            if "CERTIFICATE_VERIFY_FAILED" in error_text:
                raise PipelineError(
                    code=SSL_CERTIFICATE_VERIFY_FAILED,
                    message="YouTube SSL verification failed. Ensure certifi is installed and SSL_CERT_FILE is configured.",
                ) from exc
            raise PipelineError(
                code=SOURCE_FETCH_FAILED,
                message=f"Failed to fetch sources topic={topic}",
            ) from exc

        normalized_sources = normalize_sources(raw_sources, platform="youtube")

        logger.info("Research completed topic=%s source_count=%d", topic, len(normalized_sources))
        return normalized_sources