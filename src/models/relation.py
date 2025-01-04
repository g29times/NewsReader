from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class Relation(Base):
    """
    Database model for storing static relationships between articles
    """
    __tablename__ = 'relations'

    id = Column(Integer, primary_key=True, index=True)
    article_id_1 = Column(Integer)
    article_id_2 = Column(Integer)
    # same topic - same method, same topic - different method, ...
    relation_type = Column(String)

    # Many-to-Many relationship between articles
    # Each article can have multiple related articles
    # Each related article can have multiple articles pointing to it
    article1 = relationship("Article", foreign_keys=[article_id_1])
    article2 = relationship("Article", foreign_keys=[article_id_2])

    def __repr__(self):
        return f"<{self.id}. Article {self.article1.title} and {self.article2.title} related in: {self.relation_type}>"
