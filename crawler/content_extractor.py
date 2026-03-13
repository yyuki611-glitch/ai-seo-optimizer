import json
import logging
import re
from bs4 import BeautifulSoup
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


def extract_content(html: str) -> Dict[str, Any]:
    """HTMLからタイトル・本文・見出し・日付を抽出する。取得できない項目はNone。"""
    soup = BeautifulSoup(html, "lxml")
    json_ld = _extract_json_ld(soup)

    return {
        "title": _extract_title(soup, json_ld),
        "body_text": _extract_body_text(soup),
        "heading_structure": _extract_headings(soup),
        "published_at": _extract_published_at(soup, json_ld),
        "updated_at": json_ld.get("dateModified") if json_ld else None,
    }


def _extract_json_ld(soup: BeautifulSoup) -> dict:
    """JSON-LDスクリプトタグからArticle情報を取得する。"""
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "Article" in item.get("@type", ""):
                        return item
            elif isinstance(data, dict) and "Article" in data.get("@type", ""):
                return data
        except (json.JSONDecodeError, AttributeError):
            continue
    return {}


def _extract_title(soup: BeautifulSoup, json_ld: dict) -> Optional[str]:
    tag = soup.find("title")
    return tag.get_text(strip=True) if tag else None


def _extract_body_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()
    article = soup.find("article") or soup.find("main") or soup.body
    if article is None:
        return ""
    text = article.get_text(separator="\n")
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _extract_headings(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    return [
        {"level": int(tag.name[1]), "text": tag.get_text(strip=True)}
        for tag in soup.find_all(["h1", "h2", "h3", "h4"])
    ]


def _extract_published_at(soup: BeautifulSoup, json_ld: dict) -> Optional[str]:
    if json_ld.get("datePublished"):
        return json_ld["datePublished"]
    time_tag = soup.find("time")
    if time_tag:
        return time_tag.get("datetime") or time_tag.get_text(strip=True)
    meta = soup.find("meta", {"property": "article:published_time"})
    if meta:
        return meta.get("content")
    return None
