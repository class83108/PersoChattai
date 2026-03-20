"""Foundation spec 測試。"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenario, then, when

from persochattai.app import create_app
from persochattai.config import Settings

# --- Fixtures ---


@asynccontextmanager
async def _noop_lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield


@pytest.fixture
def app_client() -> TestClient:
    settings = Settings(
        db_url='postgresql://localhost/test',
        anthropic_api_key='sk-test',
        gemini_api_key='ai-test',
        debug=True,
    )
    app = create_app(settings)
    app.router.lifespan_context = _noop_lifespan
    return TestClient(app)


# --- 環境配置 Scenarios ---


@scenario('features/foundation.feature', '所有必要環境變數存在時正確建立 Settings')
def test_settings_with_all_env_vars() -> None:
    pass


@scenario('features/foundation.feature', '缺少必要環境變數時拋出錯誤')
def test_settings_missing_env_var() -> None:
    pass


# --- 環境配置 Steps ---


@given(parsers.parse('環境變數 {key} 設為 "{value}"'))
def set_env_var(key: str, value: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(key, value)


@given(parsers.parse('環境變數 {key} 未設定'))
def unset_env_var(key: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(key, raising=False)
    if key != 'ANTHROPIC_API_KEY':
        monkeypatch.setenv('ANTHROPIC_API_KEY', 'sk-test')
    if key != 'GEMINI_API_KEY':
        monkeypatch.setenv('GEMINI_API_KEY', 'ai-test')


@when('建立 Settings 物件', target_fixture='settings')
def create_settings() -> Settings:
    return Settings.from_env()


@when('嘗試建立 Settings 物件', target_fixture='settings_error')
def create_settings_with_error(monkeypatch: pytest.MonkeyPatch) -> pytest.ExceptionInfo[ValueError]:
    monkeypatch.setattr('persochattai.config.load_dotenv', lambda: None)
    with pytest.raises(ValueError, match='DB_URL') as exc_info:
        Settings.from_env()
    return exc_info


@then('Settings 應包含正確的 db_url')
def check_db_url(settings: Settings) -> None:
    assert settings.db_url == 'postgresql://localhost/test'


@then('Settings 應包含正確的 anthropic_api_key')
def check_anthropic_key(settings: Settings) -> None:
    assert settings.anthropic_api_key == 'sk-test'


@then('Settings 應包含正確的 gemini_api_key')
def check_gemini_key(settings: Settings) -> None:
    assert settings.gemini_api_key == 'ai-test'


@then(parsers.parse('應拋出 ValueError 並提示缺少 {var_name}'))
def check_value_error(settings_error: pytest.ExceptionInfo[ValueError], var_name: str) -> None:
    assert var_name in str(settings_error.value)


# --- FastAPI App Scenarios ---


@scenario('features/foundation.feature', 'Health check 回傳正常狀態')
def test_health_check() -> None:
    pass


@scenario('features/foundation.feature', 'Content router 已掛載')
def test_content_router() -> None:
    pass


@scenario('features/foundation.feature', 'Conversation router 已掛載')
def test_conversation_router() -> None:
    pass


@scenario('features/foundation.feature', 'Assessment router 已掛載')
def test_assessment_router() -> None:
    pass


@scenario('features/foundation.feature', 'Usage endpoint 回傳用量摘要')
def test_usage_endpoint() -> None:
    pass


# --- FastAPI App Steps ---


@given('FastAPI app 已建立', target_fixture='client')
def fastapi_app(app_client: TestClient) -> TestClient:
    return app_client


@when(parsers.parse('發送 GET 請求到 "{path}"'), target_fixture='response')
def send_get_request(client: TestClient, path: str) -> Any:
    return client.get(path)


@then(parsers.parse('回應狀態碼為 {status_code:d}'))
def check_status_code(response: Any, status_code: int) -> None:
    assert response.status_code == status_code


@then(parsers.parse('回應內容包含 "{field}" 為 "{value}"'))
def check_response_field(response: Any, field: str, value: str) -> None:
    data = response.json()
    assert data[field] == value


@then(parsers.parse('回應內容包含欄位 "{field}"'))
def check_response_has_field(response: Any, field: str) -> None:
    data = response.json()
    assert field in data
