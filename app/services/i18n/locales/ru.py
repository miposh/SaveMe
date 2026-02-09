MESSAGES: dict[str, str] = {
    "WELCOME": "Привет, {name}!\n\nОтправь мне URL для скачивания видео, аудио или изображений с 1500+ платформ.\n\nИспользуй /help для информации.",
    "HELP": (
        "<b>Доступные команды:</b>\n\n"
        "/vid <code>URL</code> - Скачать видео\n"
        "/audio <code>URL</code> - Скачать аудио\n"
        "/img <code>URL</code> - Скачать изображения\n"
        "/playlist <code>URL</code> - Скачать плейлист\n"
        "/link <code>URL</code> - Получить прямую ссылку\n"
        "/format - Выбрать формат\n"
        "/subs - Настройки субтитров\n"
        "/split - Настройки разделения\n"
        "/settings - Все настройки\n"
        "/search <code>запрос</code> - Поиск\n"
        "/clean - Очистить временные файлы"
    ),
    "URL_RECEIVED": "URL получен. Загрузка начнется в ближайшее время...",
    "DOWNLOADING": "Загрузка...",
    "UPLOADING": "Отправка...",
    "DOWNLOAD_COMPLETE": "Загрузка завершена!",
    "DOWNLOAD_FAILED": "Ошибка загрузки: {error}",
    "RATE_LIMITED": "Слишком много запросов. Подождите {seconds} секунд.",
    "SUBSCRIBE_FIRST": "Сначала подпишитесь на канал: {url}",
    "BANNED": "Вы заблокированы.",
    "INVALID_URL": "Некорректный URL.",
    "NO_MEDIA_FOUND": "Медиа не найдено.",
    "FILE_TOO_LARGE": "Файл слишком большой ({size} ГБ). Максимум: {max} ГБ.",
    "DURATION_TOO_LONG": "Видео слишком длинное ({duration}). Максимум: {max}.",
    "NSFW_BLOCKED": "NSFW контент заблокирован. Включите через /nsfw.",
    "FORMAT_SELECTED": "Формат установлен: {format}",
    "SPLIT_SET": "Разделение: {size} МБ",
    "SUBS_ENABLED": "Субтитры включены.",
    "SUBS_DISABLED": "Субтитры выключены.",
    "NSFW_ENABLED": "NSFW фильтр включен.",
    "NSFW_DISABLED": "NSFW фильтр выключен.",
    "LANG_SET": "Язык установлен: {lang}",
    "PROFILE_NOT_FOUND": "Профиль не найден. Отправьте /start.",
    "USER_NOT_FOUND": "Пользователь не найден.",
    "USER_BLOCKED": "Пользователь {id} заблокирован.",
    "USER_UNBLOCKED": "Пользователь {id} разблокирован.",
    "SEND_URL": "Отправь мне URL для скачивания, или используй /help.",
    "CLEAN_DONE": "Очищено {count} файлов ({size} МБ).",
    "CLEAN_EMPTY": "Директория загрузок пуста.",
}
