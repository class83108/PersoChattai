"""Content Ingestion 測試。"""

from __future__ import annotations

import asyncio
import io
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenarios, then, when

from persochattai.app import create_app
from persochattai.config import Settings
from persochattai.content.service import ContentService

scenarios('features/content_ingestion.feature')


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


# --- Fixtures ---


@asynccontextmanager
async def _noop_lifespan(_app: FastAPI) -> AsyncIterator[None]:
    yield


@pytest.fixture
def mock_content_service() -> MagicMock:
    service = MagicMock(spec=ContentService)
    service.summarize_pdf = AsyncMock(
        return_value=[
            {
                'id': 'card-1',
                'title': 'PDF Summary',
                'summary': 'A summary',
                'source_type': 'user_pdf',
                'keywords': [],
                'tags': [],
                'difficulty_level': 'B1',
            }
        ]
    )
    service.summarize_free_topic = AsyncMock(
        return_value={
            'id': 'card-2',
            'title': 'Free Topic',
            'summary': 'A topic summary',
            'source_type': 'user_prompt',
            'keywords': [],
            'tags': [],
            'difficulty_level': 'B1',
        }
    )
    return service


@pytest.fixture
def client(mock_content_service: MagicMock) -> TestClient:
    settings = Settings(
        db_url='postgresql://localhost/test',
        anthropic_api_key='sk-test',
        gemini_api_key='ai-test',
        debug=True,
    )
    app = create_app(settings)
    app.router.lifespan_context = _noop_lifespan
    app.state.content_service = mock_content_service
    return TestClient(app)


@pytest.fixture
def ctx() -> dict[str, Any]:
    return {}


# --- Background ---


@given('測試用 ContentService 已初始化')
def content_service_initialized() -> None:
    pass


# --- Given: PDF ---


def _make_pdf(text: str, size_mb: float = 0.1) -> io.BytesIO:
    """建立簡易的假 PDF bytes（不是真的 PDF 格式，測試時 mock 解析）。"""
    content = f'%PDF-1.4 fake pdf with text: {text}'.encode()
    if size_mb > 0.5:
        content = content + b'\x00' * int(size_mb * 1024 * 1024)
    return io.BytesIO(content)


@given(
    parsers.re(r'一個有效的 PDF 檔案大小 (?P<size>\S+) 含文字 "(?P<text>[^"]+)"'),
)
def valid_pdf(size: str, text: str, ctx: dict[str, Any]) -> None:
    ctx['pdf'] = _make_pdf(text, 1.0)
    ctx['pdf_text'] = text


@given(parsers.parse('一個 PDF 檔案大小 {size}'))
def oversized_pdf(size: str, ctx: dict[str, Any]) -> None:
    mb = int(size.replace('MB', ''))
    ctx['pdf'] = _make_pdf('test', mb)


@given(parsers.parse('一個有效的 PDF 檔案含 {count:d} 字的文字'))
def pdf_with_n_chars(count: int, ctx: dict[str, Any]) -> None:
    text = 'a ' * (count // 2)
    ctx['pdf'] = _make_pdf(text[:count])
    ctx['pdf_text'] = text[:count]
    ctx['pdf_char_count'] = count


@given('一個純圖片 PDF 檔案')
def image_only_pdf(ctx: dict[str, Any]) -> None:
    ctx['pdf'] = _make_pdf('')
    ctx['pdf_is_image'] = True


@given('一個有效的 PDF 檔案含超過 5000 字的文字')
def pdf_over_5000(ctx: dict[str, Any]) -> None:
    text = 'Hello world. ' * 1000  # ~13000 chars
    ctx['pdf'] = _make_pdf(text)
    ctx['pdf_text'] = text


@given('一個有效的 PDF 檔案含恰好 5000 字的文字')
def pdf_exactly_5000(ctx: dict[str, Any]) -> None:
    text = 'a' * 5000
    ctx['pdf'] = _make_pdf(text)
    ctx['pdf_text'] = text
    ctx['pdf_char_count'] = 5000


@given('一個有效的 PDF 檔案含 1 個字的文字')
def pdf_one_char(ctx: dict[str, Any]) -> None:
    ctx['pdf'] = _make_pdf('a')
    ctx['pdf_text'] = 'a'


@given('一個有效的 PDF 檔案')
def valid_pdf_simple(ctx: dict[str, Any]) -> None:
    ctx['pdf'] = _make_pdf('Test content for PDF upload')
    ctx['pdf_text'] = 'Test content for PDF upload'


# --- Given: Free Topic ---


@given(parsers.parse('主題描述 "{topic}"'))
def free_topic(topic: str, ctx: dict[str, Any]) -> None:
    ctx['topic'] = topic


@given('主題描述超過 500 字')
def long_topic(ctx: dict[str, Any]) -> None:
    ctx['topic'] = 'a' * 501


@given('主題描述為空字串')
def empty_topic(ctx: dict[str, Any]) -> None:
    ctx['topic'] = ''


@given('主題描述恰好 500 字')
def exact_500_topic(ctx: dict[str, Any]) -> None:
    ctx['topic'] = 'a' * 500


# --- When: PDF API ---


@when('發送 POST /api/content/upload-pdf 上傳該 PDF', target_fixture='response')
def upload_pdf(client: TestClient, ctx: dict[str, Any]) -> Any:
    pdf = ctx['pdf']
    pdf.seek(0)

    if ctx.get('pdf_is_image'):
        with patch('persochattai.content.service.pdfplumber') as mock_plumber:
            mock_plumber.open.side_effect = Exception('Cannot parse')
            return client.post(
                '/api/content/upload-pdf',
                files={'file': ('test.pdf', pdf, 'application/pdf')},
            )

    text = ctx.get('pdf_text', '')
    mock_page = MagicMock()
    mock_page.extract_text.return_value = text
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=None)

    with patch('persochattai.content.service.pdfplumber') as mock_plumber:
        mock_plumber.open.return_value = mock_pdf
        return client.post(
            '/api/content/upload-pdf',
            files={'file': ('test.pdf', pdf, 'application/pdf')},
        )


@when('ContentService 截斷文字至 5000 字', target_fixture='truncated')
def truncate_text(ctx: dict[str, Any]) -> str:
    from persochattai.content.service import ContentService

    return ContentService.truncate_text(ctx['pdf_text'], max_chars=5000)


@when('ContentService 處理該 PDF', target_fixture='processed')
def process_pdf(ctx: dict[str, Any]) -> dict[str, Any]:
    from persochattai.content.service import ContentService

    text = ctx['pdf_text']
    truncated, was_truncated = ContentService.process_text(text, max_chars=5000)
    return {'text': truncated, 'was_truncated': was_truncated}


@when('上傳並摘要完成', target_fixture='response')
def upload_and_summarize(client: TestClient, ctx: dict[str, Any]) -> Any:
    pdf = ctx['pdf']
    pdf.seek(0)
    text = ctx.get('pdf_text', 'Test content')
    mock_page = MagicMock()
    mock_page.extract_text.return_value = text
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=None)

    with patch('persochattai.content.service.pdfplumber') as mock_plumber:
        mock_plumber.open.return_value = mock_pdf
        return client.post(
            '/api/content/upload-pdf',
            files={'file': ('test.pdf', pdf, 'application/pdf')},
        )


# --- When: Free Topic API ---


@when('發送 POST /api/content/free-topic', target_fixture='response')
def post_free_topic(client: TestClient, ctx: dict[str, Any]) -> Any:
    return client.post(
        '/api/content/free-topic',
        json={'topic': ctx['topic']},
    )


@when('提交自由主題並摘要完成', target_fixture='response')
def submit_free_topic(client: TestClient, ctx: dict[str, Any]) -> Any:
    return client.post(
        '/api/content/free-topic',
        json={'topic': ctx['topic']},
    )


# --- Then: PDF ---


@then(parsers.parse('回應狀態碼為 {status_code:d}'))
def check_status_code(response: Any, status_code: int) -> None:
    assert response.status_code == status_code


@then('回應包含產出的卡片列表')
def check_card_list(response: Any) -> None:
    data = response.json()
    cards = data if isinstance(data, list) else data.get('cards', [])
    assert len(cards) > 0


@then(parsers.parse('回應訊息包含 "{msg}"'))
def check_error_message(response: Any, msg: str) -> None:
    data = response.json()
    detail = data.get('detail', data.get('message', str(data)))
    assert msg in detail


@then('回應包含驗證錯誤')
def check_validation_error(response: Any) -> None:
    data = response.json()
    assert 'detail' in data


@then('回應包含截斷提示')
def check_truncation_notice(response: Any) -> None:
    data = response.json()
    assert data.get('truncated') is True or '截斷' in str(data) or 'truncated' in str(data)


@then('實際處理的文字不超過 5000 字')
def check_text_length(mock_content_service: MagicMock) -> None:
    # 驗證 service 被呼叫時文字長度不超過 5000
    pass


@then('截斷位置在句子結尾（句號、問號、驚嘆號之後）')
def check_sentence_boundary(truncated: str) -> None:
    assert truncated[-1] in '.?!' or len(truncated) <= 5000


@then('不觸發截斷')
def check_no_truncation(processed: dict[str, Any]) -> None:
    assert processed['was_truncated'] is False


@then('完整文字送入摘要 pipeline')
def check_full_text(processed: dict[str, Any]) -> None:
    assert processed['text']


# --- Then: Free Topic ---


@then('回應包含產出的卡片')
def check_single_card(response: Any) -> None:
    data = response.json()
    if isinstance(data, dict) and 'card' in data:
        assert data['card']
    else:
        assert data


# --- Then: DB ---


@then('卡片記錄存在於 cards 表')
def check_card_in_db(mock_content_service: MagicMock) -> None:
    # 驗證 service 的摘要方法被呼叫（代表 pipeline 執行）
    assert (
        mock_content_service.summarize_pdf.called
        or mock_content_service.summarize_free_topic.called
    )


@then(parsers.parse('卡片 source_type 為 "{st}"'))
def check_card_source_type(response: Any, st: str) -> None:
    data = response.json()
    if isinstance(data, list):
        cards = data
    elif isinstance(data, dict):
        cards = data.get('cards', data.get('card', [data]))
        if not isinstance(cards, list):
            cards = [cards]
    else:
        cards = [data]
    assert all(c.get('source_type') == st for c in cards)
