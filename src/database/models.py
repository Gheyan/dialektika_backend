from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
import datetime
from typing import List
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy import func
from decimal import Decimal
from sqlalchemy import Numeric, String


class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "User"
    id: Mapped[int] = mapped_column(primary_key=True)
    firstname: Mapped[str]
    lastname: Mapped[str]
    username: Mapped[str]
    email: Mapped[str]
    hash: Mapped[str]
    role: Mapped[str]
    is_deleted: Mapped[bool] = mapped_column(nullable=True, server_default="False")

class Post(Base):
    __tablename__ = "Post"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("User.id", ondelete="CASCADE"))
    title: Mapped[str]
    description: Mapped[str] = mapped_column(nullable=True)
    attachment: Mapped[str] = mapped_column(nullable=True)

class Comments(Base):
    __tablename__ = "Comments"
    post_id: Mapped[int] = mapped_column(ForeignKey("Post.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("User.id", ondelete="CASCADE"), primary_key=True)
    comment: Mapped[str]
    date_created: Mapped[str]


    
