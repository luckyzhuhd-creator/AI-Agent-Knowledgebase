import re

STOP_WORDS = ["The","And","For","With"]

class GraphAgent:

    def extract_links(self, text):

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