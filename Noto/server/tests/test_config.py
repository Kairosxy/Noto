import json
import os
from pathlib import Path

import pytest

from config import Config, load_config, save_user_config


@pytest.fixture
def fake_root(tmp_path, monkeypatch):
    server_dir = tmp_path / "server"
    server_dir.mkdir()
    (server_dir / "data").mkdir()
    monkeypatch.setattr("config._project_root", lambda: tmp_path)
    # 清理所有 NOTO_* 环境变量，保证测试独立
    for key in list(os.environ):
        if key.startswith("NOTO_"):
            monkeypatch.delenv(key, raising=False)
    return tmp_path


def test_load_config_defaults(fake_root):
    cfg = load_config()
    assert cfg.ai_provider == ""
    assert cfg.ai_api_key == ""


def test_load_config_from_env(fake_root, monkeypatch):
    monkeypatch.setenv("NOTO_AI_PROVIDER", "openai")
    monkeypatch.setenv("NOTO_AI_API_KEY", "sk-xxx")
    cfg = load_config()
    assert cfg.ai_provider == "openai"
    assert cfg.ai_api_key == "sk-xxx"


def test_user_config_overrides_env(fake_root, monkeypatch):
    monkeypatch.setenv("NOTO_AI_PROVIDER", "openai")
    user_file = fake_root / "server" / "data" / "config.json"
    user_file.write_text(json.dumps({"ai_provider": "anthropic"}))
    cfg = load_config()
    assert cfg.ai_provider == "anthropic"


def test_save_user_config_merges(fake_root):
    cfg = load_config()
    save_user_config(cfg, {"ai_provider": "openai", "ai_api_key": "k1"})
    save_user_config(cfg, {"ai_model": "gpt-4o"})
    user_file = fake_root / "server" / "data" / "config.json"
    data = json.loads(user_file.read_text())
    assert data == {"ai_provider": "openai", "ai_api_key": "k1", "ai_model": "gpt-4o"}


def test_safe_settings_hides_keys(fake_root, monkeypatch):
    monkeypatch.setenv("NOTO_AI_API_KEY", "secret")
    cfg = load_config()
    safe = cfg.get_safe_settings()
    assert "secret" not in json.dumps(safe)
    assert safe["ai_api_key_set"] is True


def test_embedding_fallback_to_ai(fake_root, monkeypatch):
    monkeypatch.setenv("NOTO_AI_PROVIDER", "openai")
    monkeypatch.setenv("NOTO_AI_API_KEY", "k1")
    monkeypatch.setenv("NOTO_AI_BASE_URL", "https://api.example.com")
    monkeypatch.setenv("NOTO_EMBEDDING_MODEL", "text-embedding-3-small")
    cfg = load_config()
    eff = cfg.effective_embedding()
    assert eff["provider"] == "openai"
    assert eff["api_key"] == "k1"
    assert eff["base_url"] == "https://api.example.com"
    assert eff["model"] == "text-embedding-3-small"
