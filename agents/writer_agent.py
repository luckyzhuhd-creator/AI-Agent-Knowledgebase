import json
import logging
import os
import re
from datetime import datetime, timezone
from uuid import uuid4


logger = logging.getLogger(__name__)


RUN_SCHEMA_VERSION = "1.2"
RUN_STATUS_SUCCESS = "success"
RUN_STATUS_FAILED = "failed"


class WriterAgent:

    def slugify(self, topic):

        slug = topic.strip().lower()
        slug = re.sub(r"[^a-z0-9\s_-]", "", slug)
        slug = re.sub(r"\s+", "_", slug)
        slug = re.sub(r"_+", "_", slug)
        return slug or "untitled"

    def _build_run_payload(self, topic, run_id, status, duration_ms, source_count, artifacts, error_code="", error_message=""):

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
            "artifacts": artifacts,
        }

    def write(self, topic, content, urls, run_id=None, status=RUN_STATUS_SUCCESS, duration_ms=0):

        directory = "02_Research"
        os.makedirs(directory, exist_ok=True)

        slug = self.slugify(topic)
        md_path = os.path.join(directory, f"{slug}.md")
        json_path = os.path.join(directory, f"{slug}.json")
        run_path = os.path.join(directory, f"{slug}.run.json")

        with open(md_path, "w", encoding="utf-8") as file:
            file.write(content)

        with open(json_path, "w", encoding="utf-8") as file:
            json.dump({"topic": topic, "sources": urls, "content": content}, file, ensure_ascii=False, indent=2)

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

        logger.info("Note created md=%s json=%s run=%s", md_path, json_path, run_path)

        return run_payload

    def write_failure_run(self, topic, run_id, error_code, error_message, duration_ms=0):

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

        logger.info("Failure metadata written run=%s code=%s", run_path, error_code)

        return run_payload
