"""数据访问层 —— 封装 CRUD 操作。"""

import datetime
import hashlib
import json
from typing import Optional

from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from .models import (
    KnowledgeDomain, KnowledgeItem, PushHistory,
    UserSettings, ChatMessage, AgentExecutionLog
)


# ── 领域 CRUD ──

def get_all_domains(session: Session) -> list[KnowledgeDomain]:
    """获取所有领域（强制刷新，避免 session 缓存导致读到旧数据）。"""
    return (
        session.query(KnowledgeDomain)
        .populate_existing()
        .order_by(KnowledgeDomain.sort_order)
        .all()
    )


def get_enabled_domains(session: Session) -> list[KnowledgeDomain]:
    """获取已启用领域（强制刷新）。"""
    return (
        session.query(KnowledgeDomain)
        .filter(KnowledgeDomain.is_enabled == True)
        .populate_existing()
        .order_by(KnowledgeDomain.sort_order)
        .all()
    )


def get_domain_by_id(session: Session, domain_id: int) -> Optional[KnowledgeDomain]:
    return session.query(KnowledgeDomain).filter(KnowledgeDomain.id == domain_id).first()


def create_domain(session: Session, name: str, description: str = "", keywords: str = "", icon: str = "") -> KnowledgeDomain:
    max_order = session.query(func.max(KnowledgeDomain.sort_order)).scalar() or 0
    domain = KnowledgeDomain(
        name=name, description=description, keywords=keywords,
        icon=icon, sort_order=max_order + 1
    )
    session.add(domain)
    session.commit()
    return domain


def update_domain(session: Session, domain_id: int, **kwargs) -> Optional[KnowledgeDomain]:
    domain = get_domain_by_id(session, domain_id)
    if not domain:
        return None
    for k, v in kwargs.items():
        if hasattr(domain, k):
            setattr(domain, k, v)
    domain.updated_at = datetime.datetime.utcnow()
    session.commit()
    return domain


def delete_domain(session: Session, domain_id: int) -> bool:
    domain = get_domain_by_id(session, domain_id)
    if not domain:
        return False
    session.delete(domain)
    session.commit()
    return True


# ── 知识条目 CRUD ──

def create_knowledge_item(session: Session, domain_id: int, domain_name: str,
                          title: str, summary: str, detail: str,
                          source_url: str = None, source_title: str = None,
                          trust_score: float = 0.5) -> Optional[KnowledgeItem]:
    raw = f"{title}|{summary}|{detail}"
    content_hash = hashlib.sha256(raw.encode()).hexdigest()

    existing = session.query(KnowledgeItem).filter(KnowledgeItem.content_hash == content_hash).first()
    if existing:
        return None

    item = KnowledgeItem(
        domain_id=domain_id,
        domain_name=domain_name,
        title=title,
        summary=summary,
        detail=detail,
        source_url=source_url,
        source_title=source_title,
        trust_score=trust_score,
        content_hash=content_hash,
    )
    session.add(item)
    session.commit()
    return item


def get_knowledge_items(session: Session, domain_id: int = None,
                        keyword: str = None, limit: int = 50, offset: int = 0) -> list[KnowledgeItem]:
    q = session.query(KnowledgeItem)
    if domain_id:
        q = q.filter(KnowledgeItem.domain_id == domain_id)
    if keyword:
        q = q.filter(_knowledge_keyword_filter(keyword))
    return q.order_by(desc(KnowledgeItem.created_at)).offset(offset).limit(limit).all()


def _knowledge_keyword_filter(keyword: str):
    like = f"%{keyword}%"
    return (
        KnowledgeItem.title.like(like)
        | KnowledgeItem.summary.like(like)
        | KnowledgeItem.detail.like(like)
    )


def search_knowledge_items(session: Session, keyword: str, limit: int = 8) -> list[KnowledgeItem]:
    """按关键词检索知识库（标题、摘要、详情）。"""
    if not (keyword or "").strip():
        return get_knowledge_items(session, limit=limit)
    return (
        session.query(KnowledgeItem)
        .filter(_knowledge_keyword_filter(keyword.strip()))
        .order_by(desc(KnowledgeItem.created_at))
        .limit(limit)
        .all()
    )


def get_knowledge_item_by_id(session: Session, item_id: int) -> Optional[KnowledgeItem]:
    return session.query(KnowledgeItem).filter(KnowledgeItem.id == item_id).first()


def update_knowledge_item(session: Session, item_id: int, **kwargs) -> Optional[KnowledgeItem]:
    item = get_knowledge_item_by_id(session, item_id)
    if not item:
        return None
    for k, v in kwargs.items():
        if hasattr(item, k):
            setattr(item, k, v)
    session.commit()
    return item


def delete_knowledge_item(session: Session, item_id: int) -> bool:
    item = get_knowledge_item_by_id(session, item_id)
    if not item:
        return False
    session.delete(item)
    session.commit()
    return True


def get_knowledge_count(session: Session) -> int:
    return session.query(func.count(KnowledgeItem.id)).scalar() or 0


def get_recent_count(session: Session, days: int = 7) -> int:
    since = datetime.datetime.utcnow() - datetime.timedelta(days=days)
    return (
        session.query(func.count(KnowledgeItem.id))
        .filter(KnowledgeItem.created_at >= since)
        .scalar() or 0
    )


# ── 推送历史 ──

def create_push_history(session: Session, item_id: int) -> PushHistory:
    entry = PushHistory(knowledge_item_id=item_id)
    session.add(entry)
    session.commit()
    return entry


def mark_push_clicked(session: Session, item_id: int):
    """标记指定知识条目的最近一次推送为已点击。"""
    entry = (
        session.query(PushHistory)
        .filter(PushHistory.knowledge_item_id == item_id)
        .order_by(desc(PushHistory.pushed_at))
        .first()
    )
    if entry and not entry.is_clicked:
        entry.is_clicked = True
        session.commit()


def get_recent_push_history(session: Session, limit: int = 20) -> list[PushHistory]:
    return (
        session.query(PushHistory)
        .order_by(desc(PushHistory.pushed_at))
        .limit(limit)
        .all()
    )


def get_recent_push_history_with_titles(session: Session, limit: int = 10) -> list[dict]:
    """获取最近推送记录并附带知识条目标题（单次 JOIN 查询，避免 N+1）。"""
    rows = (
        session.query(PushHistory, KnowledgeItem.title, KnowledgeItem.domain_name)
        .outerjoin(KnowledgeItem, PushHistory.knowledge_item_id == KnowledgeItem.id)
        .order_by(desc(PushHistory.pushed_at))
        .limit(limit)
        .all()
    )
    return [
        {
            "id": h.id,
            "pushed_at": h.pushed_at.isoformat() if h.pushed_at else None,
            "title": title or "(已删除)",
            "domain_name": domain_name or "",
            "is_clicked": h.is_clicked,
        }
        for h, title, domain_name in rows
    ]


# ── 用户设置 ──

def get_setting(session: Session, key: str) -> Optional[str]:
    row = session.query(UserSettings).filter(UserSettings.key == key).first()
    return row.value if row else None


def set_setting(session: Session, key: str, value: str):
    row = session.query(UserSettings).filter(UserSettings.key == key).first()
    if row:
        row.value = value
    else:
        row = UserSettings(key=key, value=value)
        session.add(row)
    session.commit()


def get_all_settings(session: Session) -> dict:
    rows = session.query(UserSettings).all()
    result = {}
    for row in rows:
        try:
            result[row.key] = json.loads(row.value)
        except (json.JSONDecodeError, TypeError):
            result[row.key] = row.value
    return result


# ── 对话消息 ──

def save_chat_message(session: Session, session_id: str, role: str, content: str) -> ChatMessage:
    msg = ChatMessage(session_id=session_id, role=role, content=content)
    session.add(msg)
    session.commit()
    return msg


def get_chat_history(session: Session, session_id: str, limit: int = 50) -> list[ChatMessage]:
    return (
        session.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .limit(limit)
        .all()
    )


# ── Agent 执行日志 ──

def save_agent_log(session: Session, session_id: str, step_type: str,
                   tool_name: str = None, tool_input: str = None,
                   tool_output: str = None, content: str = None) -> AgentExecutionLog:
    log = AgentExecutionLog(
        session_id=session_id,
        step_type=step_type,
        tool_name=tool_name,
        tool_input=tool_input,
        tool_output=tool_output,
        content=content,
    )
    session.add(log)
    session.commit()
    return log


# ── 领域统计 (用于 Agent) ──

def get_domain_stats(session: Session) -> list[dict]:
    rows = (
        session.query(
            KnowledgeItem.domain_id,
            KnowledgeItem.domain_name,
            func.count(KnowledgeItem.id).label("count"),
            func.avg(KnowledgeItem.rating).label("avg_rating"),
        )
        .group_by(KnowledgeItem.domain_id, KnowledgeItem.domain_name)
        .all()
    )
    return [
        {"domain_id": r.domain_id, "domain_name": r.domain_name,
         "count": r.count, "avg_rating": round(r.avg_rating or 0, 1)}
        for r in rows
    ]


def get_user_feedback(session: Session, limit: int = 30) -> list[dict]:
    items = (
        session.query(KnowledgeItem)
        .filter(KnowledgeItem.rating != None)
        .order_by(desc(KnowledgeItem.created_at))
        .limit(limit)
        .all()
    )
    return [
        {"domain_name": i.domain_name, "title": i.title,
         "rating": i.rating, "is_favorited": i.is_favorited}
        for i in items
    ]
