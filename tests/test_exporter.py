from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from clipmark.exporter import check_ffmpeg, cut_video, composite_audio_video


class TestCheckFfmpeg:
    @patch("clipmark.exporter.shutil.which", return_value="/usr/bin/ffmpeg")
    def test_ffmpeg_found(self, mock_which) -> None:
        check_ffmpeg()  # should not raise

    @patch("clipmark.exporter.shutil.which", return_value=None)
    def test_ffmpeg_not_found(self, mock_which) -> None:
        with pytest.raises(RuntimeError, match="未找到 ffmpeg"):
            check_ffmpeg()


class TestCutVideo:
    @patch("clipmark.exporter.shutil.which", return_value="/usr/bin/ffmpeg")
    @patch("clipmark.exporter.subprocess.run")
    def test_cut_video_builds_correct_command(
        self, mock_run, mock_which, tmp_path: Path
    ) -> None:
        mock_run.return_value = MagicMock(returncode=0)
        output = tmp_path / "clip.mp4"
        result = cut_video("/input/vid.mp4", 10.5, 25.0, output)
        assert result == output
        cmd = mock_run.call_args[0][0]
        assert "ffmpeg" in cmd
        assert "-ss" in cmd
        assert "10.5" in cmd
        assert "-to" in cmd
        assert "25.0" in cmd
        assert str(output) in cmd

    @patch("clipmark.exporter.shutil.which", return_value="/usr/bin/ffmpeg")
    @patch("clipmark.exporter.subprocess.run")
    def test_creates_output_dir(self, mock_run, mock_which, tmp_path: Path) -> None:
        mock_run.return_value = MagicMock(returncode=0)
        nested = tmp_path / "sub" / "dir" / "clip.mp4"
        cut_video("/input/vid.mp4", 0.0, 10.0, nested)
        assert nested.parent.exists()


class TestCompositeAudioVideo:
    @patch("clipmark.exporter.shutil.which", return_value="/usr/bin/ffmpeg")
    @patch("clipmark.exporter.subprocess.run")
    def test_composite_builds_correct_command(
        self, mock_run, mock_which, tmp_path: Path
    ) -> None:
        mock_run.return_value = MagicMock(returncode=0)
        video = tmp_path / "vid.mp4"
        audio = tmp_path / "audio.mp3"
        output = tmp_path / "out.mp4"
        video.touch()
        audio.touch()
        result = composite_audio_video(video, audio, output)
        assert result == output
        cmd = mock_run.call_args[0][0]
        assert str(video) in cmd
        assert str(audio) in cmd
        assert "-c:v" in cmd
        assert "copy" in cmd
        assert "-c:a" in cmd
        assert "aac" in cmd
