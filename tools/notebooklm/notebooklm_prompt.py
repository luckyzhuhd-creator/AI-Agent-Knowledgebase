"""NotebookLM 输入提示词构建器。"""


def generate_prompt(topic, sources):
    """根据主题与来源列表生成标准分析提示词。"""

    prompt = f"""
Template Version: v1
Research topic: {topic}

Sources:
"""

    for source in sources:
        prompt += f"- {source}\n"

    prompt += """

Please provide:

1. Summary
2. Key concepts
3. Architecture explanation
4. Important insights

Output format:
- Use concise bullet points
- Keep all claims traceable to provided sources
- End with a short action plan
"""

    return prompt