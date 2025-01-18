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
    vector_ids = Column(String, nullable=True)  # 存储逗号分隔的向量ID列表
    title = Column(String, index=True, unique=True) # 标题 必填 唯一
    url = Column(String) # 地址 可以为空 因此不唯一（多个空）
    content = Column(Text, nullable=False) # 原文 必填 TEXT类型 较长
    summary = Column(Text, index=True) # 概要 由LLM生成
    key_topics = Column(String, index=True) # 重点 由LLM生成
    tags = Column(String, index=True) # 人工备注

    source = Column(String) # 原始文档（website, github or paper等） 可选
    collection_date = Column(DateTime, default=func.datetime('now', 'localtime')) # 收集文章的时间
    publication_date = Column(String) # 粗略文章发布时间 由LLM生成 格式可能不统一 因此不使用DateTime
    authors = Column(String) # 作者
    type = Column(String) # 资源类型 （WEB FILE NOTE）

    # 一对多关系
    user_id = Column(Integer, nullable=False) # 不使用外键 示例：1,2,3
    # user = relationship("User", back_populates="articles")

    # toString方法
    def __repr__(self):
        # simple
        # return f"<{self.id}. Article {self.title} from {self.url}>"
        # summary
        # return f"<{self.id}. Article {self.title}\n summary - {self.summary}\n key_topics - {self.key_topics}>"
        # content
        return f"<{self.id}. Article {self.title} - {self.content}>"
