"""Frontend router 基本測試 — 驗證頁面路由與 HTMX partial 端點。"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from persochattai.app import create_app
from persochattai.config import Settings


@pytest.fixture
def client() -> TestClient:
    settings = Settings(
        db_url='postgresql://localhost/test',
        anthropic_api_key='sk-test',
        gemini_api_key='ai-test',
    )
    app = create_app(settings)
    return TestClient(app, raise_server_exceptions=False)


def _mock_request(method: str, url: str) -> httpx.Request:
    return httpx.Request(method, url)


@contextmanager
def _mock_api(
    method: str = 'get',
    json: Any = None,
    status_code: int = 200,
):
    """Context manager that patches httpx.AsyncClient to return a mock response."""
    mock_resp = httpx.Response(
        status_code,
        json=json,
        request=_mock_request(method.upper(), 'http://test'),
    )
    with patch('persochattai.frontend.router.httpx.AsyncClient') as mock_cls:
        mock_client = AsyncMock()
        handler = AsyncMock(return_value=mock_resp)
        if method == 'get':
            mock_client.get = handler
        else:
            mock_client.post = handler
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_cls.return_value = mock_client
        yield mock_client


# --- Page routes ---


class TestPageRoutes:
    def test_index_redirects_to_materials(self, client: TestClient) -> None:
        resp = client.get('/', follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers['location'] == '/materials'

    def test_materials_page(self, client: TestClient) -> None:
        resp = client.get('/materials')
        assert resp.status_code == 200
        assert '素材管理' in resp.text

    def test_roleplay_page(self, client: TestClient) -> None:
        resp = client.get('/roleplay')
        assert resp.status_code == 200
        assert 'Role Play' in resp.text

    def test_report_page(self, client: TestClient) -> None:
        resp = client.get('/report')
        assert resp.status_code == 200
        assert '能力報告' in resp.text

    def test_report_page_has_htmx_partials(self, client: TestClient) -> None:
        resp = client.get('/report')
        for path in [
            '/report/partials/overview',
            '/report/partials/history',
            '/report/partials/vocabulary',
            '/report/partials/usage',
        ]:
            assert f'hx-get="{path}"' in resp.text, f'Missing hx-get for {path}'


# --- Materials partials ---


class TestMaterialsPartials:
    def test_card_list_empty(self, client: TestClient) -> None:
        """API 不可用時回傳空卡片列表。"""
        resp = client.get('/materials/partials/card-list')
        assert resp.status_code == 200

    def test_card_list_with_all_filters(self, client: TestClient) -> None:
        """所有篩選參數都傳入時仍回 200。"""
        resp = client.get(
            '/materials/partials/card-list',
            params={
                'source_type': 'podcast',
                'difficulty': 'B1',
                'keyword': 'test',
                'tag': 'tech',
            },
        )
        assert resp.status_code == 200

    def test_card_list_api_non_200(self, client: TestClient) -> None:
        """API 回 500 時仍 graceful degradation。"""
        with _mock_api(json={'detail': 'error'}, status_code=500):
            resp = client.get('/materials/partials/card-list')
            assert resp.status_code == 200

    def test_upload_pdf_success(self, client: TestClient) -> None:
        """上傳 PDF 成功時渲染結果。"""
        mock_data = {'cards': [{'id': '1', 'title': 'PDF Card'}]}
        with _mock_api(method='post', json=mock_data):
            resp = client.post(
                '/materials/upload-pdf',
                files={'file': ('test.pdf', b'%PDF-fake', 'application/pdf')},
            )
            assert resp.status_code == 200

    def test_upload_pdf_api_error(self, client: TestClient) -> None:
        """上傳 PDF API 回錯誤時顯示錯誤訊息。"""
        with _mock_api(method='post', json={'detail': '格式錯誤'}, status_code=400):
            resp = client.post(
                '/materials/upload-pdf',
                files={'file': ('bad.pdf', b'not-pdf', 'application/pdf')},
            )
            assert resp.status_code == 200
            assert '格式錯誤' in resp.text

    def test_upload_pdf_connection_error(self, client: TestClient) -> None:
        """上傳 PDF API 連線失敗時 graceful degradation。"""
        resp = client.post(
            '/materials/upload-pdf',
            files={'file': ('test.pdf', b'%PDF-fake', 'application/pdf')},
        )
        assert resp.status_code == 200
        assert '上傳失敗' in resp.text

    def test_free_topic_success(self, client: TestClient) -> None:
        """自由主題提交成功。"""
        mock_data = {'card': {'id': '1', 'title': 'Free Topic Card'}}
        with _mock_api(method='post', json=mock_data):
            resp = client.post(
                '/materials/free-topic',
                json={'topic': 'AI in education', 'difficulty': 'B2'},
            )
            assert resp.status_code == 200

    def test_free_topic_api_error(self, client: TestClient) -> None:
        """自由主題 API 回錯誤時顯示錯誤訊息。"""
        with _mock_api(method='post', json={'detail': '主題無效'}, status_code=400):
            resp = client.post(
                '/materials/free-topic',
                json={'topic': ''},
            )
            assert resp.status_code == 200
            assert '主題無效' in resp.text

    def test_free_topic_connection_error(self, client: TestClient) -> None:
        """自由主題 API 連線失敗時 graceful degradation。"""
        resp = client.post(
            '/materials/free-topic',
            json={'topic': 'test'},
        )
        assert resp.status_code == 200
        assert '提交失敗' in resp.text

    def test_free_topic_returns_cards_list(self, client: TestClient) -> None:
        """自由主題 API 回傳 cards 列表時正確處理。"""
        mock_data = {'cards': [{'id': '1', 'title': 'Card A'}, {'id': '2', 'title': 'Card B'}]}
        with _mock_api(method='post', json=mock_data):
            resp = client.post(
                '/materials/free-topic',
                json={'topic': 'AI'},
            )
            assert resp.status_code == 200


# --- Roleplay partials ---


class TestRoleplayPartials:
    def test_history_no_user_id(self, client: TestClient) -> None:
        """沒有 user_id 時回傳空歷史。"""
        resp = client.get('/roleplay/partials/history')
        assert resp.status_code == 200

    def test_history_with_user_id_api_down(self, client: TestClient) -> None:
        """API 不可用時仍回傳 200。"""
        resp = client.get('/roleplay/partials/history', params={'user_id': 'u-123'})
        assert resp.status_code == 200

    def test_history_renders_conversations(self, client: TestClient) -> None:
        """proxy 回傳對話歷史時渲染列表。"""
        mock_data = [{'id': 'c-1', 'status': 'completed', 'created_at': '2026-03-20'}]
        with _mock_api(json=mock_data):
            resp = client.get('/roleplay/partials/history', params={'user_id': 'u-1'})
            assert resp.status_code == 200


# --- Report partials ---


class TestReportPartials:
    @pytest.mark.parametrize(
        'path',
        [
            '/report/partials/overview',
            '/report/partials/history',
            '/report/partials/vocabulary',
            '/report/partials/usage',
        ],
    )
    def test_partial_returns_200_without_user_id(self, client: TestClient, path: str) -> None:
        """沒有 user_id 時回傳空狀態 HTML。"""
        resp = client.get(path)
        assert resp.status_code == 200

    @pytest.mark.parametrize(
        'path',
        [
            '/report/partials/overview',
            '/report/partials/history',
            '/report/partials/vocabulary',
            '/report/partials/usage',
        ],
    )
    def test_partial_returns_200_with_user_id_api_down(self, client: TestClient, path: str) -> None:
        """API 不可用時仍回傳 200（graceful degradation）。"""
        resp = client.get(path, params={'user_id': 'u-123'})
        assert resp.status_code == 200

    def test_overview_renders_cefr_badge(self, client: TestClient) -> None:
        """proxy 回傳 progress 資料時渲染 CEFR badge。"""
        mock_data = {
            'cefr_level': 'B2',
            'lexical_score': 6.5,
            'fluency_score': 7.0,
            'grammar_score': 5.5,
        }
        with _mock_api(json=mock_data):
            resp = client.get('/report/partials/overview', params={'user_id': 'u-1'})
            assert resp.status_code == 200
            assert 'B2' in resp.text

    def test_history_renders_assessments(self, client: TestClient) -> None:
        """proxy 回傳評估歷史時渲染列表。"""
        mock_data: list[dict[str, Any]] = [
            {
                'created_at': '2026-03-20',
                'cefr_level': 'B1',
                'lexical_score': 5.0,
                'fluency_score': 4.5,
                'grammar_score': 5.0,
            }
        ]
        with _mock_api(json=mock_data):
            resp = client.get('/report/partials/history', params={'user_id': 'u-1'})
            assert resp.status_code == 200
            assert 'B1' in resp.text

    def test_vocabulary_renders_stats(self, client: TestClient) -> None:
        """proxy 回傳詞彙統計時渲染。"""
        mock_data = {'total_words': 1500, 'new_word_rate': 0.12, 'k1_ratio': 0.85}
        with _mock_api(json=mock_data):
            resp = client.get('/report/partials/vocabulary', params={'user_id': 'u-1'})
            assert resp.status_code == 200
            assert '1500' in resp.text

    def test_usage_renders_summary(self, client: TestClient) -> None:
        """proxy 回傳用量資料時渲染。"""
        mock_data = {'total_tokens': 50000, 'total_cost': 1.2345, 'total_requests': 42}
        with _mock_api(json=mock_data):
            resp = client.get('/report/partials/usage', params={'user_id': 'u-1'})
            assert resp.status_code == 200
            assert '50,000' in resp.text


# --- _api_url ---


class TestSafePathSegment:
    def test_normal_value(self) -> None:
        from persochattai.frontend.router import _safe_path_segment

        assert _safe_path_segment('user-123') == 'user-123'

    def test_rejects_slash(self) -> None:
        from persochattai.frontend.router import _safe_path_segment

        assert _safe_path_segment('../../etc/passwd') == ''

    def test_rejects_dotdot(self) -> None:
        from persochattai.frontend.router import _safe_path_segment

        assert _safe_path_segment('..') == ''

    def test_rejects_empty(self) -> None:
        from persochattai.frontend.router import _safe_path_segment

        assert _safe_path_segment('') == ''
        assert _safe_path_segment('   ') == ''

    def test_encodes_special_chars(self) -> None:
        from persochattai.frontend.router import _safe_path_segment

        result = _safe_path_segment('user name')
        assert '/' not in result
        assert result == 'user%20name'

    def test_malicious_user_id_returns_empty_state(self, client: TestClient) -> None:
        """惡意 user_id 被過濾後回傳空狀態。"""
        resp = client.get(
            '/report/partials/overview',
            params={'user_id': '../../etc/passwd'},
        )
        assert resp.status_code == 200


class TestApiUrl:
    def test_api_url_builds_from_scope(self, client: TestClient) -> None:
        """_api_url 使用 ASGI scope 而非 Host header。"""
        from persochattai.frontend.router import _api_url

        scope = {'type': 'http', 'scheme': 'http', 'server': ('127.0.0.1', 8000)}
        mock_request = type('R', (), {'scope': scope})()
        assert _api_url('/api/test', mock_request) == 'http://127.0.0.1:8000/api/test'

    def test_api_url_fallback_without_server(self, client: TestClient) -> None:
        """沒有 server 時 fallback 到 127.0.0.1:8000。"""
        from persochattai.frontend.router import _api_url

        scope = {'type': 'http', 'scheme': 'http'}
        mock_request = type('R', (), {'scope': scope})()
        assert _api_url('/api/test', mock_request) == 'http://127.0.0.1:8000/api/test'
