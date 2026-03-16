import logging
from time import perf_counter
from uuid import uuid4

from .research_agent import ResearchAgent
from .analysis_agent import AnalysisAgent
from .knowledge_agent import KnowledgeAgent
from .writer_agent import WriterAgent


logger = logging.getLogger(__name__)


class Orchestrator:

    def run(self, topic):

        run_id = str(uuid4())
        started_at = perf_counter()
        logger.info("Pipeline started run_id=%s topic=%s", run_id, topic)

        research = ResearchAgent()
        analysis = AnalysisAgent()
        knowledge = KnowledgeAgent()
        writer = WriterAgent()

        sources = research.run(topic)

        urls = analysis.run(sources, topic)

        note = knowledge.build(topic, urls)

        duration_ms = int((perf_counter() - started_at) * 1000)
        run_payload = writer.write(topic, note, urls, run_id=run_id, status="success", duration_ms=duration_ms)

        markdown_path = ""
        if isinstance(run_payload, dict):
            artifacts = run_payload.get("artifacts", {})
            if isinstance(artifacts, dict):
                markdown_path = str(artifacts.get("markdown", ""))

        logger.info("Pipeline finished run_id=%s topic=%s sources=%d duration_ms=%d markdown=%s", run_id, topic, len(urls), duration_ms, markdown_path)