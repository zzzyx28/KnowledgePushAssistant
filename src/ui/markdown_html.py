"""将 Markdown 转为 QTextBrowser 可用的 HTML（Apple 排版）。"""

import markdown

from .styles import FONT_FAMILY, FONT_MONO

_DETAIL_CSS = """
body {
    font-family: __FONT_FAMILY__;
    font-size: 15px;
    line-height: 1.65;
    color: #1D1D1F;
    margin: 0;
}
h1, h2, h3 {
    color: #1D1D1F;
    margin: 1.2em 0 0.45em;
    font-weight: 600;
    letter-spacing: -0.3px;
}
h1 { font-size: 1.4em; }
h2 { font-size: 1.2em; }
h3 { font-size: 1.05em; }
p { margin: 0.55em 0; }
code {
    background: #F2F2F7;
    padding: 2px 7px;
    border-radius: 5px;
    font-size: 13px;
    font-family: __FONT_MONO__;
}
pre {
    background: #F2F2F7;
    padding: 14px 16px;
    border-radius: 10px;
    overflow-x: auto;
    border: 1px solid #E8E8ED;
}
pre code { background: none; padding: 0; }
blockquote {
    border-left: 3px solid #007AFF;
    margin: 0.9em 0;
    padding: 0 0 0 16px;
    color: #6E6E73;
}
a { color: #007AFF; text-decoration: none; }
a:hover { text-decoration: underline; }
ul, ol { padding-left: 1.35em; margin: 0.45em 0; }
li { margin: 0.3em 0; }
table { border-collapse: collapse; width: 100%; margin: 0.9em 0; }
th, td {
    border: 1px solid #E8E8ED;
    padding: 10px 12px;
    text-align: left;
}
th { background: #F9F9FB; font-weight: 600; }
hr { border: none; border-top: 1px solid #E8E8ED; margin: 1.4em 0; }
img { max-width: 100%; border-radius: 8px; }
""".replace("__FONT_FAMILY__", FONT_FAMILY).replace("__FONT_MONO__", FONT_MONO)


def render_markdown_to_html(text: str | None) -> str:
    """把 Markdown 正文渲染为带样式的 HTML。"""
    if not (text or "").strip():
        body = "<p style='color:#AEAEB2;'>暂无详细内容</p>"
    else:
        body = markdown.markdown(
            text,
            extensions=["fenced_code", "tables", "nl2br", "sane_lists"],
        )
    return f"<html><head><style>{_DETAIL_CSS}</style></head><body>{body}</body></html>"
