"""Writer 阶段：写入研究产物与运行元数据。"""

import json
import logging
import os
import re
from datetime import datetime, timezone
from uuid import uuid4


logger = logging.getLogger(__name__)


RUN_SCHEMA_VERSION = "1.3"
RUN_STATUS_SUCCESS = "success"
RUN_STATUS_FAILED = "failed"


class WriterAgent:
    """负责把研究结果写入文件系统并生成 run 元数据。"""

    def slugify(self, topic):
        """将主题转换为稳定文件名片段。"""

        slug = topic.strip().lower()
        slug = re.sub(r"[^a-z0-9\s_-]", "", slug)
        slug = re.sub(r"\s+", "_", slug)
        slug = re.sub(r"_+", "_", slug)
        return slug or "untitled"

    def _read_notebooklm_session(self, topic):
        path = os.path.join("02_Research", "notebooklm_session.json")
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as file:
                payload = json.load(file)
        except Exception:
            return {}
        if str(payload.get("topic", "")).strip() != topic:
            return {}
        return payload

    def _build_run_payload(self, topic, run_id, status, duration_ms, source_count, artifacts, error_code="", error_message=""):
        """构建统一格式的 run 元数据字典。"""

        session = self._read_notebooklm_session(topic)
        notebook_id = str(session.get("notebook_id", ""))
        notebook_url = str(session.get("notebook_url", ""))

        return {
            "schema_version": RUN_SCHEMA_VERSION,
            "run_id": run_id or str(uuid4()),
            "status": status,
            "duration_ms": int(duration_ms),
            "topic": topic,
            "source_count": int(source_count),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "error_code": error_code,
            "error_message": error_message,
            "notebooklm": {
                "notebook_id": notebook_id,
                "notebook_url": notebook_url,
            },
            "artifacts": artifacts,
        }

    def _build_knowledge_cards(self, urls, sources=None):
        cards = []
        source_items = sources if isinstance(sources, list) else []
        if source_items:
            for index, source in enumerate(source_items, start=1):
                if not isinstance(source, dict):
                    continue
                url = str(source.get("url", "")).strip()
                if not url:
                    continue
                title = str(source.get("title", "")).strip() or f"Source {index}"
                card = {
                    "card_id": f"source-{index}",
                    "title": title,
                    "url": url,
                }
                platform = str(source.get("platform", "")).strip()
                if platform:
                    card["platform"] = platform
                score = source.get("score")
                if isinstance(score, (int, float)):
                    card["score"] = float(score)
                cards.append(card)
            if cards:
                return cards
        for index, url in enumerate(urls, start=1):
            cards.append(
                {
                    "card_id": f"source-{index}",
                    "title": f"Source {index}",
                    "url": str(url),
                }
            )
        return cards

    def write(self, topic, content, urls, run_id=None, status=RUN_STATUS_SUCCESS, duration_ms=0, sources=None):
        """写入 Markdown/JSON 与成功运行元数据。"""

        directory = "02_Research"
        os.makedirs(directory, exist_ok=True)

        slug = self.slugify(topic)
        md_path = os.path.join(directory, f"{slug}.md")
        json_path = os.path.join(directory, f"{slug}.json")
        run_path = os.path.join(directory, f"{slug}.run.json")

        with open(md_path, "w", encoding="utf-8") as file:
            file.write(content)

        with open(json_path, "w", encoding="utf-8") as file:
            json.dump(
                {
                    "topic": topic,
                    "sources": urls,
                    "knowledge_cards": self._build_knowledge_cards(urls, sources=sources),
                    "content": content,
                },
                file,
                ensure_ascii=False,
                indent=2,
            )

        run_payload = self._build_run_payload(
            topic=topic,
            run_id=run_id,
            status=status,
            duration_ms=duration_ms,
            source_count=len(urls),
            artifacts={
                "markdown": md_path,
                "json": json_path,
                "run": run_path,
            },
        )

        with open(run_path, "w", encoding="utf-8") as file:
            json.dump(run_payload, file, ensure_ascii=False, indent=2)

        logger.info(
            "Note created md=%s json=%s run=%s",
            md_path,
            json_path,
            run_path,
            extra={"topic": topic, "stage": "writer", "event": "artifacts_written", "status": status, "source_count": len(urls)},
        )

        return run_payload

    def write_failure_run(self, topic, run_id, error_code, error_message, duration_ms=0):
        """仅写入失败场景的运行元数据文件。"""

        directory = "02_Research"
        os.makedirs(directory, exist_ok=True)

        slug = self.slugify(topic)
        run_path = os.path.join(directory, f"{slug}.run.json")

        run_payload = self._build_run_payload(
            topic=topic,
            run_id=run_id,
            status=RUN_STATUS_FAILED,
            duration_ms=duration_ms,
            source_count=0,
            artifacts={
                "markdown": "",
                "json": "",
                "run": run_path,
            },
            error_code=error_code,
            error_message=error_message,
        )

        with open(run_path, "w", encoding="utf-8") as file:
            json.dump(run_payload, file, ensure_ascii=False, indent=2)

        logger.info(
            "Failure metadata written run=%s code=%s",
            run_path,
            error_code,
            extra={"topic": topic, "stage": "writer", "event": "failure_metadata_written", "status": RUN_STATUS_FAILED, "error_code": error_code},
        )

        return run_payload
