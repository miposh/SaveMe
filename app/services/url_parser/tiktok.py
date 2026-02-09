from app.core.constants import TIKTOK_DOMAINS
from app.services.url_parser.extractor import extract_domain


def is_tiktok_url(url: str) -> bool:
    domain = extract_domain(url)
    return any(d in domain for d in TIKTOK_DOMAINS)
