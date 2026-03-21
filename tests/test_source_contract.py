from agents.source_contract import (
    extract_urls,
    extract_urls_with_report,
    normalize_source,
    normalize_sources,
    normalize_sources_with_report,
    validate_source_schema,
)


def test_normalize_source_returns_none_for_invalid_input():
    assert normalize_source("x", platform="youtube") is None
    assert normalize_source({"url": "   "}, platform="youtube") is None


def test_normalize_sources_and_extract_urls():
    items = [
        {"title": " A ", "url": " https://a.com ", "score": "0.8"},
        {"title": "B", "url": "https://b.com", "platform": "youtube", "score": 1},
        {"title": "bad", "url": ""},
        123,
    ]

    sources = normalize_sources(items, platform="youtube")
    assert sources == [
        {"title": "A", "url": "https://a.com", "platform": "youtube", "score": 0.8},
        {"title": "B", "url": "https://b.com", "platform": "youtube", "score": 1.0},
    ]
    assert extract_urls(items) == ["https://a.com", "https://b.com"]


def test_validate_source_schema_returns_errors_for_invalid_source():
    errors = validate_source_schema({"title": "A", "url": "", "platform": " ", "score": "x"})
    assert "url must be a non-empty string" in errors
    assert "platform must be a non-empty string" in errors
    assert "score must be a finite number" in errors


def test_normalize_sources_with_report_and_extract_urls_with_report():
    items = [
        {"title": "A", "url": "https://a.com", "score": 1},
        {"title": "bad", "url": ""},
        123,
    ]

    sources, invalid_count = normalize_sources_with_report(items, platform="youtube")
    assert invalid_count == 2
    assert sources == [
        {"title": "A", "url": "https://a.com", "platform": "youtube", "score": 1.0},
    ]

    urls, url_invalid_count = extract_urls_with_report(items)
    assert urls == ["https://a.com"]
    assert url_invalid_count == 2
