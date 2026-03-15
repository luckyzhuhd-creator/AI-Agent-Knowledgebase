import json
import logging
import os
import re
from datetime import datetime, timezone


logger = logging.getLogger(__name__)


class WriterAgent:

    def slugify(self, topic):

        slug = topic.strip().lower()
        slug = re.sub(r"[^a-z0-9\s_-]", "", slug)
        slug = re.sub(r"\s+", "_", slug)
        slug = re.sub(r"_+", "_", slug)
        return slug or "untitled"

    def write(self, topic, content, urls):

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

        run_payload = {
            "schema_version": "1.0",
            "topic": topic,
            "source_count": len(urls),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "artifacts": {
                "markdown": md_path,
                "json": json_path,
                "run": run_path,
            },
        }

        with open(run_path, "w", encoding="utf-8") as file:
            json.dump(run_payload, file, ensure_ascii=False, indent=2)

        logger.info("Note created md=%s json=%s run=%s", md_path, json_path, run_path)

        return run_payload
