"""Frontend router 基本測試 — 驗證頁面路由與 HTMX partial 端點。"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from persochattai.app import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app, raise_server_exceptions=False)


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

    def test_card_list_with_filters(self, client: TestClient) -> None:
        resp = client.get(
            '/materials/partials/card-list',
            params={'source_type': 'podcast', 'difficulty': 'B1', 'keyword': 'test'},
        )
        assert resp.status_code == 200

    def test_card_list_api_error_graceful(self, client: TestClient) -> None:
        """API 連線失敗時仍回傳空列表（graceful degradation）。"""
        resp = client.get('/materials/partials/card-list')
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
        mock_resp = httpx.Response(200, json=mock_data, request=httpx.Request('GET', 'http://test'))
        with patch('persochattai.frontend.router.httpx.AsyncClient') as mock_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

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
        mock_resp = httpx.Response(200, json=mock_data, request=httpx.Request('GET', 'http://test'))
        with patch('persochattai.frontend.router.httpx.AsyncClient') as mock_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            resp = client.get('/report/partials/history', params={'user_id': 'u-1'})
            assert resp.status_code == 200
            assert 'B1' in resp.text

    def test_vocabulary_renders_stats(self, client: TestClient) -> None:
        """proxy 回傳詞彙統計時渲染。"""
        mock_data = {'total_words': 1500, 'new_word_rate': 0.12, 'k1_ratio': 0.85}
        mock_resp = httpx.Response(200, json=mock_data, request=httpx.Request('GET', 'http://test'))
        with patch('persochattai.frontend.router.httpx.AsyncClient') as mock_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            resp = client.get('/report/partials/vocabulary', params={'user_id': 'u-1'})
            assert resp.status_code == 200
            assert '1500' in resp.text

    def test_usage_renders_summary(self, client: TestClient) -> None:
        """proxy 回傳用量資料時渲染。"""
        mock_data = {'total_tokens': 50000, 'total_cost': 1.2345, 'total_requests': 42}
        mock_resp = httpx.Response(200, json=mock_data, request=httpx.Request('GET', 'http://test'))
        with patch('persochattai.frontend.router.httpx.AsyncClient') as mock_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            resp = client.get('/report/partials/usage', params={'user_id': 'u-1'})
            assert resp.status_code == 200
            assert '50,000' in resp.text
