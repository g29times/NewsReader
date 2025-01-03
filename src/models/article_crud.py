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
def get_article_by_url(db: Session, article_url: str):
    return db.query(Article).filter(Article.url == article_url).first()

@logy
def get_articles(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Article).offset(skip).limit(limit).all()

@logy
def get_article_by_ids(db: Session, article_ids: list):
    return db.query(Article).filter(Article.id.in_(article_ids)).all()

@logy
def get_all_articles(db: Session):
    return db.query(Article).order_by(Article.id.desc()).all()

@logy
def search_articles(db: Session, query: str):
    return db.query(Article).filter(
        Article.title.contains(query) |
        Article.summary.contains(query) |
        Article.key_topics.contains(query) |
        Article.tags.contains(query)
    ).all()

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
    # update_article(session, 3, {'content': '大模型发展了这么久，AI 智能体们早就开始整顿职场了。打开特工宇宙的教程，不需要太高的技术力，就能去搭建一个智能体，从写文章到按下发送键，都不用亲自动手，AI 打工我躺平。按照这个进度，很快每个同事都能拥有自己的专属智能体了。想象一下，到那个时候：不必要的拉通对齐会，只需要你的 Agent 和老板的 Agent 去开就行了！组织活动不需要挨个去问去催了，让你的 Agent 和所有人的 Agent 对接！采购的买方 Agent 可以自动联系多个卖方 Agent 比价，卖方 Agent 也可以同时支持成千上万个客户 Agent 进行咨询！'})
    print(get_article_by_id(session, 3))
    # delete_article(session, 0) 根据实际
