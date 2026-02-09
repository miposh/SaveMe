from app.core.constants import (
    GALLERYDL_FALLBACK_DOMAINS,
    GALLERYDL_ONLY_DOMAINS,
    GALLERYDL_ONLY_PATH,
    YTDLP_ONLY_DOMAINS,
)
from app.services.url_parser.extractor import extract_domain


def get_download_engine(url: str) -> str:
    domain = extract_domain(url)

    if any(d in domain for d in YTDLP_ONLY_DOMAINS):
        return "ytdlp"

    if any(d in domain for d in GALLERYDL_ONLY_DOMAINS):
        return "gallery_dl"

    if any(path in url for path in GALLERYDL_ONLY_PATH):
        return "gallery_dl"

    if any(d in domain for d in GALLERYDL_FALLBACK_DOMAINS):
        return "ytdlp_with_gallery_dl_fallback"

    return "ytdlp"
