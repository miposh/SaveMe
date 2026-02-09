import re
import logging
from urllib.parse import urlparse

import tldextract

logger = logging.getLogger(__name__)

URL_REGEX = re.compile(r"https?://\S+")


def extract_urls(text: str) -> list[str]:
    return URL_REGEX.findall(text)


def extract_domain(url: str) -> str:
    try:
        extracted = tldextract.extract(url)
        domain = f"{extracted.domain}.{extracted.suffix}"
        return domain.lower()
    except Exception:
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return ""


def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


async def extract_info(url: str) -> dict | None:
    import asyncio

    def _sync_extract(target_url: str) -> dict | None:
        from yt_dlp import YoutubeDL

        opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": False,
        }
        try:
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(target_url, download=False)
                return info
        except Exception as e:
            logger.error("extract_info failed for %s: %s", target_url, e)
            return None

    return await asyncio.to_thread(_sync_extract, url)
