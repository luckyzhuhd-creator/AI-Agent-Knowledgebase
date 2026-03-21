"""Analysis 阶段：提取 URL 并生成 NotebookLM 输入文件。"""

import json
import logging
import os

from agents.source_contract import extract_urls_with_report
from tools.notebooklm.notebooklm_prompt import generate_prompt


logger = logging.getLogger(__name__)


def _is_notebooklm_enabled():
    return os.getenv("NOTEBOOKLM_AUTO_ANALYZE", "0").strip().lower() in {"1", "true", "yes", "on"}


class AnalysisAgent:
    """负责将来源转换为可分析输入。"""

    def run(self, sources, topic):
        """提取有效 URL，生成提示词文件，并返回 URL 列表。"""

        logger.info(
            "Prepare NotebookLM sources topic=%s",
            topic,
            extra={"topic": topic, "stage": "analysis", "event": "analysis_started"},
        )

        urls, invalid_count = extract_urls_with_report(sources)
        if invalid_count:
            logger.warning(
                "Analysis dropped invalid sources topic=%s invalid_count=%d",
                topic,
                invalid_count,
                extra={
                    "topic": topic,
                    "stage": "analysis",
                    "event": "source_schema_filtered",
                    "invalid_count": invalid_count,
                },
            )

        prompt = generate_prompt(topic, urls)
        os.makedirs("02_Research", exist_ok=True)
        with open("02_Research/notebooklm_input.txt", "w", encoding="utf-8") as file:
            file.write(prompt)

        logger.info(
            "NotebookLM prompt generated topic=%s source_count=%d",
            topic,
            len(urls),
            extra={
                "topic": topic,
                "stage": "analysis",
                "event": "analysis_prompt_generated",
                "source_count": len(urls),
                "invalid_count": invalid_count,
            },
        )

        if _is_notebooklm_enabled() and urls:
            try:
                from tools.notebooklm.notebooklm_client import run_notebooklm_analysis

                result = run_notebooklm_analysis(topic=topic, urls=urls, prompt=prompt)
                answer = str(result.get("answer", "")).strip()
                notebook_id = str(result.get("notebook_id", ""))

                with open("02_Research/notebooklm_output.md", "w", encoding="utf-8") as file:
                    file.write(answer)

                notebook_url = f"https://notebooklm.google.com/notebook/{notebook_id}" if notebook_id else ""
                with open("02_Research/notebooklm_session.json", "w", encoding="utf-8") as file:
                    json.dump(
                        {
                            "topic": topic,
                            "notebook_id": notebook_id,
                            "notebook_url": notebook_url,
                            "source_count": len(urls),
                        },
                        file,
                        ensure_ascii=False,
                        indent=2,
                    )

                logger.info(
                    "NotebookLM analysis completed topic=%s notebook_id=%s",
                    topic,
                    notebook_id,
                    extra={"topic": topic, "stage": "analysis", "event": "notebooklm_completed"},
                )
            except Exception:
                logger.exception(
                    "NotebookLM analysis failed topic=%s",
                    topic,
                    extra={"topic": topic, "stage": "analysis", "event": "notebooklm_failed"},
                )

        return urls
