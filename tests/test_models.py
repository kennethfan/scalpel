from __future__ import annotations

from clipmark.models import CompositeStatus, Marker, OutputClip, Project, TTSStatus


class TestMarker:
    def test_default_values(self) -> None:
        m = Marker(name="test", start_time=1.0, end_time=5.0)
        assert m.name == "test"
        assert m.start_time == 1.0
        assert m.end_time == 5.0
        assert m.notes == ""
        assert m.commentary == ""
        assert m.tts_status == TTSStatus.pending
        assert len(m.id) == 12

    def test_duration(self) -> None:
        m = Marker(name="clip", start_time=10.0, end_time=15.5)
        assert m.duration == 5.5

    def test_duration_zero_when_reversed(self) -> None:
        m = Marker(name="bad", start_time=10.0, end_time=5.0)
        assert m.duration == 0.0


class TestOutputClip:
    def test_default_values(self) -> None:
        oc = OutputClip(marker_id="abc123")
        assert oc.marker_id == "abc123"
        assert oc.video_path is None
        assert oc.audio_path is None
        assert oc.composite_path is None
        assert oc.composite_status == CompositeStatus.pending


class TestProject:
    def test_default_values(self) -> None:
        p = Project(name="test_project")
        assert p.name == "test_project"
        assert p.video_paths == []
        assert p.markers == []
        assert p.output_clips == []
        assert p.output_dir is None

    def test_with_markers(self) -> None:
        markers = [
            Marker(name="a", start_time=0.0, end_time=10.0),
            Marker(name="b", start_time=10.0, end_time=20.0),
        ]
        p = Project(name="multi", markers=markers)
        assert len(p.markers) == 2

    def test_video_paths(self) -> None:
        p = Project(name="vids", video_paths=["/tmp/vid1.mp4", "/tmp/vid2.mp4"])
        assert len(p.video_paths) == 2
