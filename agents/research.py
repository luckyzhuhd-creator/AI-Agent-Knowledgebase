import logging
import sys
from time import perf_counter
from uuid import uuid4

from agents.orchestrator import Orchestrator
from agents.pipeline_error import PipelineError
from agents.writer_agent import WriterAgent


def main():

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
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
        logger.error("Pipeline failed run_id=%s topic=%s code=%s message=%s", run_id, topic, exc.code, str(exc))
        return exc.exit_code
    except Exception as exc:
        duration_ms = int((perf_counter() - started_at) * 1000)
        writer.write_failure_run(topic, run_id, "UNEXPECTED_ERROR", str(exc), duration_ms=duration_ms)
        logger.exception("Pipeline failed run_id=%s topic=%s code=UNEXPECTED_ERROR", run_id, topic)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())