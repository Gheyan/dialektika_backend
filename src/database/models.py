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

class Task(Base):
    __tablename__ = "Task"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    description: Mapped[str] = mapped_column(nullable=True)
    priority: Mapped[str]
    status: Mapped[str]
    postDate: Mapped[datetime.datetime]
    deadlineDate: Mapped[datetime.datetime]
    completionDate: Mapped[datetime.datetime] = mapped_column(nullable=True)

    assignees: Mapped[List["TaskAssignee"]] = relationship(
        back_populates="task", cascade="all, delete-orphan", passive_deletes=True
    )
    attachments: Mapped[List["TaskAttachment"]] = relationship(
        back_populates="task", cascade="all, delete-orphan", passive_deletes=True
    )

class User(Base):
    __tablename__ = "User"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]
    email: Mapped[str]
    hash: Mapped[str]
    role: Mapped[str]
    is_deleted: Mapped[bool] = mapped_column(nullable=True, server_default="False")


    tasks: Mapped[List["TaskAssignee"]] = relationship(back_populates="user", passive_deletes=True)

class TaskAssignee(Base):
    __tablename__ = "TaskAssignee"
    id: Mapped[int] = mapped_column(primary_key=True)
    taskID: Mapped[int] = mapped_column(ForeignKey("Task.id", ondelete="CASCADE"))
    assigneeID: Mapped[int] = mapped_column(ForeignKey("User.id", ondelete="CASCADE"))

    task: Mapped["Task"] = relationship(back_populates="assignees")
    user: Mapped["User"] = relationship(back_populates="tasks")

    comments: Mapped[List["Comment"]] = relationship(back_populates="taskAssignee")


class Comment(Base):
    __tablename__ = "Comment"
    id: Mapped[int] = mapped_column(primary_key=True)
    taskAssigneeID: Mapped[int] =  mapped_column(ForeignKey("TaskAssignee.id", ondelete="CASCADE"))
    replyerID: Mapped[int] = mapped_column(ForeignKey("User.id", ondelete="CASCADE"), nullable=True)
    date: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    reply: Mapped[str] = mapped_column(nullable=True)
    comment: Mapped[str] = mapped_column(nullable=True)

    taskAssignee: Mapped["TaskAssignee"] = relationship(back_populates="comments")
    replyer: Mapped["User"] = relationship()


class TaskAttachment(Base):
    __tablename__ = "TaskAttachment"
    id: Mapped[int] = mapped_column(primary_key=True)
    taskID: Mapped[int] = mapped_column(ForeignKey("Task.id", ondelete="CASCADE"))
    fileURL: Mapped[str] = mapped_column(nullable=True)

    task: Mapped["Task"] = relationship(back_populates="attachments")


class Log(Base):
    __tablename__ = "Log"
    id: Mapped[int] = mapped_column(primary_key=True)
    taskID: Mapped[int] = mapped_column(ForeignKey("Task.id", ondelete="SET NULL"), nullable=True)
    current_userID: Mapped[int] = mapped_column(ForeignKey("User.id", ondelete="SET NULL"), nullable=True)
    affected_userID: Mapped[int] = mapped_column(ForeignKey("User.id", ondelete="SET NULL"), nullable=True)
    username: Mapped[str] = mapped_column(nullable=True)
    date: Mapped[datetime.datetime] = mapped_column(nullable=True, server_default=func.now())
    type: Mapped[str]
    viewed: Mapped[bool] = mapped_column(default=False)