import logging

from tools.youtube_search import search_youtube


logger = logging.getLogger(__name__)


class ResearchAgent:

    def run(self, topic):

        logger.info("Researching topic=%s", topic)

        try:
            raw_sources = search_youtube(topic)
        except ModuleNotFoundError as exc:
            if exc.name == "yt_dlp":
                raise RuntimeError("Missing dependency: yt-dlp. Install with './.venv/bin/python -m pip install yt-dlp'.") from exc
            raise
        except Exception as exc:
            error_text = str(exc)
            if "CERTIFICATE_VERIFY_FAILED" in error_text:
                raise RuntimeError("YouTube SSL verification failed. Ensure certifi is installed and SSL_CERT_FILE is configured.") from exc
            raise

        normalized_sources = []
        for item in raw_sources:
            if not isinstance(item, dict):
                continue

            url = item.get("url", "")
            if not isinstance(url, str):
                continue
            url = url.strip()
            if not url:
                continue

            normalized_sources.append(
                {
                    "title": str(item.get("title", "")).strip(),
                    "url": url,
                    "platform": "youtube",
                    "score": 0.0,
                }
            )

        logger.info("Research completed topic=%s source_count=%d", topic, len(normalized_sources))
        return normalized_sources