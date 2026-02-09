import hashlib
import logging
import os
import random
import time

import aiohttp

from app.core.config import AppConfig

logger = logging.getLogger(__name__)


class CookieManager:

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._youtube_cookie_cache: dict[int, dict] = {}
        self._non_youtube_cookie_cache: dict[str, dict] = {}
        self._round_robin_index: int = 0
        self._retry_tracking: dict[int, dict] = {}
        self._cookie_dir = os.path.join(config.save_dir, "cookies")

    async def ensure_cookie_dir(self) -> None:
        os.makedirs(self._cookie_dir, exist_ok=True)

    def _get_cookie_path(self, user_id: int, service: str = "default") -> str:
        return os.path.join(self._cookie_dir, f"{user_id}_{service}.txt")

    async def download_cookie(self, url: str, dest_path: str) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status != 200:
                        logger.error(
                            "Failed to download cookie from %s: status %d",
                            url, resp.status,
                        )
                        return False
                    content = await resp.text()
                    if not content.strip():
                        logger.error("Empty cookie file from %s", url)
                        return False

                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    with open(dest_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    logger.info("Downloaded cookie to %s", dest_path)
                    return True
        except Exception as e:
            logger.error("Error downloading cookie from %s: %s", url, e)
            return False

    def get_youtube_cookie_path(self, user_id: int) -> str | None:
        urls = self._config.cookies.youtube_cookie_urls
        if not urls:
            return None

        if self._config.cookies.youtube_cookie_order == "random":
            idx = random.randint(0, len(urls) - 1)
        else:
            idx = self._round_robin_index % len(urls)
            self._round_robin_index += 1

        cookie_path = self._get_cookie_path(user_id, f"youtube_{idx}")
        if os.path.exists(cookie_path):
            age = time.time() - os.path.getmtime(cookie_path)
            if age < self._config.limits.cookie_cache_duration * 60:
                return cookie_path

        return cookie_path

    def get_youtube_cookie_url(self) -> str | None:
        urls = self._config.cookies.youtube_cookie_urls
        if not urls:
            return None

        if self._config.cookies.youtube_cookie_order == "random":
            return random.choice(urls)

        url = urls[self._round_robin_index % len(urls)]
        self._round_robin_index += 1
        return url

    async def get_or_download_youtube_cookie(self, user_id: int) -> str | None:
        await self.ensure_cookie_dir()

        cookie_path = self.get_youtube_cookie_path(user_id)
        if not cookie_path:
            return None

        if os.path.exists(cookie_path):
            age = time.time() - os.path.getmtime(cookie_path)
            if age < self._config.limits.cookie_cache_duration * 60:
                return cookie_path

        url = self.get_youtube_cookie_url()
        if not url:
            return None

        success = await self.download_cookie(url, cookie_path)
        return cookie_path if success else None

    def get_service_cookie_url(self, domain: str) -> str | None:
        cookies = self._config.cookies
        domain_lower = domain.lower()

        if "instagram" in domain_lower:
            return cookies.instagram_cookie_url or None
        if "tiktok" in domain_lower:
            return cookies.tiktok_cookie_url or None
        if "facebook" in domain_lower or "fb.com" in domain_lower:
            return cookies.facebook_cookie_url or None
        if "twitter" in domain_lower or "x.com" in domain_lower:
            return cookies.twitter_cookie_url or None
        if "vk.com" in domain_lower or "vkvideo" in domain_lower:
            return cookies.vk_cookie_url or None

        return None

    async def get_or_download_service_cookie(
        self, user_id: int, domain: str,
    ) -> str | None:
        await self.ensure_cookie_dir()

        url = self.get_service_cookie_url(domain)
        if not url:
            return None

        service = domain.replace(".", "_")
        cookie_path = self._get_cookie_path(user_id, service)

        if os.path.exists(cookie_path):
            age = time.time() - os.path.getmtime(cookie_path)
            if age < self._config.limits.cookie_cache_duration * 60:
                return cookie_path

        success = await self.download_cookie(url, cookie_path)
        return cookie_path if success else None

    def get_cache_key(self, user_id: int, url: str, service: str | None = None) -> str:
        data = f"{user_id}_{url}_{service or ''}"
        return hashlib.md5(data.encode()).hexdigest()[:16]

    def is_retry_limit_reached(self, user_id: int) -> bool:
        tracking = self._retry_tracking.get(user_id)
        if not tracking:
            return False

        now = time.time()
        window = self._config.limits.youtube_cookie_retry_window
        limit = self._config.limits.youtube_cookie_retry_limit_per_hour

        if now - tracking.get("last_reset", 0) > window:
            self._retry_tracking[user_id] = {"attempts": [], "last_reset": now}
            return False

        recent = [t for t in tracking.get("attempts", []) if now - t < window]
        self._retry_tracking[user_id]["attempts"] = recent
        return len(recent) >= limit

    def record_retry(self, user_id: int) -> None:
        now = time.time()
        if user_id not in self._retry_tracking:
            self._retry_tracking[user_id] = {"attempts": [], "last_reset": now}
        self._retry_tracking[user_id]["attempts"].append(now)

    def cleanup_old_cookies(self, max_age_hours: int = 24) -> int:
        removed = 0
        if not os.path.exists(self._cookie_dir):
            return removed

        now = time.time()
        for filename in os.listdir(self._cookie_dir):
            filepath = os.path.join(self._cookie_dir, filename)
            if os.path.isfile(filepath):
                age = now - os.path.getmtime(filepath)
                if age > max_age_hours * 3600:
                    try:
                        os.remove(filepath)
                        removed += 1
                    except Exception as e:
                        logger.error("Failed to remove old cookie %s: %s", filepath, e)
        return removed
