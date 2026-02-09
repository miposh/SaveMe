MESSAGES: dict[str, str] = {
    "WELCOME": "Welcome, {name}!\n\nSend me a URL to download video, audio, or images from 1500+ platforms.\n\nUse /help for more info.",
    "HELP": (
        "<b>Available commands:</b>\n\n"
        "/vid <code>URL</code> - Download video\n"
        "/audio <code>URL</code> - Download audio\n"
        "/img <code>URL</code> - Download images\n"
        "/playlist <code>URL</code> - Download playlist\n"
        "/link <code>URL</code> - Get direct link\n"
        "/format - Set preferred format\n"
        "/subs - Subtitle settings\n"
        "/split - Split settings\n"
        "/settings - All settings\n"
        "/search <code>query</code> - Search\n"
        "/clean - Clean temp files"
    ),
    "URL_RECEIVED": "URL received. Download will start shortly...",
    "DOWNLOADING": "Downloading...",
    "UPLOADING": "Uploading...",
    "DOWNLOAD_COMPLETE": "Download complete!",
    "DOWNLOAD_FAILED": "Download failed: {error}",
    "RATE_LIMITED": "Too many requests. Please wait {seconds} seconds.",
    "SUBSCRIBE_FIRST": "Please subscribe to our channel first: {url}",
    "BANNED": "You are blocked from using this bot.",
    "INVALID_URL": "Invalid URL. Please send a valid URL.",
    "NO_MEDIA_FOUND": "No media found at this URL.",
    "FILE_TOO_LARGE": "File is too large ({size} GB). Maximum: {max} GB.",
    "DURATION_TOO_LONG": "Video is too long ({duration}). Maximum: {max}.",
    "NSFW_BLOCKED": "NSFW content blocked. Enable with /nsfw.",
    "FORMAT_SELECTED": "Format set to: {format}",
    "SPLIT_SET": "Split set to: {size} MB",
    "SUBS_ENABLED": "Subtitles enabled.",
    "SUBS_DISABLED": "Subtitles disabled.",
    "NSFW_ENABLED": "NSFW filter enabled.",
    "NSFW_DISABLED": "NSFW filter disabled.",
    "LANG_SET": "Language set to: {lang}",
    "PROFILE_NOT_FOUND": "Profile not found. Send /start first.",
    "USER_NOT_FOUND": "User not found.",
    "USER_BLOCKED": "User {id} blocked.",
    "USER_UNBLOCKED": "User {id} unblocked.",
    "SEND_URL": "Send me a URL to download media, or use /help for commands.",
    "CLEAN_DONE": "Cleaned {count} files ({size} MB).",
    "CLEAN_EMPTY": "Download directory is clean.",
}
