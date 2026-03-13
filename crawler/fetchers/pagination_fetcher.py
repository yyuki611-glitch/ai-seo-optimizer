import logging
import requests
from bs4 import BeautifulSoup
from typing import List

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = "ai-seo-optimizer/1.0"
MAX_PAGES = 100


def fetch_urls_from_pagination(
    pagination_url_template: str,
    article_url_pattern: str,
    article_list_selector: str,
    timeout: int = 30,
    user_agent: str = DEFAULT_USER_AGENT,
) -> List[str]:
    """
    ページネーションを辿って記事URL一覧を収集する。
    pagination_url_template は {page} プレースホルダーを含むURL。
    記事が見つからないページで終了。
    """
    collected = []
    seen = set()

    for page in range(1, MAX_PAGES + 1):
        page_url = pagination_url_template.format(page=page)
        try:
            resp = requests.get(
                page_url,
                timeout=timeout,
                headers={"User-Agent": user_agent},
            )
            if resp.status_code != 200:
                logger.info(f"ページ取得終了: {page_url} status={resp.status_code}")
                break

            soup = BeautifulSoup(resp.text, "lxml")
            links = soup.select(article_list_selector)
            page_urls = [
                a["href"] for a in links
                if a.get("href") and article_url_pattern in a["href"]
            ]

            if not page_urls:
                logger.info(f"記事URLなし、ページネーション終了: page={page}")
                break

            for url in page_urls:
                if url not in seen:
                    collected.append(url)
                    seen.add(url)

            logger.info(f"ページ {page}: {len(page_urls)}件取得")

        except Exception as e:
            logger.error(f"ページ取得例外: {page_url} / {e}")
            break

    logger.info(f"ページネーション完了: 計{len(collected)}件")
    return collected
