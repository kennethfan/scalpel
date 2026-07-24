from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from clipmark.ai_client import AIClient


class TestAIClient:
    def test_is_configured_returns_true_when_configured(self) -> None:
        client = AIClient(endpoint="https://api.openai.com", api_key="sk-test")
        assert client.is_configured() is True

    def test_is_configured_returns_false_when_missing_key(self) -> None:
        client = AIClient(endpoint="https://api.openai.com", api_key="")
        assert client.is_configured() is False

    def test_is_configured_returns_false_when_missing_endpoint(self) -> None:
        client = AIClient(endpoint="", api_key="sk-test")
        assert client.is_configured() is False

    def test_generate_commentary_raises_when_unconfigured(self) -> None:
        client = AIClient()
        with pytest.raises(RuntimeError, match="AI 未配置"):
            client.generate_commentary("some notes")

    @patch("clipmark.ai_client.OpenAI")
    def test_generate_commentary_returns_text(self, mock_openai: MagicMock) -> None:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=" 生成的解说词 "))]
        )
        mock_openai.return_value = mock_instance

        client = AIClient(endpoint="https://api.openai.com", api_key="sk-test")
        result = client.generate_commentary("测试备注")
        assert result == "生成的解说词"

    @patch("clipmark.ai_client.OpenAI")
    def test_generate_commentary_uses_prompt_template(
        self, mock_openai: MagicMock
    ) -> None:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="ok"))]
        )
        mock_openai.return_value = mock_instance

        client = AIClient(
            endpoint="https://api.openai.com",
            api_key="sk-test",
            prompt_template="Write about: {notes}",
        )
        client.generate_commentary("cats")
        called_kwargs = mock_instance.chat.completions.create.call_args.kwargs
        assert called_kwargs["messages"][0]["content"] == "Write about: cats"

    @patch("clipmark.ai_client.OpenAI")
    def test_generate_commentary_passes_params(self, mock_openai: MagicMock) -> None:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="ok"))]
        )
        mock_openai.return_value = mock_instance

        client = AIClient(
            endpoint="https://api.openai.com",
            api_key="sk-test",
            model="gpt-4",
            temperature=0.5,
            max_tokens=256,
        )
        client.generate_commentary("notes")
        called_kwargs = mock_instance.chat.completions.create.call_args.kwargs
        assert called_kwargs["model"] == "gpt-4"
        assert called_kwargs["temperature"] == 0.5
        assert called_kwargs["max_tokens"] == 256
