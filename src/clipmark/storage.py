from __future__ import annotations

import json
from pathlib import Path

from .models import Marker, OutputClip, Project


def save_project(project: Project, path: str | Path) -> None:
    """将 Project 序列化为 JSON 文件"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = project.model_dump(mode="json")
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_project(path: str | Path) -> Project:
    """从 JSON 文件反序列化 Project"""
    path = Path(path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    return Project(**raw)
