import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


def _parse_int_list(value: str) -> list[int]:
    if not value:
        return []
    return [int(x.strip()) for x in value.split(",") if x.strip()]


def _parse_youtube_cookie_urls() -> list[str]:
    urls: list[str] = []
    main_url = os.getenv("YOUTUBE_COOKIE_URL", "")
    if main_url:
        urls.append(main_url)
    for i in range(1, 11):
        url = os.getenv(f"YOUTUBE_COOKIE_URL_{i}", "")
        if url:
            urls.append(url)
    return urls


class LocalApiConfig(BaseSettings):
    enabled: bool = Field(default=False, alias="LOCAL_API_ENABLED")
    base_url: str = Field(
        default="http://telegram-bot-api:8081", alias="LOCAL_API_BASE_URL"
    )
    files_url: str = Field(
        default="http://telegram-bot-api:8081", alias="LOCAL_API_FILES_URL"
    )

    model_config = {"env_file": ".env", "extra": "ignore"}


class BotConfig(BaseSettings):
    token: str = Field(alias="BOT_TOKEN")
    name: str = Field(default="saveme_bot", alias="BOT_NAME")
    name_for_users: str = Field(default="saveme_bot", alias="BOT_NAME_FOR_USERS")
    miniapp_url: str = Field(default="", alias="MINIAPP_URL")
    api_id: int = Field(default=0, alias="API_ID")
    api_hash: str = Field(default="", alias="API_HASH")
    channel_guard_session_string: str = Field(
        default="", alias="CHANNEL_GUARD_SESSION_STRING"
    )
    local_api: LocalApiConfig = Field(default_factory=LocalApiConfig)

    model_config = {"env_file": ".env", "extra": "ignore"}


class AdminConfig(BaseSettings):
    raw_admin_ids: str = Field(default="", alias="ADMIN_IDS")
    raw_allowed_group_ids: str = Field(default="", alias="ALLOWED_GROUP_IDS")
    star_receiver: int = Field(default=7360853)

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def admin_ids(self) -> list[int]:
        return _parse_int_list(self.raw_admin_ids)

    @property
    def allowed_group_ids(self) -> list[int]:
        return _parse_int_list(self.raw_allowed_group_ids)


class ChannelConfig(BaseSettings):
    subscribe_channel_id: int = Field(default=0, alias="SUBSCRIBE_CHANNEL_ID")
    subscribe_channel_url: str = Field(default="", alias="SUBSCRIBE_CHANNEL_URL")
    required_channel_mention: str = Field(
        default="", alias="REQUIRED_CHANNEL_MENTION"
    )
    logs_channel_id: int = Field(default=0, alias="LOGS_CHANNEL_ID")
    logs_video_channel_id: int = Field(default=0, alias="LOGS_VIDEO_CHANNEL_ID")
    logs_nsfw_channel_id: int = Field(default=0, alias="LOGS_NSFW_CHANNEL_ID")
    logs_img_channel_id: int = Field(default=0, alias="LOGS_IMG_CHANNEL_ID")
    logs_paid_channel_id: int = Field(default=0, alias="LOGS_PAID_CHANNEL_ID")
    logs_exception_channel_id: int = Field(
        default=0, alias="LOGS_EXCEPTION_CHANNEL_ID"
    )

    model_config = {"env_file": ".env", "extra": "ignore"}


class BrandingConfig(BaseSettings):
    credits_managed_by: str = Field(default="", alias="CREDITS_MANAGED_BY")
    credits_bots: str = Field(default="", alias="CREDITS_BOTS")

    model_config = {"env_file": ".env", "extra": "ignore"}


class PostgresConfig(BaseSettings):
    host: str = Field(default="localhost", alias="POSTGRES_HOST")
    port: int = Field(default=5432, alias="POSTGRES_PORT")
    db: str = Field(default="saveme", alias="POSTGRES_DB")
    user: str = Field(default="saveme", alias="POSTGRES_USER")
    password: str = Field(default="", alias="POSTGRES_PASSWORD")

    model_config = {"env_file": ".env", "extra": "ignore"}


class CookieConfig(BaseSettings):
    cookie_url: str = Field(default="", alias="COOKIE_URL")
    youtube_cookie_order: str = Field(
        default="round_robin", alias="YOUTUBE_COOKIE_ORDER"
    )
    youtube_cookie_test_url: str = Field(
        default="https://www.youtube.com/watch?v=_GuOjXYl5ew",
        alias="YOUTUBE_COOKIE_TEST_URL",
    )
    instagram_cookie_url: str = Field(default="", alias="INSTAGRAM_COOKIE_URL")
    tiktok_cookie_url: str = Field(default="", alias="TIKTOK_COOKIE_URL")
    facebook_cookie_url: str = Field(default="", alias="FACEBOOK_COOKIE_URL")
    twitter_cookie_url: str = Field(default="", alias="TWITTER_COOKIE_URL")
    vk_cookie_url: str = Field(default="", alias="VK_COOKIE_URL")

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def youtube_cookie_urls(self) -> list[str]:
        return _parse_youtube_cookie_urls()


class ProxyConfig(BaseSettings):
    proxy_type: str = Field(default="http", alias="PROXY_TYPE")
    proxy_ip: str = Field(default="", alias="PROXY_IP")
    proxy_port: int = Field(default=3128, alias="PROXY_PORT")
    proxy_user: str = Field(default="", alias="PROXY_USER")
    proxy_password: str = Field(default="", alias="PROXY_PASSWORD")
    proxy_2_type: str = Field(default="socks5", alias="PROXY_2_TYPE")
    proxy_2_ip: str = Field(default="", alias="PROXY_2_IP")
    proxy_2_port: int = Field(default=3128, alias="PROXY_2_PORT")
    proxy_2_user: str = Field(default="", alias="PROXY_2_USER")
    proxy_2_password: str = Field(default="", alias="PROXY_2_PASSWORD")
    proxy_select: str = Field(default="round_robin", alias="PROXY_SELECT")

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def proxy_1_url(self) -> str:
        if not self.proxy_ip:
            return ""
        auth = ""
        if self.proxy_user:
            auth = f"{self.proxy_user}:{self.proxy_password}@"
        return f"{self.proxy_type}://{auth}{self.proxy_ip}:{self.proxy_port}"

    @property
    def proxy_2_url(self) -> str:
        if not self.proxy_2_ip:
            return ""
        auth = ""
        if self.proxy_2_user:
            auth = f"{self.proxy_2_user}:{self.proxy_2_password}@"
        return f"{self.proxy_2_type}://{auth}{self.proxy_2_ip}:{self.proxy_2_port}"


class PotConfig(BaseSettings):
    enabled: bool = Field(default=True, alias="YOUTUBE_POT_ENABLED")
    base_url: str = Field(
        default="http://bgutil-provider:4416", alias="YOUTUBE_POT_BASE_URL"
    )
    disable_innertube: bool = Field(
        default=False, alias="YOUTUBE_POT_DISABLE_INNERTUBE"
    )

    model_config = {"env_file": ".env", "extra": "ignore"}


class DashboardConfig(BaseSettings):
    port: int = Field(default=5555, alias="DASHBOARD_PORT")
    username: str = Field(default="admin", alias="DASHBOARD_USERNAME")
    password: str = Field(default="", alias="DASHBOARD_PASSWORD")

    model_config = {"env_file": ".env", "extra": "ignore"}


class LimitsConfig(BaseSettings):
    max_file_size_gb: int = Field(default=8)
    download_timeout: int = Field(default=7200)
    max_video_duration: int = Field(default=43200)
    max_sub_duration: int = Field(default=5400)
    max_sub_size: int = Field(default=10)
    max_sub_quality: str = Field(default="1080")
    max_playlist_count: int = Field(default=50)
    max_tiktok_count: int = Field(default=500)
    max_img_files: int = Field(default=1000)
    max_img_range_wait_time: int = Field(default=1800)
    max_img_total_wait_time: int = Field(default=14400)
    max_img_inactivity_time: int = Field(default=300)
    max_animation_duration: int = Field(default=14400)
    max_http_connection_lifetime: int = Field(default=14400)
    http_request_timeout: int = Field(default=60)
    rate_limit_per_minute: int = Field(default=5)
    rate_limit_per_hour: int = Field(default=60)
    rate_limit_per_day: int = Field(default=1000)
    rate_limit_cooldown_minute: int = Field(default=300)
    rate_limit_cooldown_hour: int = Field(default=3600)
    rate_limit_cooldown_day: int = Field(default=86400)
    command_limit_per_minute: int = Field(default=20)
    command_cooldown_initial: int = Field(default=60)
    command_cooldown_multiplier: int = Field(default=2)
    group_multiplier: int = Field(default=2)
    nsfw_star_cost: int = Field(default=1)
    cookie_cache_duration: int = Field(default=30)
    cookie_cache_max_lifetime: int = Field(default=7200)
    youtube_cookie_retry_limit_per_hour: int = Field(default=8)
    youtube_cookie_retry_window: int = Field(default=3600)

    model_config = {"extra": "ignore"}


class AppConfig(BaseSettings):
    bot: BotConfig = Field(default_factory=BotConfig)
    admin: AdminConfig = Field(default_factory=AdminConfig)
    channels: ChannelConfig = Field(default_factory=ChannelConfig)
    branding: BrandingConfig = Field(default_factory=BrandingConfig)
    postgres: PostgresConfig = Field(default_factory=PostgresConfig)
    cookies: CookieConfig = Field(default_factory=CookieConfig)
    proxy: ProxyConfig = Field(default_factory=ProxyConfig)
    pot: PotConfig = Field(default_factory=PotConfig)
    dashboard: DashboardConfig = Field(default_factory=DashboardConfig)
    limits: LimitsConfig = Field(default_factory=LimitsConfig)
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    work_in_progress: bool = Field(default=False, alias="WORK_IN_PROGRESS")
    save_dir: str = Field(default="downloads")
    cookie_file_path: str = Field(default="TXT/cookie.txt")

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    return AppConfig()
