import asyncio
import hashlib
import json
import logging
import math
import os
import re
import shutil

logger = logging.getLogger(__name__)


def get_ffmpeg_path() -> str | None:
    path = shutil.which("ffmpeg")
    if path:
        return path
    logger.error("ffmpeg not found in PATH")
    return None


def get_ffprobe_path() -> str | None:
    path = shutil.which("ffprobe")
    if path:
        return path
    logger.error("ffprobe not found in PATH")
    return None


async def get_video_info(video_path: str) -> tuple[int, int, float]:
    ffprobe = get_ffprobe_path()
    if not ffprobe:
        return 0, 0, 0.0

    try:
        proc = await asyncio.create_subprocess_exec(
            ffprobe,
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-show_entries", "format=duration",
            "-of", "json",
            video_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()

        if proc.returncode != 0:
            return 0, 0, 0.0

        data = json.loads(stdout.decode())
        width = data["streams"][0]["width"] if data.get("streams") else 0
        height = data["streams"][0]["height"] if data.get("streams") else 0
        duration = (
            float(data["format"]["duration"])
            if "format" in data and "duration" in data["format"]
            else 0.0
        )
        return width, height, duration
    except Exception as e:
        logger.error("ffprobe error: %s", e)
        return 0, 0, 0.0


async def get_duration(video_path: str) -> float:
    _, _, duration = await get_video_info(video_path)
    return duration


async def get_media_info_dict(file_path: str) -> dict[str, str]:
    ffprobe = get_ffprobe_path()
    if not ffprobe:
        return {"error": "ffprobe not found"}

    try:
        proc = await asyncio.create_subprocess_exec(
            ffprobe,
            "-v", "error",
            "-show_format",
            "-show_streams",
            "-of", "json",
            file_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        data = json.loads(stdout.decode())

        info: dict[str, str] = {}
        fmt = data.get("format", {})
        info["Format"] = fmt.get("format_long_name", fmt.get("format_name", "unknown"))
        info["Duration"] = _format_duration(float(fmt.get("duration", 0)))
        info["Size"] = _format_size(int(fmt.get("size", 0)))
        info["Bitrate"] = f"{int(fmt.get('bit_rate', 0)) // 1000} kbps"

        for stream in data.get("streams", []):
            codec_type = stream.get("codec_type", "")
            if codec_type == "video":
                info["Video codec"] = stream.get("codec_long_name", stream.get("codec_name", ""))
                info["Resolution"] = f"{stream.get('width', 0)}x{stream.get('height', 0)}"
                info["FPS"] = str(eval(stream.get("r_frame_rate", "0/1")))  # noqa: S307
            elif codec_type == "audio":
                info["Audio codec"] = stream.get("codec_long_name", stream.get("codec_name", ""))
                info["Sample rate"] = f"{stream.get('sample_rate', 0)} Hz"
                info["Channels"] = str(stream.get("channels", 0))

        return info
    except Exception as e:
        logger.error("get_media_info_dict error: %s", e)
        return {"error": str(e)}


def _format_duration(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    if size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


async def extract_thumbnail(
    video_path: str,
    output_dir: str,
    thumb_name: str,
    seek_sec: int = 2,
) -> tuple[float, str]:
    thumb_hash = hashlib.md5(thumb_name.encode()).hexdigest()[:10]
    thumb_path = os.path.abspath(os.path.join(output_dir, f"{thumb_hash}.jpg"))

    width, height, duration = await get_video_info(video_path)
    orig_w = width if width > 0 else 1920
    orig_h = height if height > 0 else 1080

    aspect_ratio = orig_w / orig_h
    max_dim = 640

    if aspect_ratio > 1.5:
        thumb_w = max_dim
        thumb_h = int(max_dim / aspect_ratio)
    elif aspect_ratio < 0.75:
        thumb_h = max_dim
        thumb_w = int(max_dim * aspect_ratio)
    else:
        if orig_w >= orig_h:
            thumb_w = max_dim
            thumb_h = int(max_dim / aspect_ratio)
        else:
            thumb_h = max_dim
            thumb_w = int(max_dim * aspect_ratio)

    thumb_w = max(thumb_w, 240)
    thumb_h = max(thumb_h, 240)

    ffmpeg = get_ffmpeg_path()
    if not ffmpeg:
        await _create_default_thumbnail(thumb_path, thumb_w, thumb_h)
        return duration, thumb_path

    try:
        proc = await asyncio.create_subprocess_exec(
            ffmpeg, "-y",
            "-i", video_path,
            "-ss", str(seek_sec),
            "-vframes", "1",
            "-vf", f"scale={thumb_w}:{thumb_h}",
            thumb_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()

        if not os.path.exists(thumb_path):
            await _create_default_thumbnail(thumb_path, thumb_w, thumb_h)
    except Exception as e:
        logger.error("Error creating thumbnail: %s", e)
        await _create_default_thumbnail(thumb_path, thumb_w, thumb_h)

    return duration, thumb_path


async def _create_default_thumbnail(
    thumb_path: str,
    width: int = 480,
    height: int = 480,
) -> None:
    ffmpeg = get_ffmpeg_path()
    if not ffmpeg:
        return

    try:
        proc = await asyncio.create_subprocess_exec(
            ffmpeg, "-y",
            "-f", "lavfi",
            "-i", f"color=c=black:s={width}x{height}",
            "-frames:v", "1",
            thumb_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        logger.info("Created default %dx%d thumbnail at %s", width, height, thumb_path)
    except Exception as e:
        logger.error("Failed to create default thumbnail: %s", e)


async def split_video(
    output_dir: str,
    video_name: str,
    video_path: str,
    video_size: int,
    max_size: int,
    duration: float,
) -> dict:
    rounds = math.floor(video_size / max_size) + 1
    segment_duration = duration / rounds
    caption_list: list[str] = []
    path_list: list[str] = []

    if rounds > 20:
        logger.warning("Excessive split rounds: %d", rounds)

    ffmpeg = get_ffmpeg_path()
    if not ffmpeg:
        return {"video": caption_list, "path": path_list}

    for i in range(rounds):
        start_time = i * segment_duration
        end_time = min((i + 1) * segment_duration, duration)
        part_name = f"{video_name} - Part {i + 1}"
        target_path = os.path.join(output_dir, f"{part_name}.mp4")

        caption_list.append(part_name)
        path_list.append(target_path)

        try:
            logger.info(
                "Splitting part %d/%d (%.1f-%.1f)",
                i + 1, rounds, start_time, end_time,
            )
            proc = await asyncio.create_subprocess_exec(
                ffmpeg, "-y",
                "-i", video_path,
                "-ss", str(start_time),
                "-t", str(end_time - start_time),
                "-c", "copy",
                target_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

            if not os.path.exists(target_path) or os.path.getsize(target_path) == 0:
                logger.error("Failed to create split part %d: %s", i + 1, target_path)
            else:
                logger.info(
                    "Part %d created: %s (%d bytes)",
                    i + 1, target_path, os.path.getsize(target_path),
                )
        except Exception as e:
            logger.error("Error splitting part %d: %s", i + 1, e)

    return {"video": caption_list, "path": path_list}


async def embed_subtitles(
    video_path: str,
    srt_path: str,
    subs_lang: str = "en",
    is_mkv: bool = False,
    max_sub_duration: int = 5400,
    max_sub_size_mb: int = 10,
    max_sub_quality: int = 1080,
) -> bool:
    if not video_path or not os.path.exists(video_path):
        logger.error("Video file not found: %s", video_path)
        return False

    if not srt_path or not os.path.exists(srt_path):
        logger.error("Subtitle file not found: %s", srt_path)
        return False

    ffmpeg = get_ffmpeg_path()
    if not ffmpeg:
        return False

    width, height, total_time = await get_video_info(video_path)
    if width == 0 or height == 0:
        logger.error("Unable to determine video resolution")
        return False

    original_size = os.path.getsize(video_path)
    original_size_mb = original_size / (1024 * 1024)

    if total_time > max_sub_duration:
        logger.info("Video too long for subtitles: %.1f sec", total_time)
        return False

    if original_size_mb > max_sub_size_mb:
        logger.info("Video too large for subtitles: %.2f MB", original_size_mb)
        return False

    if min(width, height) > max_sub_quality:
        logger.info("Video quality too high for subtitles: %dx%d", width, height)
        return False

    _ensure_utf8_srt(srt_path)

    if subs_lang in {"ar", "fa", "ur", "ps", "iw", "he"}:
        _fix_arabic_encoding(srt_path, subs_lang)

    video_dir = os.path.dirname(video_path)
    video_base = os.path.splitext(os.path.basename(video_path))[0]

    if is_mkv or video_path.lower().endswith(".mkv"):
        output_path = os.path.join(video_dir, f"{video_base}_with_subs_temp.mkv")
        cmd = [
            ffmpeg, "-y",
            "-i", video_path,
            "-i", srt_path,
            "-c", "copy",
            "-c:s", "srt",
            "-map", "0",
            "-map", "1:0",
        ]
        if subs_lang and subs_lang != "OFF":
            cmd += ["-metadata:s:s:0", f"language={subs_lang}"]
        cmd.append(output_path)
    else:
        output_path = os.path.join(video_dir, f"{video_base}_with_subs_temp.mp4")
        srt_escaped = srt_path.replace("'", "'\\''")
        filter_arg = (
            f"subtitles='{srt_escaped}':force_style='FontName=Arial Black,"
            f"FontSize=16,PrimaryColour=&Hffffff,OutlineColour=&H000000,"
            f"BackColour=&H80000000,Outline=2,Shadow=1,MarginV=25'"
        )
        cmd = [
            ffmpeg, "-y",
            "-i", video_path,
            "-vf", filter_arg,
            "-c:a", "copy",
            output_path,
        ]

    try:
        logger.info("Running ffmpeg: %s", " ".join(cmd))
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()

        if proc.returncode != 0:
            logger.error("FFmpeg error: %s", stderr.decode()[:500] if stderr else "")
            if os.path.exists(output_path):
                os.remove(output_path)
            return False
    except Exception as e:
        logger.error("FFmpeg execution error: %s", e)
        if os.path.exists(output_path):
            os.remove(output_path)
        return False

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        logger.error("Output file is missing or empty")
        return False

    output_size = os.path.getsize(output_path)
    if output_size < original_size * 0.5:
        logger.error(
            "Output too small: %d bytes (original: %d bytes)",
            output_size, original_size,
        )
        os.remove(output_path)
        return False

    backup_path = video_path + ".backup"
    try:
        os.rename(video_path, backup_path)
        os.rename(output_path, video_path)
        if os.path.exists(backup_path):
            os.remove(backup_path)
    except Exception as e:
        logger.error("Error replacing video file: %s", e)
        if os.path.exists(backup_path):
            try:
                if os.path.exists(video_path):
                    os.remove(video_path)
                os.rename(backup_path, video_path)
            except Exception:
                pass
        if os.path.exists(output_path):
            os.remove(output_path)
        return False

    logger.info("Successfully embedded subtitles")
    return True


def _ensure_utf8_srt(srt_path: str) -> str | None:
    try:
        with open(srt_path, "r", encoding="utf-8") as f:
            f.read()
        return srt_path
    except UnicodeDecodeError:
        try:
            import chardet

            with open(srt_path, "rb") as f:
                raw = f.read()
            detected = chardet.detect(raw)
            encoding = detected.get("encoding") or "cp1252"

            with open(srt_path, "r", encoding=encoding) as f:
                content = f.read()

            with open(srt_path, "w", encoding="utf-8") as f:
                f.write(content)
            return srt_path
        except Exception as e:
            logger.error("Error converting SRT to UTF-8: %s", e)
            return None


def _fix_arabic_encoding(srt_path: str, lang: str) -> str | None:
    try:
        with open(srt_path, "r", encoding="utf-8") as f:
            content = f.read()

        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(content)
        return srt_path
    except Exception as e:
        logger.error("Error fixing Arabic encoding: %s", e)
        return None
