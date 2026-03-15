from agents.graph.graph_agent import GraphAgent


class KnowledgeAgent:

    def build(self, topic, urls):

        graph = GraphAgent()

        content = f"# {topic}\n\n"

        content += "## Sources\n"
        for url in urls:
            content += f"- {url}\n"

        links = graph.extract_links("\n".join(urls))

        content += "\n## Related Concepts\n"
        for link in links:
            content += f"- {link}\n"

        content += "\n## Insights\n"
        content += "NotebookLM analysis pending\n"

        return content