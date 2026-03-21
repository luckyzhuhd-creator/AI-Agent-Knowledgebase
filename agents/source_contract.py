"""Source 数据契约：归一化与 URL 提取。"""

import math


def validate_source_schema(source):
    """校验 Source 是否满足统一 schema。"""
    if not isinstance(source, dict):
        return ["source must be a dict"]

    errors = []

    title = source.get("title")
    if not isinstance(title, str):
        errors.append("title must be a string")

    url = source.get("url")
    if not isinstance(url, str) or not url.strip():
        errors.append("url must be a non-empty string")

    platform = source.get("platform")
    if not isinstance(platform, str) or not platform.strip():
        errors.append("platform must be a non-empty string")

    score = source.get("score")
    if not isinstance(score, (int, float)) or not math.isfinite(float(score)):
        errors.append("score must be a finite number")

    return errors


def normalize_source(item, platform="unknown", default_score=0.0):
    """将单条原始来源转换为标准 Source 结构。"""
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

    candidate = {
        "title": title,
        "url": url,
        "platform": source_platform.strip(),
        "score": score,
    }
    if validate_source_schema(candidate):
        return None
    return candidate


def normalize_sources_with_report(items, platform="unknown", default_score=0.0):
    """批量归一化来源列表并返回无效数量。"""
    normalized = []
    invalid_count = 0
    iterable = items if isinstance(items, list | tuple) else []
    for item in iterable:
        source = normalize_source(item, platform=platform, default_score=default_score)
        if source is None:
            invalid_count += 1
            continue
        normalized.append(source)
    return normalized, invalid_count


def normalize_sources(items, platform="unknown", default_score=0.0):
    """批量归一化来源列表并过滤无效项。"""
    normalized, _ = normalize_sources_with_report(items, platform=platform, default_score=default_score)
    return normalized


def extract_urls_with_report(sources):
    """从来源列表中提取规范化后的 URL 列表并返回无效数量。"""
    normalized, invalid_count = normalize_sources_with_report(sources)
    return [source["url"] for source in normalized], invalid_count


def extract_urls(sources):
    """从来源列表中提取规范化后的 URL 列表。"""
    urls, _ = extract_urls_with_report(sources)
    return urls
