from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, func
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src import logy
from src.models.chat import Base, Chat
from src.database.connection import db_session
from typing import List, Optional
from datetime import datetime

# 管理员用 返回用户的所有聊天 无限制
@logy
def get_user_all_chats(db: Session, user_id: int):
    return db.query(Chat).filter(Chat.user_id == user_id).all()

# 按聊天名称 搜索用户的有效的聊天记录
@logy
def search_chats(db: Session, user_id: int, query: str):
    return db.query(Chat).filter(
        Chat.user_id == user_id,
        Chat.is_active == True,
        Chat.title.contains(query)
    ).all()

# 创建新的聊天记录
@logy
def create_chat(db: Session, user_id: int, conversation_id: str, title: Optional[str] = None) -> Chat:
    chat = Chat(
        user_id=user_id,
        conversation_id=conversation_id,
        title=title
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat

# 重点 获取用户的所有有效的聊天记录 按编辑时间倒排
@logy
def get_user_chats(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Chat]:
    return db.query(Chat).filter(
        Chat.user_id == user_id,
        Chat.is_active == True
    ).order_by(Chat.updated_at.desc()).offset(skip).limit(limit).all()

# 重点 通过ID获取聊天记录
@logy
def get_chat(db: Session, chat_id: int) -> Optional[Chat]:
    return db.query(Chat).filter(Chat.id == chat_id).first()

# 重点 更新聊天记录
@logy
def update_chat(db: Session, chat_id: int, **kwargs) -> Optional[Chat]:
    chat = get_chat(db, chat_id)
    if not chat:
        return None
    for key, value in kwargs.items():
        setattr(chat, key, value)
    db.commit()
    db.refresh(chat)
    return chat

# 删除聊天记录（软删除）
@logy
def delete_chat(db: Session, chat_id: int) -> bool:
    chat = get_chat(db, chat_id)
    if not chat:
        return False
    chat.is_active = False
    db.commit()
    return True
