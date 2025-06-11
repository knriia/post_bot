from datetime import datetime
from typing import Annotated

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


intpk = Annotated[int, mapped_column(primary_key=True, index=True)]
strnull = Annotated[str, mapped_column(nullable=False)]


class QueryUsers(Base):
    __tablename__ = 'query_users'
    id: Mapped[intpk]
    username: Mapped[strnull] = mapped_column(unique=True)
    hashed_password: Mapped[strnull]
    disabled: Mapped[bool | None] = None


class QueryPosts(Base):
    __tablename__ = 'query_posts'

    id: Mapped[intpk]
    title: Mapped[strnull]
    content: Mapped[strnull]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    username: Mapped[str] = mapped_column(ForeignKey(QueryUsers.username, ondelete='CASCADE'))
