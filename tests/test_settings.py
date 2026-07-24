from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from clipmark.settings import load_config, save_config


class TestConfigPersistence:
    def test_load_empty_when_no_file(self, tmp_path: Path) -> None:
        with patch("clipmark.settings.CONFIG_PATH", tmp_path / "nonexistent.json"):
            cfg = load_config()
            assert cfg == {}

    def test_save_and_load_roundtrip(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.json"
        with (
            patch("clipmark.settings.CONFIG_PATH", config_path),
            patch("clipmark.settings._KEYRING_AVAILABLE", False),
        ):
            save_config({
                "ai": {
                    "endpoint": "https://test.api.com",
                    "api_key": "sk-test-key-123",
                    "model": "gpt-4",
                    "temperature": 0.5,
                    "max_tokens": 256,
                    "prompt_template": "Write: {notes}",
                }
            })

            # 验证 JSON 中不包含明文 api_key
            raw = config_path.read_text(encoding="utf-8")
            assert "sk-test-key-123" not in raw
            assert "_api_key_b64" in raw

            cfg = load_config()
            assert cfg["ai"]["endpoint"] == "https://test.api.com"
            assert cfg["ai"]["api_key"] == "sk-test-key-123"
            assert cfg["ai"]["model"] == "gpt-4"
            assert cfg["ai"]["temperature"] == 0.5
            assert cfg["ai"]["max_tokens"] == 256

    def test_save_without_api_key(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.json"
        with (
            patch("clipmark.settings.CONFIG_PATH", config_path),
            patch("clipmark.settings._KEYRING_AVAILABLE", False),
        ):
            save_config({
                "ai": {
                    "endpoint": "https://test.api.com",
                    "api_key": "",
                    "model": "gpt-4o-mini",
                }
            })
            raw = config_path.read_text(encoding="utf-8")
            assert "_api_key_b64" not in raw
