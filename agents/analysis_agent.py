import logging
import os

from tools.notebooklm.notebooklm_prompt import generate_prompt


logger = logging.getLogger(__name__)


class AnalysisAgent:

    def run(self, sources, topic):

        logger.info("Prepare NotebookLM sources topic=%s", topic)

        urls = []
        for source in sources:
            if isinstance(source, dict):
                url = source.get("url", "")
            else:
                logger.warning("Skip non-standard source item type=%s", type(source).__name__)
                url = ""

            if isinstance(url, str):
                url = url.strip()

            if url:
                urls.append(url)

        prompt = generate_prompt(topic, urls)
        os.makedirs("02_Research", exist_ok=True)
        with open("02_Research/notebooklm_input.txt", "w", encoding="utf-8") as file:
            file.write(prompt)

        logger.info("NotebookLM prompt generated topic=%s source_count=%d", topic, len(urls))

        return urls