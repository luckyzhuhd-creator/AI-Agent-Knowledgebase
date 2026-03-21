"""流水线编排器：串联各 Agent 执行完整研究流程。"""

import logging
from time import perf_counter
from uuid import uuid4

from .research_agent import ResearchAgent
from .analysis_agent import AnalysisAgent
from .knowledge_agent import KnowledgeAgent
from .writer_agent import RUN_STATUS_SUCCESS, WriterAgent


logger = logging.getLogger(__name__)


class Orchestrator:
    """负责顺序执行 research/analysis/knowledge/writer。"""

    STAGE_ORDER = ("research", "analysis", "knowledge", "writer")

    def create_skills(self, topic, run_id, started_at):
        """创建并返回当前运行可用的阶段技能注册表。"""

        research = ResearchAgent()
        analysis = AnalysisAgent()
        knowledge = KnowledgeAgent()
        writer = WriterAgent()

        def run_research(context):
            context["sources"] = research.run(topic)
            return context

        def run_analysis(context):
            context["urls"] = analysis.run(context.get("sources", []), topic)
            return context

        def run_knowledge(context):
            context["note"] = knowledge.build(topic, context.get("urls", []))
            return context

        def run_writer(context):
            duration_ms = int((perf_counter() - started_at) * 1000)
            context["run_payload"] = writer.write(
                topic,
                context.get("note", ""),
                context.get("urls", []),
                run_id=run_id,
                status=RUN_STATUS_SUCCESS,
                duration_ms=duration_ms,
                sources=context.get("sources", []),
            )
            context["duration_ms"] = duration_ms
            return context

        return {
            "research": run_research,
            "analysis": run_analysis,
            "knowledge": run_knowledge,
            "writer": run_writer,
        }

    def run_super_skill(self, topic, run_id=None, stages=None):
        """按技能阶段编排执行并返回运行上下文。"""

        run_id = run_id or str(uuid4())
        started_at = perf_counter()
        logger.info(
            "Pipeline started run_id=%s topic=%s",
            run_id,
            topic,
            extra={"run_id": run_id, "topic": topic, "stage": "orchestrator", "event": "pipeline_started"},
        )

        stage_order = list(stages) if stages else list(self.STAGE_ORDER)
        invalid_stages = [name for name in stage_order if name not in self.STAGE_ORDER]
        if invalid_stages:
            raise ValueError(f"Unknown stages: {','.join(invalid_stages)}")

        skills = self.create_skills(topic, run_id, started_at)
        context = {"run_id": run_id, "topic": topic, "sources": [], "urls": [], "note": "", "run_payload": None, "duration_ms": 0}
        for stage_name in stage_order:
            logger.info(
                "Executing stage run_id=%s topic=%s stage=%s",
                run_id,
                topic,
                stage_name,
                extra={"run_id": run_id, "topic": topic, "stage": "orchestrator", "event": "stage_executing", "step": stage_name},
            )
            context = skills[stage_name](context)

        run_payload = context.get("run_payload")
        urls = context.get("urls", [])
        duration_ms = int(context.get("duration_ms") or int((perf_counter() - started_at) * 1000))

        markdown_path = ""
        if isinstance(run_payload, dict):
            artifacts = run_payload.get("artifacts", {})
            if isinstance(artifacts, dict):
                markdown_path = str(artifacts.get("markdown", ""))

        logger.info(
            "Pipeline finished run_id=%s topic=%s sources=%d duration_ms=%d markdown=%s",
            run_id,
            topic,
            len(urls),
            duration_ms,
            markdown_path,
            extra={
                "run_id": run_id,
                "topic": topic,
                "stage": "orchestrator",
                "event": "pipeline_completed",
                "status": "success",
                "source_count": len(urls),
                "duration_ms": duration_ms,
            },
        )

        return context

    def run(self, topic, run_id=None):
        """执行一次完整流水线并返回写入阶段产物信息。"""

        context = self.run_super_skill(topic, run_id=run_id)
        return context.get("run_payload")
