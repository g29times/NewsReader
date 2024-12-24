from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from .base import Base
from .user import User  # 添加 User 的导入

class Article(Base):
    """
    Database model for storing AI news articles and research papers
    """
    __tablename__ = 'articles'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True) # 标题 必填
    url = Column(String, unique=True) # 地址 可能是文件
    content = Column(Text, nullable=True) # 原文 全文 可选
    summary = Column(Text) # 概要 由LLM生成
    key_topics = Column(Text) # 重点 由LLM生成
    tags = Column(String) # 人工备注

    source = Column(String) # 原始文档（website, github or paper等） 可选
    collection_date = Column(DateTime, default=func.now()) # 收集时间
    publication_date = Column(String) # 发布时间 粗略
    authors = Column(String) # 作者
    type = Column(String) # 资源类型 （WEB FILE 等）

    # 一对多关系
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="articles")

    # toString方法
    def __repr__(self):
        # simple
        # return f"<{self.id}. Article {self.title} from {self.url}>"
        # summary
        # return f"<{self.id}. Article {self.title}\n summary - {self.summary}\n key_topics - {self.key_topics}>"
        # content
        return f"<{self.id}. Article {self.title} - {self.content}>"
