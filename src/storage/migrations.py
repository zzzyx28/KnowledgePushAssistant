"""首次运行自动建表并插入默认数据。"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from .models import Base, KnowledgeDomain
from ..config import DB_PATH
from ..agent.defaults import DEFAULT_DOMAINS


def init_database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
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

    return engine
