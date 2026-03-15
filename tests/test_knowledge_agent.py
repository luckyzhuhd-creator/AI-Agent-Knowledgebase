from agents.knowledge_agent import KnowledgeAgent
import agents.knowledge_agent as knowledge_module


def test_knowledge_agent_build_contains_sections(monkeypatch):
    class FakeGraphAgent:
        def extract_links(self, text):
            return ["[[AI]]", "[[Agent]]"]

    monkeypatch.setattr(knowledge_module, "GraphAgent", FakeGraphAgent)

    content = KnowledgeAgent().build(
        "AI Agent Framework",
        ["https://a.com", "https://b.com"],
    )

    assert "# AI Agent Framework" in content
    assert "## Sources" in content
    assert "- https://a.com" in content
    assert "## Related Concepts" in content
    assert "- [[AI]]" in content
    assert "## Insights" in content
