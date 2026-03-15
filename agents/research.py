import logging
import sys

from agents.orchestrator import Orchestrator


def main():

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
    logger = logging.getLogger(__name__)

    if len(sys.argv) < 2:
        logger.error("Usage: python -m agents.research <topic>")
        return 1

    topic = " ".join(sys.argv[1:]).strip()
    logger.info("Starting research topic=%s", topic)

    try:
        Orchestrator().run(topic)
    except Exception:
        logger.exception("Pipeline failed topic=%s", topic)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())