"""首次运行自动建表并插入默认数据。"""

import json

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from .models import Base, KnowledgeDomain, UserSettings
from ..config import DB_PATH, DEFAULT_SETTINGS
from ..agent.defaults import DEFAULT_DOMAINS


def init_database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        f"sqlite:///{DB_PATH}",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    # 启用 WAL 模式以支持更好的并发读写
    from sqlalchemy import event
    @event.listens_for(engine, "connect")
    def _set_wal(dbapi_conn, connection_record):
        dbapi_conn.execute("PRAGMA journal_mode=WAL")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        from .models import KnowledgeDomain
        existing_count = session.query(KnowledgeDomain).count()
        if existing_count == 0:
            for i, d in enumerate(DEFAULT_DOMAINS):
                domain = KnowledgeDomain(
                    name=d["name"],
                    description=d["description"],
                    keywords=d["keywords"],
                    icon=d["icon"],
                    sort_order=i,
                    is_enabled=True,
                )
                session.add(domain)
            session.commit()

        if session.query(UserSettings).count() == 0:
            for key, value in DEFAULT_SETTINGS.items():
                if key.startswith("window_"):
                    continue
                session.add(
                    UserSettings(
                        key=key,
                        value=json.dumps(value, ensure_ascii=False),
                    )
                )
            session.commit()

    return engine
