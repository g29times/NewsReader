from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

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
