import logging
import time

import aiohttp

from app.core.config import AppConfig
from app.services.url_parser.youtube import is_youtube_url

logger = logging.getLogger(__name__)


class PotProvider:

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._cache_available: bool | None = None
        self._cache_last_check: float = 0
        self._check_interval: int = 30

    @property
    def enabled(self) -> bool:
        return self._config.pot.enabled

    @property
    def base_url(self) -> str:
        return self._config.pot.base_url

    @property
    def disable_innertube(self) -> bool:
        return self._config.pot.disable_innertube

    async def check_availability(self) -> bool:
        now = time.time()

        if (
            self._cache_available is not None
            and now - self._cache_last_check < self._check_interval
        ):
            return self._cache_available

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.base_url, timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    is_available = resp.status in (200, 404)

            self._cache_available = is_available
            self._cache_last_check = now

            if is_available:
                logger.info(
                    "PO token provider available at %s", self.base_url,
                )
            else:
                logger.warning(
                    "PO token provider returned unexpected status at %s",
                    self.base_url,
                )

            return is_available
        except Exception as e:
            logger.warning("PO token provider not available: %s", e)
            self._cache_available = False
            self._cache_last_check = now
            return False

    async def add_pot_to_ytdl_opts(self, ytdl_opts: dict, url: str) -> dict:
        if not self.enabled:
            return ytdl_opts

        if not is_youtube_url(url):
            return ytdl_opts

        if not await self.check_availability():
            logger.warning("PO token provider not available, skipping")
            return ytdl_opts

        extractor_args = {**ytdl_opts.get("extractor_args", {})}

        pot_args = dict(extractor_args.get("youtubepot", {}))
        providers = list(pot_args.get("providers", []))
        if "bgutilhttp" not in providers:
            providers.append("bgutilhttp")
        pot_args = {**pot_args, "providers": providers}

        bg_cfg = dict(pot_args.get("bgutilhttp", {}))
        bg_cfg = {**bg_cfg, "base_url": [self.base_url]}
        pot_args = {**pot_args, "bgutilhttp": bg_cfg}

        if self.disable_innertube:
            pot_args = {**pot_args, "disable_innertube": ["1"]}

        extractor_args = {**extractor_args, "youtubepot": pot_args}

        result = {**ytdl_opts, "extractor_args": extractor_args}

        logger.info("PO token enabled for YouTube URL: %s", url)
        logger.info("Providers: %s", providers)

        return result

    def build_cli_extractor_args(self, url: str) -> list[str]:
        if not self.enabled:
            return []
        if not is_youtube_url(url):
            return []

        pot_segment = f"youtubepot-bgutilhttp:base_url={self.base_url}"
        if self.disable_innertube:
            pot_segment += ";disable_innertube=1"

        return ["--extractor-args", pot_segment]

    def clear_cache(self) -> None:
        self._cache_available = None
        self._cache_last_check = 0
        logger.info("PO token provider cache cleared")

    async def is_available(self) -> bool:
        return await self.check_availability()
