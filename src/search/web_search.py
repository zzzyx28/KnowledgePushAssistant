"""DuckDuckGo 搜索 + 网页内容抓取。"""

import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS


def search_web(query: str, top_k: int = 5) -> list[dict]:
    """搜索互联网，返回标题、摘要、URL 列表。"""
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=top_k):
                results.append({
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "url": r.get("href", ""),
                })
    except Exception:
        pass
    return results


def fetch_web_content(url: str, timeout: int = 10) -> str:
    """抓取指定 URL 的网页正文。"""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines[:200])
    except Exception as e:
        return f"[抓取失败] {str(e)}"
