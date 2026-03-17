import logging
import os

from agents.source_contract import extract_urls
from tools.notebooklm.notebooklm_prompt import generate_prompt


logger = logging.getLogger(__name__)


class AnalysisAgent:

    def run(self, sources, topic):

        logger.info("Prepare NotebookLM sources topic=%s", topic)

        urls = extract_urls(sources)

        prompt = generate_prompt(topic, urls)
        os.makedirs("02_Research", exist_ok=True)
        with open("02_Research/notebooklm_input.txt", "w", encoding="utf-8") as file:
            file.write(prompt)

        logger.info("NotebookLM prompt generated topic=%s source_count=%d", topic, len(urls))

        return urls