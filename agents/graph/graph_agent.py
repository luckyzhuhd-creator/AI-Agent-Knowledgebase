"""图谱辅助：从文本中抽取概念并生成双链引用。"""

import re

STOP_WORDS = ["The", "And", "For", "With"]


class GraphAgent:
    """从文本提取候选概念并输出链接标签。"""

    def extract_links(self, text):
        """提取概念词并返回 [[Concept]] 格式链接列表。"""

        words = re.findall(r"[A-Z][a-zA-Z]+", text)

        concepts = []

        for w in words:

            if w not in STOP_WORDS:
                concepts.append(w)

        concepts = list(set(concepts))

        links = []

        for c in concepts[:8]:
            links.append(f"[[{c}]]")

        return links