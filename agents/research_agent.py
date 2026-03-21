"""Research 阶段：获取并归一化外部来源。"""

import logging
import os
import time

from agents.pipeline_error import (
    DEPENDENCY_MISSING,
    PipelineError,
    SOURCE_FETCH_FAILED,
    SOURCE_FETCH_RATE_LIMITED,
    SOURCE_FETCH_TIMEOUT,
    SOURCE_FETCH_UNAVAILABLE,
    SSL_CERTIFICATE_VERIFY_FAILED,
)
from agents.source_contract import normalize_sources_with_report
from tools.youtube_search import search_youtube


logger = logging.getLogger(__name__)


def _read_int_env(name, default, minimum, maximum):
    value = os.getenv(name, str(default)).strip()
    try:
        parsed = int(value)
    except ValueError:
        parsed = default
    return max(minimum, min(maximum, parsed))


def _classify_fetch_error(exc):
    error_text = str(exc)
    lowered = error_text.lower()

    if "certificate_verify_failed" in lowered:
        return (
            SSL_CERTIFICATE_VERIFY_FAILED,
            "YouTube SSL verification failed. Ensure certifi is installed and SSL_CERT_FILE is configured.",
        )
    if "timed out" in lowered or "timeout" in lowered:
        return (
            SOURCE_FETCH_TIMEOUT,
            "Source fetch timed out. Retry later or increase timeout settings.",
        )
    if "429" in lowered or "rate limit" in lowered or "too many requests" in lowered:
        return (
            SOURCE_FETCH_RATE_LIMITED,
            "Source fetch was rate limited by upstream provider.",
        )
    if "503" in lowered or "service unavailable" in lowered or "temporarily unavailable" in lowered:
        return (
            SOURCE_FETCH_UNAVAILABLE,
            "Source fetch service is temporarily unavailable.",
        )
    return (
        SOURCE_FETCH_FAILED,
        None,
    )


class ResearchAgent:
    """负责检索原始来源并转换为 Source 契约。"""

    def run(self, topic):
        """按主题检索来源并返回标准化结果。"""

        logger.info(
            "Researching topic=%s",
            topic,
            extra={"topic": topic, "stage": "research", "event": "research_started"},
        )

        retries = _read_int_env("SOURCE_FETCH_RETRIES", 0, 0, 5)
        backoff_ms = _read_int_env("SOURCE_FETCH_BACKOFF_MS", 300, 50, 5000)

        last_error = None
        for attempt in range(retries + 1):
            try:
                raw_sources = search_youtube(topic)
                break
            except ModuleNotFoundError as exc:
                if exc.name == "yt_dlp":
                    raise PipelineError(
                        code=DEPENDENCY_MISSING,
                        message="Missing dependency: yt-dlp. Install with './.venv/bin/python -m pip install yt-dlp'.",
                    ) from exc
                raise
            except Exception as exc:
                last_error = exc
                if attempt < retries:
                    logger.warning(
                        "Source fetch retry topic=%s attempt=%d/%d error=%s",
                        topic,
                        attempt + 1,
                        retries + 1,
                        str(exc),
                        extra={"topic": topic, "stage": "research", "event": "source_fetch_retry"},
                    )
                    time.sleep(backoff_ms / 1000.0)
                    continue
                error_code, error_message = _classify_fetch_error(exc)
                raise PipelineError(
                    code=error_code,
                    message=error_message or f"Failed to fetch sources topic={topic}",
                ) from exc
        else:
            raise PipelineError(
                code=SOURCE_FETCH_FAILED,
                message=f"Failed to fetch sources topic={topic}",
            ) from last_error

        normalized_sources, invalid_count = normalize_sources_with_report(raw_sources, platform="youtube")
        if invalid_count:
            logger.warning(
                "Research dropped invalid sources topic=%s invalid_count=%d",
                topic,
                invalid_count,
                extra={
                    "topic": topic,
                    "stage": "research",
                    "event": "source_schema_filtered",
                    "invalid_count": invalid_count,
                },
            )

        logger.info(
            "Research completed topic=%s source_count=%d",
            topic,
            len(normalized_sources),
            extra={
                "topic": topic,
                "stage": "research",
                "event": "research_completed",
                "source_count": len(normalized_sources),
                "invalid_count": invalid_count,
            },
        )
        return normalized_sources
