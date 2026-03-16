import os

import yt_dlp


__all__ = ["search_youtube"]


def _read_int_env(name, default, minimum, maximum):

    raw = os.getenv(name)
    if raw is None:
        value = default
    else:
        try:
            value = int(raw)
        except ValueError:
            value = default

    if value < minimum:
        return minimum
    if value > maximum:
        return maximum
    return value


def search_youtube(query, max_results=None, timeout_seconds=None, retries=None):

    resolved_max_results = max_results if max_results is not None else _read_int_env("YOUTUBE_MAX_RESULTS", 5, 1, 50)
    resolved_timeout = timeout_seconds if timeout_seconds is not None else _read_int_env("YOUTUBE_TIMEOUT_SECONDS", 20, 1, 120)
    resolved_retries = retries if retries is not None else _read_int_env("YOUTUBE_RETRIES", 3, 0, 10)

    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "socket_timeout": resolved_timeout,
        "retries": resolved_retries,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        results = ydl.extract_info(f"ytsearch{resolved_max_results}:{query}", download=False)

    videos = []
    for entry in results.get("entries", []):
        videos.append({
            "title": entry.get("title", ""),
            "url": entry.get("url", ""),
        })

    return videos