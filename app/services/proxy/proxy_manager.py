import logging
import random

from app.core.config import AppConfig
from app.core.constants import PROXY_DOMAINS, PROXY_2_DOMAINS
from app.services.url_parser.extractor import extract_domain

logger = logging.getLogger(__name__)


class ProxyManager:

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._round_robin_index: int = 0

    @property
    def proxy_1_url(self) -> str:
        return self._config.proxy.proxy_1_url

    @property
    def proxy_2_url(self) -> str:
        return self._config.proxy.proxy_2_url

    def get_all_proxy_urls(self) -> list[str]:
        urls: list[str] = []
        if self.proxy_1_url:
            urls.append(self.proxy_1_url)
        if self.proxy_2_url:
            urls.append(self.proxy_2_url)
        return urls

    def select_for_user(self) -> str | None:
        urls = self.get_all_proxy_urls()
        if not urls:
            return None
        if len(urls) == 1:
            return urls[0]

        if self._config.proxy.proxy_select == "random":
            return random.choice(urls)

        selected = urls[self._round_robin_index % len(urls)]
        self._round_robin_index += 1
        return selected

    def select_for_domain(self, url: str) -> str | None:
        domain = extract_domain(url)
        logger.info("select_for_domain: url=%s, domain=%s", url, domain)

        if any(d in domain for d in PROXY_2_DOMAINS):
            if self.proxy_2_url:
                logger.info("Domain %s matched PROXY_2_DOMAINS", domain)
                return self.proxy_2_url

        if any(d in domain for d in PROXY_DOMAINS):
            if self.proxy_1_url:
                logger.info("Domain %s matched PROXY_DOMAINS", domain)
                return self.proxy_1_url

        return None

    def add_proxy_to_ytdl_opts(
        self,
        ytdl_opts: dict,
        url: str,
        user_proxy_enabled: bool = False,
    ) -> dict:
        if user_proxy_enabled:
            proxy_url = self.select_for_user()
            if proxy_url:
                result = {**ytdl_opts, "proxy": proxy_url}
                logger.info("Added user proxy: %s", proxy_url)
                return result

        domain_proxy = self.select_for_domain(url)
        if domain_proxy:
            result = {**ytdl_opts, "proxy": domain_proxy}
            logger.info("Added domain proxy for %s: %s", url, domain_proxy)
            return result

        return ytdl_opts

    def add_proxy_to_gallery_dl_config(
        self,
        config: dict,
        url: str,
        user_proxy_enabled: bool = False,
    ) -> dict:
        if user_proxy_enabled:
            proxy_url = self.select_for_user()
            if proxy_url:
                result = {
                    **config,
                    "extractor": {
                        **config.get("extractor", {}),
                        "proxy": proxy_url,
                    },
                }
                logger.info("Added user proxy to gallery-dl: %s", proxy_url)
                return result

        domain_proxy = self.select_for_domain(url)
        if domain_proxy:
            result = {
                **config,
                "extractor": {
                    **config.get("extractor", {}),
                    "proxy": domain_proxy,
                },
            }
            logger.info("Added domain proxy to gallery-dl: %s", domain_proxy)
            return result

        return config

    def try_with_proxy_fallback(
        self,
        ytdl_opts: dict,
        url: str,
        operation_func,
        *args,
        **kwargs,
    ):
        all_proxies = self.get_all_proxy_urls()
        if not all_proxies:
            return operation_func(ytdl_opts, *args, **kwargs)

        for i, proxy_url in enumerate(all_proxies):
            try:
                current_opts = {**ytdl_opts, "proxy": proxy_url}
                logger.info(
                    "Trying %s with proxy %d/%d: %s",
                    url, i + 1, len(all_proxies), proxy_url,
                )
                result = operation_func(current_opts, *args, **kwargs)
                if result is not None:
                    return result
            except Exception as e:
                logger.warning(
                    "Failed with proxy %d/%d: %s", i + 1, len(all_proxies), e,
                )

        try:
            logger.info("All proxies failed, trying without proxy")
            opts_no_proxy = {k: v for k, v in ytdl_opts.items() if k != "proxy"}
            return operation_func(opts_no_proxy, *args, **kwargs)
        except Exception as e:
            logger.error("Failed without proxy: %s", e)
            return None

    def is_proxy_domain(self, url: str) -> bool:
        domain = extract_domain(url)
        if any(d in domain for d in PROXY_DOMAINS):
            return True
        if any(d in domain for d in PROXY_2_DOMAINS):
            return True
        return False
