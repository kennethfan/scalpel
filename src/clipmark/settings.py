from __future__ import annotations

import base64
import json
from pathlib import Path

from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .ai_client import DEFAULT_PROMPT_TEMPLATE, AIClient

CONFIG_DIR = Path.home() / ".clipmark"
CONFIG_PATH = CONFIG_DIR / "config.json"

# 尝试使用系统 keychain（macOS Keychain / Windows Credential Manager / libsecret）
_KEYRING_AVAILABLE = False
try:
    import keyring as _keyring

    # 验证 keyring 真正可读写（macOS 未签名 Python 可能写入成功但读取失败）
    _keyring.set_password("__clipmark_test__", "__test__", "1")
    _keyring.get_password("__clipmark_test__", "__test__")
    _keyring.delete_password("__clipmark_test__", "__test__")
    _KEYRING_AVAILABLE = True
except Exception:
    pass

_KEYRING_SERVICE = "clipmark"
_KEYRING_KEY = "api_key"


def _load_api_key() -> str:
    if _KEYRING_AVAILABLE:
        try:
            val = _keyring.get_password(_KEYRING_SERVICE, _KEYRING_KEY)
            if val:
                return val
        except Exception:
            pass
    # Fallback: base64-obfuscated in config
    cfg = _load_config_raw()
    encoded = cfg.get("ai", {}).get("_api_key_b64", "")
    if encoded:
        return base64.b64decode(encoded).decode("utf-8")
    return ""


def _save_api_key(key: str) -> None:
    if _KEYRING_AVAILABLE and key:
        try:
            _keyring.set_password(_KEYRING_SERVICE, _KEYRING_KEY, key)
            # 清理遗留的 base64 存储
            cfg = _load_config_raw()
            cfg.get("ai", {}).pop("_api_key_b64", None)
            _write_config_raw(cfg)
            return
        except Exception:
            pass
    # Fallback: write base64-obfuscated key
    cfg = _load_config_raw()
    cfg.setdefault("ai", {})["_api_key_b64"] = base64.b64encode(
        key.encode("utf-8")
    ).decode("ascii")
    _write_config_raw(cfg)


def _delete_api_key() -> None:
    if _KEYRING_AVAILABLE:
        try:
            _keyring.delete_password(_KEYRING_SERVICE, _KEYRING_KEY)
        except Exception:
            pass
    cfg = _load_config_raw()
    cfg.get("ai", {}).pop("_api_key_b64", None)
    _write_config_raw(cfg)


def _load_config_raw() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def load_config() -> dict:
    cfg = _load_config_raw()
    api_key = _load_api_key()
    if api_key:
        cfg.setdefault("ai", {})["api_key"] = api_key
    return cfg


def save_config(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # 抽出 API key 单独存储
    ai = data.get("ai", {})
    api_key = ai.pop("api_key", "")

    # 保存剩余配置到 JSON
    _write_config_raw(data)

    # 保存 API key 到安全存储
    if api_key:
        _save_api_key(api_key)
    else:
        _delete_api_key()


def _write_config_raw(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


class AISettingsDialog(QDialog):
    """AI 设置对话框"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("AI 设置")
        self.setMinimumWidth(500)

        config = load_config()
        ai_cfg = config.get("ai", {})

        self._result: AIClient | None = None

        layout = QVBoxLayout(self)

        # API 配置
        api_group = QGroupBox("API 配置")
        api_form = QFormLayout(api_group)

        self._endpoint_input = QLineEdit(ai_cfg.get("endpoint", ""))
        self._endpoint_input.setPlaceholderText("https://api.openai.com")
        api_form.addRow("Endpoint:", self._endpoint_input)

        self._key_input = QLineEdit(ai_cfg.get("api_key", ""))
        self._key_input.setPlaceholderText("sk-...")
        self._key_input.setEchoMode(QLineEdit.EchoMode.Password)
        api_form.addRow("API Key:", self._key_input)

        self._model_input = QLineEdit(ai_cfg.get("model", "gpt-4o-mini"))
        self._model_input.setPlaceholderText("gpt-4o-mini")
        api_form.addRow("Model:", self._model_input)

        # 参数配置
        param_group = QGroupBox("请求参数")
        param_form = QFormLayout(param_group)

        self._temp_input = QSpinBox()
        self._temp_input.setRange(0, 100)
        self._temp_input.setValue(int(ai_cfg.get("temperature", 0.7) * 100))
        self._temp_input.setSuffix("%")
        param_form.addRow("Temperature:", self._temp_input)

        self._tokens_input = QSpinBox()
        self._tokens_input.setRange(64, 4096)
        self._tokens_input.setValue(ai_cfg.get("max_tokens", 512))
        self._tokens_input.setSingleStep(64)
        param_form.addRow("Max Tokens:", self._tokens_input)

        # 提示词模板
        prompt_group = QGroupBox("提示词模板")
        prompt_layout = QVBoxLayout(prompt_group)

        self._prompt_input = QPlainTextEdit(ai_cfg.get("prompt_template", ""))
        self._prompt_input.setPlaceholderText(DEFAULT_PROMPT_TEMPLATE)
        self._prompt_input.setMinimumHeight(120)
        prompt_layout.addWidget(self._prompt_input)

        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(api_group)
        layout.addWidget(param_group)
        layout.addWidget(prompt_group)
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        endpoint = self._endpoint_input.text().strip()
        api_key = self._key_input.text().strip()
        model = self._model_input.text().strip() or "gpt-4o-mini"
        temperature = self._temp_input.value() / 100.0
        max_tokens = self._tokens_input.value()
        prompt = self._prompt_input.toPlainText().strip()

        self._result = AIClient(
            endpoint=endpoint,
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            prompt_template=prompt or DEFAULT_PROMPT_TEMPLATE,
        )

        # 持久化
        save_config({
            "ai": {
                "endpoint": endpoint,
                "api_key": api_key,
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "prompt_template": prompt,
            }
        })
        self.accept()

    @property
    def result(self) -> AIClient | None:
        return self._result
