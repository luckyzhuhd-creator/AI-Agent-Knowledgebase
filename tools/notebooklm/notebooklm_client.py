import asyncio

from notebooklm import NotebookLMClient


async def _run_notebooklm_analysis(topic, urls, prompt):
    async with await NotebookLMClient.from_storage() as client:
        notebook = await client.notebooks.create(topic)
        for url in urls:
            await client.sources.add_url(notebook.id, url, wait=True)

        result = await client.chat.ask(notebook.id, prompt)
        answer = getattr(result, "answer", "")
        if not isinstance(answer, str) or not answer.strip():
            answer = str(result)

        return {
            "notebook_id": notebook.id,
            "answer": answer.strip(),
        }


def run_notebooklm_analysis(topic, urls, prompt):
    if not urls:
        return {"notebook_id": "", "answer": ""}

    coro = _run_notebooklm_analysis(topic=topic, urls=urls, prompt=prompt)
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()