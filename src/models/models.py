from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class Article(Base):
    """
    Database model for storing AI news articles and research papers
    """
    __tablename__ = 'articles'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True) # 必填
    url = Column(String, unique=True) # 可选 可能是文件
    summary = Column(Text) # 重点 由LLM生成
    key_points = Column(Text) # 重点 由LLM生成
    source = Column(String) # 来源 可选
    collection_date = Column(DateTime, default=func.now()) # 收集时间
    publication_date = Column(DateTime, default=func.now()) # 发布时间
    content = Column(Text, nullable=True) # 全文 可选
    authors = Column(String) # 可选
    tags = Column(String) # 人工打标用 可选
    is_research_paper = Column(Boolean, default=False) # 是否为研究论文
    weight = Column(Integer, default=0) # 需要设计
    area = Column(String) # 领域
    topic = Column(String) # 一级 需人工划定大范围 然后让LLM选
    branch = Column(String) # 二级 对应Layer 1 key_points
    persons = Column(String) # 三级 对应Layer 2 key_points
    problem = Column(Text, nullable=True) # 问题

    def __repr__(self):
        # simple
        # return f"<{self.id}. Article {self.title} from {self.url}>"
        # summary
        return f"<{self.id}. Article {self.title}\n summary - {self.summary}\n key_points - {self.key_points}>"
        # content
        # return f"<{self.id}. Article {self.title} - {self.content}>"

class Relation(Base):
    """
    Database model for storing static relationships between articles
    """
    __tablename__ = 'relations'

    id = Column(Integer, primary_key=True, index=True)
    article_id_1 = Column(Integer, ForeignKey('articles.id'))
    article_id_2 = Column(Integer, ForeignKey('articles.id'))
    # same topic - same method, same topic - different method, ...
    relation_type = Column(String)

    # Many-to-Many relationship between articles
    # Each article can have multiple related articles
    # Each related article can have multiple articles pointing to it
    article1 = relationship("Article", foreign_keys=[article_id_1])
    article2 = relationship("Article", foreign_keys=[article_id_2])

    def __repr__(self):
        return f"<{self.id}. Article {self.article1.title} and {self.article2.title} related in: {self.relation_type}>"

class Idea(Base):
    """
    Database model for storing dynamically generated ideas
    """
    __tablename__ = 'ideas'

    id = Column(Integer, primary_key=True, index=True)
    article_ids = Column(String)  # Comma-separated list of article IDs
    generated_idea = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    relevance_score = Column(Integer, default=0)

    def __repr__(self):
        return f"<{self.generated_idea}> from Articles: {self.article_ids}"
