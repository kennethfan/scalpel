from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

from clipmark.tts import synthesize


class TestSynthesize:
    @patch("clipmark.tts.edge_tts.Communicate")
    def test_synthesize_returns_output_path(self, mock_comm, tmp_path: Path) -> None:
        mock_instance = mock_comm.return_value
        mock_instance.save = AsyncMock()

        output = tmp_path / "test.mp3"
        result = synthesize("你好世界", output)
        assert result == str(output)
        mock_comm.assert_called_once_with("你好世界", "zh-CN-XiaoxiaoNeural")

    @patch("clipmark.tts.edge_tts.Communicate")
    def test_synthesize_custom_voice(self, mock_comm, tmp_path: Path) -> None:
        mock_instance = mock_comm.return_value
        mock_instance.save = AsyncMock()

        output = tmp_path / "test.mp3"
        synthesize("hello", output, voice="en-US-JennyNeural")
        mock_comm.assert_called_once_with("hello", "en-US-JennyNeural")
