from __future__ import annotations

from openai import OpenAI

# 默认提示词模板
DEFAULT_PROMPT_TEMPLATE = """你是一个短视频解说词写手。根据以下备注内容，撰写一段口播解说词。

备注：{notes}

要求：
- 口语化，适合人声朗读
- 时长约 15-30 秒
- 自然流畅，像真人说话"""


class AIClient:
    """OpenAI 兼容 API 客户端"""

    def __init__(
        self,
        endpoint: str = "",
        api_key: str = "",
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 512,
        prompt_template: str = "",
    ) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.prompt_template = prompt_template or DEFAULT_PROMPT_TEMPLATE

    def is_configured(self) -> bool:
        return bool(self.endpoint and self.api_key)

    def generate_commentary(self, notes: str) -> str:
        """基于备注生成解说词"""
        if not self.is_configured():
            raise RuntimeError("AI 未配置：请先在设置中填写 API endpoint 和 key")

        prompt = self.prompt_template.format(notes=notes)

        client = OpenAI(base_url=f"{self.endpoint}/v1", api_key=self.api_key)
        resp = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        text = resp.choices[0].message.content.strip()
        return text
