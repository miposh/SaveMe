from aiogram_dialog import DialogManager


QUALITY_OPTIONS = [
    {"label": "144p", "value": "144", "format_str": "bv*[height<=144]+ba/worst"},
    {"label": "240p", "value": "240", "format_str": "bv*[height<=240]+ba/worst"},
    {"label": "360p", "value": "360", "format_str": "bv*[height<=360]+ba/b"},
    {"label": "480p", "value": "480", "format_str": "bv*[height<=480]+ba/b"},
    {"label": "720p", "value": "720", "format_str": "bv*[height<=720]+ba/b"},
    {"label": "1080p", "value": "1080", "format_str": "bv*[height<=1080]+ba/b"},
    {"label": "1440p", "value": "1440", "format_str": "bv*[height<=1440]+ba/b"},
    {"label": "2160p", "value": "2160", "format_str": "bv*[height<=2160]+ba/b"},
    {"label": "4320p", "value": "4320", "format_str": "bv*[height<=4320]+ba/b"},
]

CODEC_OPTIONS = [
    {"label": "AVC1 (H.264)", "value": "avc1"},
    {"label": "AV01 (AV1)", "value": "av01"},
    {"label": "VP9", "value": "vp9"},
]

PRESETS = [
    {"label": "Best Video", "value": "best", "format_str": "bv+ba/best"},
    {"label": "4K PC", "value": "4k", "format_str": "bv*[height<=2160]+ba/best"},
    {"label": "Full HD Mobile", "value": "fhd", "format_str": "bv*[height<=1080]+ba/b"},
]


def build_format_string(quality: str, codec: str) -> str:
    codec_map = {
        "avc1": "avc1",
        "av01": "av01",
        "vp9": "vp9",
    }
    vc = codec_map.get(codec, "avc1")

    if quality == "best":
        return f"bv*[vcodec*={vc}]+ba/bv+ba/best"

    return (
        f"bv*[vcodec*={vc}][height<={quality}]+ba[acodec*=mp4a]/"
        f"bv*[vcodec*={vc}][height<={quality}]+ba[acodec*=opus]/"
        f"bv*[vcodec*={vc}]+ba/bv+ba/best"
    )


async def get_main_data(dialog_manager: DialogManager, **kwargs) -> dict:
    data = dialog_manager.dialog_data
    current_codec = data.get("codec", "avc1")
    current_quality = data.get("quality", "best")
    return {
        "current_codec": current_codec,
        "current_quality": current_quality,
        "url": data.get("url", ""),
    }


async def get_quality_grid_data(dialog_manager: DialogManager, **kwargs) -> dict:
    return {
        "qualities": QUALITY_OPTIONS,
    }


async def get_codec_data(dialog_manager: DialogManager, **kwargs) -> dict:
    current_codec = dialog_manager.dialog_data.get("codec", "avc1")
    codecs = []
    for c in CODEC_OPTIONS:
        is_active = c["value"] == current_codec
        codecs.append({
            **c,
            "active": is_active,
            "display": f">> {c['label']}" if is_active else c["label"],
        })
    return {"codecs": codecs, "current_codec": current_codec}


async def get_confirm_data(dialog_manager: DialogManager, **kwargs) -> dict:
    data = dialog_manager.dialog_data
    quality = data.get("quality", "best")
    codec = data.get("codec", "avc1")
    format_str = build_format_string(quality, codec)

    quality_label = quality
    for q in QUALITY_OPTIONS:
        if q["value"] == quality:
            quality_label = q["label"]
            break
    for p in PRESETS:
        if p["value"] == quality:
            quality_label = p["label"]
            break

    return {
        "quality_label": quality_label,
        "codec": codec.upper(),
        "format_str": format_str,
        "url": data.get("url", ""),
    }
