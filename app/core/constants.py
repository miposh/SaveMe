COMMANDS = {
    "cookie": "/cookie",
    "check_cookie": "/check_cookie",
    "save_as_cookie": "/save_as_cookie",
    "subs": "/subs",
    "audio": "/audio",
    "uncache": "/uncache",
    "playlist": "/playlist",
    "format": "/format",
    "mediainfo": "/mediainfo",
    "settings": "/settings",
    "cookies_from_browser": "/cookies_from_browser",
    "block_user": "/block_user",
    "unblock_user": "/unblock_user",
    "run_time": "/run_time",
    "log": "/log",
    "clean": "/clean",
    "usage": "/usage",
    "tags": "/tags",
    "broadcast": "/broadcast",
    "all": "/all",
    "split": "/split",
    "reload_cache": "/reload_cache",
    "auto_cache": "/auto_cache",
    "search": "/search",
    "keyboard": "/keyboard",
    "link": "/link",
    "proxy": "/proxy",
    "img": "/img",
    "add_bot_to_group": "/add_bot_to_group",
    "nsfw": "/nsfw",
    "args": "/args",
    "list": "/list",
    "ban_time": "/ban_time",
}

BLACK_LIST: list[str] = []

YTDLP_ONLY_DOMAINS = [
    "youtube.com", "youtu.be", "m.youtube.com", "www.youtube.com",
    "music.youtube.com", "gaming.youtube.com",
]

GALLERYDL_ONLY_DOMAINS = [
    "2ch.su", "35photo.pro", "behoimi.org", "4archive.org", "8chan.moe",
    "comics.8muses.com", "agn.ph", "arca.live", "architizer.com", "aryion.com",
    "catbox.moe", "civitai.com", "danke-fuers-lesen.de", "desktopography.net",
    "e-hentai.org", "exhentai.org", "everia.club", "fapello.com", "furry34.com",
    "gelbooru.com", "girlswithmuscle.com", "itaku.ee", "kemono.cr", "kemono.party",
    "coomer.party", "leakgallery.com", "myportfolio.com", "nekohouse.su",
    "nhentai.net", "photovogue.com", "pixeltabel.com", "weasyl.com", "wikifeet.com",
    "xasiat.com", "wallhaven.cc",
]

GALLERYDL_ONLY_PATH = [
    "vk.com/wall-",
    "vk.com/album-",
]

GALLERYDL_FALLBACK_DOMAINS = [
    "instagram.com",
]

WHITELIST = [
    "www.linkedin.com", "linkedin.com", "boozallen.com", "www.boozallen.com",
    "m.ok.ru", "ok.ru", "shazam.com", "rutube.ru", "soundcloud.com",
    "bilibili.com", "dailymotion.com", "sky.com", "xbox.com",
    "youtube.com", "youtu.be", "1tv.ru", "x.ai",
    "twitch.tv", "vimeo.com", "facebook.com", "tiktok.com", "instagram.com",
    "fb.com", "ig.me", "b-cdn.net",
]

GREYLIST = [
    "snapchat.com",
    "reddit.com",
    "vkvideo.ru", "vkontakte.ru", "vk.com",
    "twitter.com", "x.com", "t.co",
]

NO_COOKIE_DOMAINS = [
    "dailymotion.com",
]

PROXY_DOMAINS: list[str] = []
PROXY_2_DOMAINS: list[str] = []

NO_FILTER_DOMAINS = [
    "bashlinker.alenwalak.workers.dev",
    "cdn.indexer.eu.org",
    "a-tushar-82q-fef07c6bf20a.herokuapp.com",
    "file-to-link-632f24ac9728.herokuapp.com",
]

TIKTOK_DOMAINS = [
    "tiktok.com", "vm.tiktok.com", "vt.tiktok.com",
    "www.tiktok.com", "m.tiktok.com", "tiktokv.com",
    "www.tiktokv.com", "tiktok.ru", "www.tiktok.ru",
]

CLEAN_QUERY = [
    "tiktok.com", "vimeo.com", "twitch.tv",
    "instagram.com", "ig.me", "dailymotion.com",
    "twitter.com", "x.com",
    "ok.ru", "mail.ru", "my.mail.ru",
    "rutube.ru", "youku.com", "bilibili.com",
    "tv.kakao.com", "tudou.com", "coub.com",
    "fb.watch", "9gag.com", "streamable.com",
    "veoh.com", "archive.org", "ted.com",
    "mediasetplay.mediaset.it", "ndr.de", "zdf.de", "arte.tv",
    "video.yandex.ru", "video.sibnet.ru", "pladform.ru", "pikabu.ru",
    "bitchute.com", "rumble.com", "peertube.tv",
    "aparat.com", "nicovideo.jp",
    "disk.yandex.net", "streaming.disk.yandex.net",
]

PIPED_DOMAIN = "poketube.fun"

WHITE_KEYWORDS = [
    "a55",
    "Hassas",
    "assasinate", "assasinated", "assassinate", "assassinated", "assassination",
]

PORN_DOMAINS_FILE = "TXT/porn_domains.txt"
PORN_KEYWORDS_FILE = "TXT/porn_keywords.txt"
SUPPORTED_SITES_FILE = "TXT/supported_sites.txt"
COOKIE_FILE_PATH = "TXT/cookie.txt"
