import re
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from app.core.constants import CLEAN_QUERY


def normalize_url(url: str) -> str:
    url = url.strip()

    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    should_clean = any(d in domain for d in CLEAN_QUERY)

    if should_clean:
        cleaned = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            "",
            "",
            "",
        ))
        return cleaned

    return url


def get_clean_playlist_url(url: str) -> str:
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    if "list" in params:
        clean_params = {"list": params["list"][0]}
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            "",
            urlencode(clean_params),
            "",
        ))

    return url
