from agents.source_contract import extract_urls, normalize_source, normalize_sources


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