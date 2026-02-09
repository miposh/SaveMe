import logging
import re
from urllib.parse import urlparse, parse_qs, unquote

import tldextract

from app.core.constants import WHITELIST, GREYLIST, PORN_DOMAINS_FILE, PORN_KEYWORDS_FILE

logger = logging.getLogger(__name__)

_porn_domains: set[str] = set()
_porn_keywords: set[str] = set()


def load_domain_lists() -> None:
    global _porn_domains, _porn_keywords

    try:
        with open(PORN_DOMAINS_FILE, "r", encoding="utf-8", errors="ignore") as f:
            _porn_domains = {line.strip().lower() for line in f if line.strip()}
        logger.info("Loaded %d porn domains", len(_porn_domains))
    except Exception as e:
        logger.error("Failed to load %s: %s", PORN_DOMAINS_FILE, e)
        _porn_domains = set()

    try:
        with open(PORN_KEYWORDS_FILE, "r", encoding="utf-8", errors="ignore") as f:
            _porn_keywords = {line.strip().lower() for line in f if line.strip()}
        logger.info("Loaded %d porn keywords", len(_porn_keywords))
    except Exception as e:
        logger.error("Failed to load %s: %s", PORN_KEYWORDS_FILE, e)
        _porn_keywords = set()


def _unwrap_redirect_url(url: str) -> str:
    try:
        current = url
        for _ in range(2):
            parsed = urlparse(current)
            qs = parse_qs(parsed.query or "")
            candidate = None
            for key in [
                "url", "u", "q", "redirect", "redir",
                "target", "to", "dest", "destination", "r", "s",
            ]:
                values = qs.get(key)
                if not values:
                    continue
                for v in values:
                    v = unquote(v)
                    m = re.search(r"https?://[^\s]+", v)
                    if m:
                        candidate = m.group(0)
                        break
                if candidate:
                    break
            if candidate:
                current = candidate
            else:
                break
        return current
    except Exception:
        return url


def _extract_domain_parts(url: str) -> tuple[list[str], str]:
    try:
        unwrapped = _unwrap_redirect_url(url)
        ext = tldextract.extract(unwrapped)
        if ext.domain and ext.suffix:
            full_domain = f"{ext.domain}.{ext.suffix}".lower()
            subdomain = ext.subdomain.lower() if ext.subdomain else ""
            parts = [full_domain]
            if subdomain:
                sub_parts = subdomain.split(".")
                for i in range(len(sub_parts)):
                    parts.append(".".join(sub_parts[i:] + [full_domain]))
            return parts, ext.domain.lower()
        if ext.domain:
            return [ext.domain.lower()], ext.domain.lower()
        return [url.lower()], url.lower()
    except Exception:
        parsed = urlparse(url)
        if parsed.netloc:
            return [parsed.netloc.lower()], parsed.netloc.lower()
        return [url.lower()], url.lower()


def _is_porn_domain(domain_parts: list[str]) -> bool:
    whitelist_lower = {d.lower() for d in WHITELIST}
    greylist_lower = {d.lower() for d in GREYLIST}

    for dom in domain_parts:
        if dom in whitelist_lower:
            return False

    for dom in domain_parts:
        if dom in greylist_lower:
            return False

    for dom in domain_parts:
        if dom in _porn_domains:
            return True

    return False


def _compile_url_keyword_regex(raw_keyword: str) -> re.Pattern:
    words = [re.escape(w) for w in raw_keyword.split() if w]
    if not words:
        return re.compile(r"a^")
    joiner = r"[^A-Za-z0-9]+"
    core = joiner.join(words)
    return re.compile(
        rf"(?<![A-Za-z0-9])(?:{core})(?![A-Za-z0-9])",
        flags=re.IGNORECASE,
    )


def is_porn(
    url: str,
    title: str = "",
    description: str = "",
    caption: str | None = None,
    tags: str | None = None,
    white_keywords: list[str] | None = None,
) -> bool:
    clean_url = _unwrap_redirect_url(url).lower()
    domain_parts, _ = _extract_domain_parts(clean_url)

    whitelist_lower = {d.lower() for d in WHITELIST}
    for dom in domain_parts:
        if dom in whitelist_lower:
            return False

    if _is_porn_domain(domain_parts):
        logger.info("is_porn: domain match: %s", domain_parts)
        return True

    title_lower = title.lower() if title else ""
    description_lower = description.lower() if description else ""
    caption_lower = caption.lower() if caption else ""
    tags_lower = tags.lower().replace("_", " ") if tags else ""
    url_lower = clean_url

    if not (title_lower or description_lower or caption_lower or tags_lower or url_lower):
        return False

    combined = " ".join([title_lower, description_lower, caption_lower, tags_lower, url_lower])

    if white_keywords:
        white_kws = [re.escape(kw.lower()) for kw in white_keywords if kw.strip()]
        if white_kws:
            white_pattern = re.compile(
                r"\b(" + "|".join(white_kws) + r")\b",
                flags=re.IGNORECASE,
            )
            if white_pattern.search(combined):
                return False

    text_kws = [re.escape(kw.lower()) for kw in _porn_keywords if kw.strip()]
    url_kws = [kw.lower() for kw in _porn_keywords if kw.strip()]

    if not text_kws:
        return False

    text_pattern = re.compile(
        r"\b(" + "|".join(text_kws) + r")\b",
        flags=re.IGNORECASE,
    )
    text_to_check = " ".join([title_lower, description_lower, caption_lower, tags_lower])
    if text_pattern.search(text_to_check):
        logger.info("is_porn: keyword match in text fields")
        return True

    for raw_kw in url_kws:
        url_pattern = _compile_url_keyword_regex(raw_kw)
        if url_pattern.search(url_lower):
            logger.info("is_porn: keyword match in URL: %s", raw_kw)
            return True

    return False


def check_porn_detailed(
    url: str,
    title: str = "",
    description: str = "",
    caption: str | None = None,
    white_keywords: list[str] | None = None,
) -> tuple[bool, str]:
    clean_url = _unwrap_redirect_url(url).lower()
    domain_parts, _ = _extract_domain_parts(clean_url)

    whitelist_lower = {d.lower() for d in WHITELIST}
    for dom in domain_parts:
        if dom in whitelist_lower:
            return False, f"Domain in whitelist: {dom}"

    if _is_porn_domain(domain_parts):
        return True, f"Domain in porn list: {domain_parts}"

    title_lower = title.lower() if title else ""
    description_lower = description.lower() if description else ""
    caption_lower = caption.lower() if caption else ""

    if not (title_lower or description_lower or caption_lower):
        return False, "All text fields empty"

    combined = " ".join([title_lower, description_lower, caption_lower])

    if white_keywords:
        white_kws = [re.escape(kw.lower()) for kw in white_keywords if kw.strip()]
        if white_kws:
            white_pattern = re.compile(
                r"\b(" + "|".join(white_kws) + r")\b",
                flags=re.IGNORECASE,
            )
            matches = white_pattern.findall(combined)
            if matches:
                return False, f"White keywords found: {', '.join(set(matches))}"

    text_kws = [re.escape(kw.lower()) for kw in _porn_keywords if kw.strip()]
    if not text_kws:
        return False, "No porn keywords loaded"

    text_pattern = re.compile(
        r"\b(" + "|".join(text_kws) + r")\b",
        flags=re.IGNORECASE,
    )
    matches = text_pattern.findall(combined)
    if matches:
        return True, f"Keywords found: {', '.join(set(matches))}"

    url_lower = clean_url
    url_matches: list[str] = []
    for raw_kw in [kw.lower() for kw in _porn_keywords if kw.strip()]:
        url_pattern = _compile_url_keyword_regex(raw_kw)
        found = url_pattern.findall(url_lower)
        if found:
            url_matches.extend(found)

    if url_matches:
        return True, f"NSFW keywords in URL: {', '.join(set(url_matches))}"

    return False, "No keywords found"


def reload_caches() -> dict[str, int]:
    load_domain_lists()
    return {
        "porn_domains": len(_porn_domains),
        "porn_keywords": len(_porn_keywords),
    }
