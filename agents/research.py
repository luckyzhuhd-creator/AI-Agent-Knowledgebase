import json
import logging
import os
import sys
from pathlib import Path
from time import perf_counter
from uuid import uuid4

if __package__ in (None, ""):
    project_root = str(Path(__file__).resolve().parents[1])
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from agents.orchestrator import Orchestrator
from agents.pipeline_error import PipelineError, UNEXPECTED_ERROR
from agents.writer_agent import WriterAgent


class JsonFormatter(logging.Formatter):

    OPTIONAL_FIELDS = ("run_id", "topic", "error_code")

    def format(self, record):
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
        }
        for field in self.OPTIONAL_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        return json.dumps(payload, ensure_ascii=False)


def configure_logging():

    if os.getenv("LOG_FORMAT", "plain").lower() == "json":
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)
        return

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")


def main():

    configure_logging()
    logger = logging.getLogger(__name__)
    writer = WriterAgent()

    if len(sys.argv) < 2:
        logger.error("Usage: python -m agents.research <topic>")
        return 1

    topic = " ".join(sys.argv[1:]).strip()
    run_id = str(uuid4())
    started_at = perf_counter()
    logger.info("Starting research run_id=%s topic=%s", run_id, topic)

    try:
        Orchestrator().run(topic, run_id=run_id)
    except PipelineError as exc:
        duration_ms = int((perf_counter() - started_at) * 1000)
        writer.write_failure_run(topic, run_id, exc.code, str(exc), duration_ms=duration_ms)
        logger.error(
            "Pipeline failed run_id=%s topic=%s code=%s message=%s",
            run_id,
            topic,
            exc.code,
            str(exc),
            extra={"run_id": run_id, "topic": topic, "error_code": exc.code},
        )
        return exc.exit_code
    except Exception as exc:
        duration_ms = int((perf_counter() - started_at) * 1000)
        writer.write_failure_run(topic, run_id, UNEXPECTED_ERROR, str(exc), duration_ms=duration_ms)
        logger.exception(
            "Pipeline failed run_id=%s topic=%s code=UNEXPECTED_ERROR",
            run_id,
            topic,
            extra={"run_id": run_id, "topic": topic, "error_code": UNEXPECTED_ERROR},
        )
        return PipelineError.EXIT_CODE_BY_ERROR_CODE[UNEXPECTED_ERROR]

    return 0


if __name__ == "__main__":
    raise SystemExit(main())