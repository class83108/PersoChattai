"""All Ears English 爬蟲 adapter。"""

from __future__ import annotations

import logging

import httpx
from bs4 import BeautifulSoup

from persochattai.content.scraper.protocol import ArticleMeta, RawArticle, ScraperError

logger = logging.getLogger(__name__)

_BASE_URL = 'https://www.allearsenglish.com'
_LIST_PATH = '/category/business-english/'


class AllEarsEnglishScraper:
    source_type: str = 'podcast_allearsenglish'

    async def fetch_article_list(self) -> list[ArticleMeta]:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(f'{_BASE_URL}{_LIST_PATH}')
                resp.raise_for_status()
        except httpx.HTTPStatusError:
            logger.warning('AllEarsEnglish: HTTP 錯誤，無法取得文章列表')
            return []
        except httpx.RequestError:
            logger.warning('AllEarsEnglish: 連線失敗，無法取得文章列表')
            return []

        return self._parse_article_list(resp.text)

    def _parse_article_list(self, html: str) -> list[ArticleMeta]:
        soup = BeautifulSoup(html, 'html.parser')
        articles: list[ArticleMeta] = []

        for article in soup.find_all('article'):
            h2 = article.find('h2')
            if not h2:
                continue
            link = h2.find('a')
            if not link or not link.get('href'):
                continue
            articles.append(
                ArticleMeta(
                    url=str(link['href']),
                    title=link.get_text(strip=True),
                )
            )

        if not articles and soup.find('body'):
            logger.warning(
                'AllEarsEnglish: 解析失敗 — 找不到 article > h2 > a 結構，HTML 結構可能已變更'
            )

        return articles

    async def fetch_article_content(self, url: str) -> RawArticle:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.warning('AllEarsEnglish: 無法取得文章內容 %s: %s', url, e)
            raise ScraperError(f'Failed to fetch {url}') from e

        return self._parse_article_content(resp.text, url)

    def _parse_article_content(self, html: str, url: str) -> RawArticle:
        soup = BeautifulSoup(html, 'html.parser')

        title_el = soup.find('h1', class_='entry-title')
        title = title_el.get_text(strip=True) if title_el else ''

        content_el = soup.find('div', class_='entry-content')
        content = ''
        if content_el:
            paragraphs = content_el.find_all('p')
            content = '\n'.join(p.get_text(strip=True) for p in paragraphs)

        return RawArticle(url=url, title=title, content=content)
