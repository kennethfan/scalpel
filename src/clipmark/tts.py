from __future__ import annotations

import asyncio
from pathlib import Path

import edge_tts


def synthesize(text: str, output_path: str | Path, voice: str = "zh-CN-XiaoxiaoNeural") -> str:
    """将文本合成为音频文件，返回输出路径"""
    output_path = str(output_path)

    async def _run() -> None:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)

    asyncio.run(_run())
    return output_path
