from __future__ import annotations

import json
from pathlib import Path

from clipmark.models import Marker, Project
from clipmark.storage import load_project, save_project


class TestSaveLoadRoundtrip:
    def test_empty_project(self, tmp_path: Path) -> None:
        p = Project(name="empty")
        path = tmp_path / "project.json"
        save_project(p, path)
        assert path.exists()
        loaded = load_project(path)
        assert loaded.name == "empty"
        assert loaded.markers == []
        assert loaded.video_paths == []

    def test_project_with_markers(self, tmp_path: Path) -> None:
        markers = [
            Marker(name="clip1", start_time=0.0, end_time=10.0, notes="hello"),
            Marker(name="clip2", start_time=15.0, end_time=30.0, notes="world"),
        ]
        p = Project(
            name="test",
            video_paths=["/tmp/vid.mp4"],
            markers=markers,
        )
        path = tmp_path / "test.json"
        save_project(p, path)
        loaded = load_project(path)
        assert loaded.name == "test"
        assert loaded.video_paths == ["/tmp/vid.mp4"]
        assert len(loaded.markers) == 2
        assert loaded.markers[0].name == "clip1"
        assert loaded.markers[0].start_time == 0.0
        assert loaded.markers[0].end_time == 10.0
        assert loaded.markers[0].notes == "hello"
        assert loaded.markers[1].name == "clip2"
        assert loaded.markers[1].start_time == 15.0
        assert loaded.markers[1].end_time == 30.0

    def test_json_format(self, tmp_path: Path) -> None:
        p = Project(name="fmt_test")
        path = tmp_path / "fmt.json"
        save_project(p, path)
        raw = json.loads(path.read_text(encoding="utf-8"))
        assert raw["name"] == "fmt_test"
        assert "video_paths" in raw
        assert "markers" in raw
        assert "output_clips" in raw
