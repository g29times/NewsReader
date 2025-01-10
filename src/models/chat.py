from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from datetime import datetime
import os
import sys

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)
from src.database.connection import Base, engine

class Chat(Base):
    """聊天记录表"""
    __tablename__ = 'chats'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # 不使用外键 示例：1,2,3
    conversation_id = Column(String(50), nullable=False, unique=True)  # 对话ID 示例：12345678
    title = Column(String(200))
    created_at = Column(DateTime, default=func.datetime('now', 'localtime'),
        server_default=func.datetime('now', 'localtime'))
    updated_at = Column(DateTime, default=func.datetime('now', 'localtime'), 
        onupdate=func.datetime('now', 'localtime'))
    is_active = Column(Boolean, default=True)  # 是否有效
    
    def __repr__(self):
        return f"<Chat {self.conversation_id}>"
