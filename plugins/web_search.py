"""联网搜索模块 — DuckDuckGo 搜索 + Jina 网页转 Markdown。"""

import logging
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://html.duckduckgo.com/html/"
_JINA_PREFIX = "https://r.jina.ai/"
_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
_TIMEOUT = 15
_MAX_CONTENT_LEN = 4000


def _truncate(text: str) -> str:
    if len(text) <= _MAX_CONTENT_LEN:
        return text
    return text[:_MAX_CONTENT_LEN] + "\n\n[内容已截断]"


def _http_get(url: str) -> str:
    """通用 HTTP GET，返回文本内容。"""
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="replace")


def search(query: str, max_results: int = 5) -> str:
    """DuckDuckGo HTML 搜索，返回格式化摘要。"""
    try:
        data = urllib.parse.urlencode({"q": query}).encode()
        req = urllib.request.Request(
            _SEARCH_URL, data=data, method="POST",
            headers={"User-Agent": _USER_AGENT},
        )
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        return _parse_ddg_html(html, max_results)
    except Exception as e:
        logger.warning("搜索失败: %s", e)
        return f"搜索失败: {e}"


def fetch_url(url: str) -> str:
    """通过 Jina 将网页转 Markdown；失败则直接抓取。"""
    clean = url.removeprefix("https://").removeprefix("http://")
    try:
        return _truncate(_http_get(f"{_JINA_PREFIX}{clean}"))
    except Exception as e:
        logger.warning("Jina 抓取失败: %s，回退直接请求", e)

    try:
        return _truncate(_http_get(url))
    except Exception as e:
        return f"网页抓取失败: {e}"


# ── DuckDuckGo HTML 解析 ──

def _parse_ddg_html(html: str, max_results: int) -> str:
    results = []
    parts = html.split('class="result__a"')

    for part in parts[1:max_results + 1]:
        title = _extract_text(part, ">", "</a>")
        href = _extract_href(part)
        snippet = _extract_snippet(part)

        if title:
            entry = f"**{title.strip()}**"
            if href:
                entry += f"\n  {href}"
            if snippet:
                entry += f"\n  {snippet.strip()}"
            results.append(entry)

    return "\n\n".join(results) if results else "未找到相关搜索结果。"


def _extract_href(part: str) -> str:
    start = part.find('href="')
    if start == -1:
        return ""
    end = part.find('"', start + 6)
    href = part[start + 6:end]
    if "uddg=" in href:
        href = urllib.parse.unquote(href.split("uddg=")[-1].split("&")[0])
    return href


def _extract_snippet(part: str) -> str:
    marker = 'class="result__snippet"'
    pos = part.find(marker)
    if pos == -1:
        return ""
    sub = part[pos:]
    return _extract_text(sub, ">", "</a>") or _extract_text(sub, ">", "</td>")


def _extract_text(text: str, start: str, end: str) -> str:
    """提取两个标记之间的文本，去除 HTML 标签。"""
    s = text.find(start)
    if s == -1:
        return ""
    s += len(start)
    e = text.find(end, s)
    if e == -1:
        return ""
    raw = text[s:e]
    result = []
    in_tag = False
    for ch in raw:
        if ch == "<":
            in_tag = True
        elif ch == ">":
            in_tag = False
        elif not in_tag:
            result.append(ch)
    return "".join(result).strip()
