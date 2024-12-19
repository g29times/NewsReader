from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, func
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src import logy
from src.models.article import Base, Article
from src.database.connection import db_session

@logy
def create_article(db: Session, article_data: dict):
    new_article = Article(**article_data)
    db.add(new_article)
    db.commit()
    db.refresh(new_article)
    return new_article


@logy
def get_article_by_id(db: Session, article_id: int):
    return db.query(Article).filter(Article.id == article_id).first()


@logy
def get_articles(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Article).offset(skip).limit(limit).all()

@logy
def get_article_by_ids(db: Session, article_ids: list):
    return db.query(Article).filter(Article.id.in_(article_ids)).all()

@logy
def get_all_articles(db: Session):
    return db.query(Article).all()


@logy
def update_article(db: Session, article_id: int, update_data: dict):
    article = get_article_by_id(db, article_id)
    if article:
        for key, value in update_data.items():
            setattr(article, key, value)
        db.commit()
        db.refresh(article)
    return article


@logy
def delete_article(db: Session, article_id: int):
    article = get_article_by_id(db, article_id)
    if article:
        db.delete(article)
        db.commit()
    return article


if __name__ == '__main__':
    session = db_session
    print(get_article_by_id(session, 3))
    # delete_article(session, 0) 根据实际