import yt_dlp


__all__ = ["search_youtube"]


def search_youtube(query):

    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        results = ydl.extract_info(f"ytsearch5:{query}", download=False)

    videos = []
    for entry in results.get("entries", []):
        videos.append({
            "title": entry.get("title", ""),
            "url": entry.get("url", ""),
        })

    return videos