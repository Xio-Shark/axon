"""联网搜索模块 — DuckDuckGo + Jina 网页提取。

两层能力：
1. search(query)     — 搜索引擎获取摘要结果
2. fetch_url(url)    — 抓取网页并转为 Markdown（通过 Jina）
"""

import json
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
    """通过 Jina 将网页转 Markdown，节省 token。"""
    clean = url.removeprefix("https://").removeprefix("http://")
    jina_url = f"{_JINA_PREFIX}{clean}"
    try:
        req = urllib.request.Request(
            jina_url,
            headers={"User-Agent": _USER_AGENT},
        )
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            content = resp.read().decode("utf-8", errors="replace")
        # 截断过长内容
        if len(content) > 4000:
            content = content[:4000] + "\n\n[内容已截断]"
        return content
    except Exception as e:
        logger.warning("Jina 抓取失败: %s，回退 curl", e)
        return _fallback_fetch(url)


def _fallback_fetch(url: str) -> str:
    """直接 urllib 抓取作为兜底。"""
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": _USER_AGENT},
        )
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        if len(raw) > 4000:
            raw = raw[:4000] + "\n\n[内容已截断]"
        return raw
    except Exception as e:
        return f"网页抓取失败: {e}"


def _parse_ddg_html(html: str, max_results: int) -> str:
    """极简 HTML 解析提取 DuckDuckGo 搜索结果。"""
    results = []
    # DuckDuckGo HTML 结果在 class="result__body" 的 div 里
    # 标题在 class="result__a"，摘要在 class="result__snippet"
    parts = html.split('class="result__a"')

    for part in parts[1:max_results + 1]:
        title = _extract_text_between(part, ">", "</a>")
        # 提取 href
        href_start = part.find('href="')
        href = ""
        if href_start != -1:
            href_end = part.find('"', href_start + 6)
            href = part[href_start + 6:href_end]
            # DuckDuckGo 的链接是跳转链接，提取真实 URL
            if "uddg=" in href:
                real = urllib.parse.unquote(
                    href.split("uddg=")[-1].split("&")[0]
                )
                href = real

        snippet = ""
        snip_marker = 'class="result__snippet"'
        snip_pos = part.find(snip_marker)
        if snip_pos != -1:
            snippet = _extract_text_between(
                part[snip_pos:], ">", "</a>"
            )
            if not snippet:
                snippet = _extract_text_between(
                    part[snip_pos:], ">", "</td>"
                )

        if title:
            entry = f"**{title.strip()}**"
            if href:
                entry += f"\n  {href}"
            if snippet:
                entry += f"\n  {snippet.strip()}"
            results.append(entry)

    if not results:
        return "未找到相关搜索结果。"

    return "\n\n".join(results)


def _extract_text_between(text: str, start: str, end: str) -> str:
    """提取两个标记之间的文本，去除 HTML 标签。"""
    s = text.find(start)
    if s == -1:
        return ""
    s += len(start)
    e = text.find(end, s)
    if e == -1:
        return ""
    raw = text[s:e]
    # 简单去除 HTML 标签
    clean = ""
    in_tag = False
    for ch in raw:
        if ch == "<":
            in_tag = True
        elif ch == ">":
            in_tag = False
        elif not in_tag:
            clean += ch
    return clean.strip()
