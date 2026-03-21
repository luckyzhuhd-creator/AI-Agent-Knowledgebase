"""Knowledge 阶段：组织来源并构建初始知识笔记。"""

import os

from agents.graph.graph_agent import GraphAgent


class KnowledgeAgent:
    """负责把来源链接整理为结构化文本内容。"""

    def build(self, topic, urls):
        """根据主题与来源 URL 生成知识草稿文本。"""

        graph = GraphAgent()

        content = f"# {topic}\n\n"

        content += "## Sources\n"
        for url in urls:
            content += f"- {url}\n"

        links = graph.extract_links("\n".join(urls))

        content += "\n## Related Concepts\n"
        for link in links:
            content += f"- {link}\n"

        insights = "NotebookLM analysis pending"
        output_path = os.path.join("02_Research", "notebooklm_output.md")
        if os.path.exists(output_path):
            with open(output_path, "r", encoding="utf-8") as file:
                value = file.read().strip()
            if value:
                insights = value

        content += "\n## Insights\n"
        content += insights + "\n"

        return content