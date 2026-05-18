"""Agent 工具 —— JSON Schema 定义 + Python 实现。

Agent 通过 Function Calling 机制调用这些工具。
每个工具同时提供 JSON Schema（给 LLM）和 Python 函数实现。
"""

import datetime
import json
from typing import Any

from sqlalchemy.orm import Session

from ..storage import repository as repo
from ..search.web_search import search_web, fetch_web_content

# ── JSON Schema 定义 ──

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "searchWeb",
            "description": "（可选）搜索互联网；仅用于需核实时效性外部信息时，每轮推送最多调用1次。常规知识点请直接撰写，勿依赖搜索",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "topK": {"type": "integer", "description": "返回结果数量，默认5", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetchWebContent",
            "description": "（可选）抓取网页正文；仅在 searchWeb 已有可靠 URL 且确需补充细节时使用，勿反复抓取",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "要抓取的网页URL"},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "readUserSettings",
            "description": "读取用户推送设置（推送开关、间隔、时间窗口、模型配置等）",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "readPushHistory",
            "description": "读取最近的推送记录，了解已推送内容避免重复",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "返回条数，默认10", "default": 10},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "readUserFeedback",
            "description": "读取用户对历史推送的反馈记录（好评/不感兴趣/收藏）",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "返回条数，默认20", "default": 20},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "getDomainStats",
            "description": "获取各领域的知识条数和平均评分统计",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "getCurrentTime",
            "description": "获取当前日期时间和星期几",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "listDomains",
            "description": "获取用户自定义的所有知识领域（名称、描述、关键词、是否启用）",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "pushKnowledgeCard",
            "description": "根据领域与用户偏好直接撰写并保存知识卡片（无需网页素材），触发推送通知",
            "parameters": {
                "type": "object",
                "properties": {
                    "domainId": {"type": "integer", "description": "领域ID"},
                    "title": {"type": "string", "description": "卡片标题（≤20字）"},
                    "summary": {"type": "string", "description": "卡片摘要（≤60字）"},
                    "detail": {"type": "string", "description": "学习详情（Markdown格式，3-5段）"},
                    "sourceUrl": {"type": "string", "description": "来源URL"},
                    "sourceTitle": {"type": "string", "description": "来源标题"},
                },
                "required": ["domainId", "title", "summary", "detail"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "skipPush",
            "description": "跳过本次推送；仅用于推送关闭、超出时间窗口等时机/设置问题，不得因搜索无结果而跳过",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string", "description": "跳过原因"},
                },
                "required": ["reason"],
            },
        },
    },
]

# ── 工具执行上下文 ──

class ToolContext:
    """持有数据库 session 和回调，供工具函数使用。"""

    def __init__(self, session: Session, on_push=None, restrict_web_tools: bool = False):
        self.session = session
        self.on_push = on_push  # 推送后的回调，用于通知UI
        self.restrict_web_tools = restrict_web_tools
        self.web_search_count = 0
        self.web_fetch_count = 0


# ── 工具函数实现 ──

def _search_web(ctx: ToolContext, query: str, topK: int = 5) -> str:
    if ctx.restrict_web_tools and ctx.web_search_count >= 1:
        return json.dumps({
            "skipped": True,
            "message": "本轮已达网页搜索上限，请直接撰写知识点并调用 pushKnowledgeCard",
        }, ensure_ascii=False)
    ctx.web_search_count += 1
    results = search_web(query, top_k=topK)
    if not results:
        return json.dumps({
            "results": [],
            "message": "未搜到结果，请基于自身知识撰写卡片，勿再次搜索或 skipPush",
        }, ensure_ascii=False)
    return json.dumps(results, ensure_ascii=False, indent=2)


def _fetch_web_content(ctx: ToolContext, url: str) -> str:
    if ctx.restrict_web_tools and ctx.web_fetch_count >= 1:
        return json.dumps({
            "skipped": True,
            "message": "本轮已达网页抓取上限，请直接撰写知识点并调用 pushKnowledgeCard",
        }, ensure_ascii=False)
    ctx.web_fetch_count += 1
    content = fetch_web_content(url)
    return content[:5000]


def _read_user_settings(ctx: ToolContext) -> str:
    ctx.session.expire_all()
    settings = repo.get_all_settings(ctx.session)
    return json.dumps(settings, ensure_ascii=False, indent=2)


def _read_push_history(ctx: ToolContext, limit: int = 10) -> str:
    ctx.session.expire_all()
    result = repo.get_recent_push_history_with_titles(ctx.session, limit=limit)
    return json.dumps(result, ensure_ascii=False, indent=2)


def _read_user_feedback(ctx: ToolContext, limit: int = 20) -> str:
    ctx.session.expire_all()
    feedback = repo.get_user_feedback(ctx.session, limit=limit)
    return json.dumps(feedback, ensure_ascii=False, indent=2)


def _get_domain_stats(ctx: ToolContext) -> str:
    ctx.session.expire_all()
    stats = repo.get_domain_stats(ctx.session)
    return json.dumps(stats, ensure_ascii=False, indent=2)


def _get_current_time(ctx: ToolContext) -> str:
    now = datetime.datetime.now()
    weekdays = ["一", "二", "三", "四", "五", "六", "日"]
    result = {
        "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
        "weekday": f"星期{weekdays[now.weekday()]}",
        "hour": now.hour,
        "minute": now.minute,
    }
    return json.dumps(result, ensure_ascii=False)


def _list_domains(ctx: ToolContext) -> str:
    ctx.session.expire_all()
    domains = repo.get_all_domains(ctx.session)
    result = [
        {
            "id": d.id,
            "name": d.name,
            "description": d.description,
            "keywords": d.keywords,
            "icon": d.icon,
            "is_enabled": d.is_enabled,
        }
        for d in domains
    ]
    return json.dumps(result, ensure_ascii=False, indent=2)


def _push_knowledge_card(ctx: ToolContext, domainId: int, title: str,
                         summary: str, detail: str, sourceUrl: str = None,
                         sourceTitle: str = None) -> str:
    domain = repo.get_domain_by_id(ctx.session, domainId)
    domain_name = domain.name if domain else "未分类"

    item = repo.create_knowledge_item(
        ctx.session,
        domain_id=domainId,
        domain_name=domain_name,
        title=title,
        summary=summary,
        detail=detail,
        source_url=sourceUrl,
        source_title=sourceTitle,
    )

    if item is None:
        return json.dumps({"status": "duplicate", "message": "内容重复，已跳过"})

    repo.create_push_history(ctx.session, item.id)

    if ctx.on_push:
        ctx.on_push(item)

    return json.dumps({
        "status": "success",
        "message": "知识卡片已生成并推送",
        "item_id": item.id,
    }, ensure_ascii=False)


def _skip_push(ctx: ToolContext, reason: str) -> str:
    return json.dumps({"status": "skipped", "reason": reason}, ensure_ascii=False)


# ── Tool 名称 → 函数映射 ──

TOOL_MAP = {
    "searchWeb": _search_web,
    "fetchWebContent": _fetch_web_content,
    "readUserSettings": _read_user_settings,
    "readPushHistory": _read_push_history,
    "readUserFeedback": _read_user_feedback,
    "getDomainStats": _get_domain_stats,
    "getCurrentTime": _get_current_time,
    "listDomains": _list_domains,
    "pushKnowledgeCard": _push_knowledge_card,
    "skipPush": _skip_push,
}


def execute_tool(ctx: ToolContext, tool_name: str, arguments: dict) -> str:
    """执行指定工具并返回结果字符串。"""
    func = TOOL_MAP.get(tool_name)
    if not func:
        return json.dumps({"error": f"未知工具: {tool_name}"})
    try:
        return func(ctx, **arguments)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
