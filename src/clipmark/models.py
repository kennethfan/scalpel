from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TTSStatus(str, Enum):
    """TTS 合成状态"""
    pending = "pending"
    generating = "generating"
    done = "done"
    failed = "failed"


class CompositeStatus(str, Enum):
    """视频合成状态"""
    pending = "pending"
    processing = "processing"
    done = "done"
    failed = "failed"


class Marker(BaseModel):
    """单个区间标记"""
    id: str = Field(default_factory=lambda: __import__("uuid").uuid4().hex[:12])
    name: str = ""
    start_time: float = 0.0  # 起始时间（秒）
    end_time: float = 0.0  # 结束时间（秒）
    notes: str = ""  # 用户备注
    commentary: str = ""  # AI 生成的解说词
    tts_status: TTSStatus = TTSStatus.pending

    @property
    def duration(self) -> float:
        return max(0.0, self.end_time - self.start_time)


class OutputClip(BaseModel):
    """输出片段"""
    marker_id: str
    video_path: Optional[str] = None
    audio_path: Optional[str] = None
    composite_path: Optional[str] = None
    composite_status: CompositeStatus = CompositeStatus.pending


class Project(BaseModel):
    """ClipMark 项目"""
    name: str
    video_paths: list[str] = Field(default_factory=list)
    markers: list[Marker] = Field(default_factory=list)
    output_clips: list[OutputClip] = Field(default_factory=list)
    output_dir: Optional[str] = None
