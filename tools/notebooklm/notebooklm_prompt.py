def generate_prompt(topic, sources):

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