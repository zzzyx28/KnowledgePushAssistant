"""SQLAlchemy 数据模型。"""

import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, create_engine
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class KnowledgeDomain(Base):
    __tablename__ = "knowledge_domains"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    keywords = Column(Text, default="")
    icon = Column(String(10), default="📚")
    sort_order = Column(Integer, default=0)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    domain_id = Column(Integer, ForeignKey("knowledge_domains.id"), nullable=True)
    domain_name = Column(String(100), default="")
    title = Column(String(200), nullable=False)
    summary = Column(String(500), default="")
    detail = Column(Text, default="")
    source_url = Column(String(1000), nullable=True)
    source_title = Column(String(200), nullable=True)
    trust_score = Column(Float, default=0.5)
    content_hash = Column(String(64), unique=True, nullable=False)
    is_read = Column(Boolean, default=False)
    is_favorited = Column(Boolean, default=False)
    rating = Column(Integer, nullable=True)  # 1=有用, -1=不感兴趣
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class PushHistory(Base):
    __tablename__ = "push_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    knowledge_item_id = Column(Integer, ForeignKey("knowledge_items.id"), nullable=True)
    pushed_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_clicked = Column(Boolean, default=False)


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(200), unique=True, nullable=False)
    value = Column(Text, default="")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False)  # "user" | "assistant"
    content = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class AgentExecutionLog(Base):
    __tablename__ = "agent_execution_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False)
    step_type = Column(String(20), nullable=False)  # thought | action | observation | final | error
    tool_name = Column(String(100), nullable=True)
    tool_input = Column(Text, nullable=True)
    tool_output = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
