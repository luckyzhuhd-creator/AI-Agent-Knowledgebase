import logging

from .research_agent import ResearchAgent
from .analysis_agent import AnalysisAgent
from .knowledge_agent import KnowledgeAgent
from .writer_agent import WriterAgent


logger = logging.getLogger(__name__)


class Orchestrator:

    def run(self, topic):

        logger.info("Pipeline started topic=%s", topic)

        research = ResearchAgent()
        analysis = AnalysisAgent()
        knowledge = KnowledgeAgent()
        writer = WriterAgent()

        sources = research.run(topic)

        urls = analysis.run(sources, topic)

        note = knowledge.build(topic, urls)

        run_payload = writer.write(topic, note, urls)

        markdown_path = ""
        if isinstance(run_payload, dict):
            artifacts = run_payload.get("artifacts", {})
            if isinstance(artifacts, dict):
                markdown_path = str(artifacts.get("markdown", ""))

        logger.info("Pipeline finished topic=%s sources=%d markdown=%s", topic, len(urls), markdown_path)