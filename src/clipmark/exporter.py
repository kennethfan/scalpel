from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def check_ffmpeg() -> None:
    """检查 ffmpeg 是否可用，不可用时抛出友好的 RuntimeError"""
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "未找到 ffmpeg，请先安装 ffmpeg。\n"
            "安装方式：\n"
            "  macOS: brew install ffmpeg\n"
            "  Ubuntu/Debian: sudo apt install ffmpeg\n"
            "  Windows: 从 https://ffmpeg.org/download.html 下载并添加到 PATH"
        )


def cut_video(
    input_path: str,
    start_time: float,
    end_time: float,
    output_path: str | Path,
) -> Path:
    """裁剪视频片段（不重新编码）"""
    check_ffmpeg()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-ss", str(start_time),
        "-to", str(end_time),
        "-c", "copy",
        str(output_path),
    ]
    _run(cmd)
    return output_path


def composite_audio_video(
    video_path: str | Path,
    audio_path: str | Path,
    output_path: str | Path,
) -> Path:
    """将音轨叠加到视频上（配音覆盖原音频）"""
    check_ffmpeg()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        str(output_path),
    ]
    _run(cmd)
    return output_path


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg 执行失败 (exit {result.returncode}):\n"
            f"{result.stderr.strip()}"
        )
