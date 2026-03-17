def normalize_source(item, platform="unknown", default_score=0.0):
    if not isinstance(item, dict):
        return None

    url = item.get("url", "")
    if not isinstance(url, str):
        return None
    url = url.strip()
    if not url:
        return None

    title = item.get("title", "")
    if not isinstance(title, str):
        title = str(title)
    title = title.strip()

    source_platform = item.get("platform", platform)
    if not isinstance(source_platform, str) or not source_platform.strip():
        source_platform = platform

    score = item.get("score", default_score)
    try:
        score = float(score)
    except (TypeError, ValueError):
        score = float(default_score)

    return {
        "title": title,
        "url": url,
        "platform": source_platform.strip(),
        "score": score,
    }


def normalize_sources(items, platform="unknown", default_score=0.0):
    normalized = []
    for item in items:
        source = normalize_source(item, platform=platform, default_score=default_score)
        if source is not None:
            normalized.append(source)
    return normalized


def extract_urls(sources):
    return [source["url"] for source in normalize_sources(sources)]