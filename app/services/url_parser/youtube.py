import re
from urllib.parse import urlparse, parse_qs

YOUTUBE_DOMAINS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "music.youtube.com"}

VIDEO_ID_REGEX = re.compile(r"(?:v=|youtu\.be/|/embed/|/v/|/shorts/)([a-zA-Z0-9_-]{11})")


def is_youtube_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower().replace("www.", "") in YOUTUBE_DOMAINS or "youtu.be" in parsed.netloc.lower()
    except Exception:
        return False


def extract_video_id(url: str) -> str | None:
    match = VIDEO_ID_REGEX.search(url)
    if match:
        return match.group(1)

    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    if "v" in params:
        return params["v"][0]

    if "youtu.be" in parsed.netloc:
        path = parsed.path.strip("/")
        if len(path) == 11:
            return path

    return None


def is_playlist_url(url: str) -> bool:
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    return "list" in params


def is_shorts_url(url: str) -> bool:
    return "/shorts/" in url
