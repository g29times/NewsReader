from sqlalchemy.orm import Session
from .models import Article

def create_article(db: Session, article_data: dict):
    new_article = Article(**article_data)
    db.add(new_article)
    db.commit()
    db.refresh(new_article)
    return new_article


def get_article_by_id(db: Session, article_id: int):
    return db.query(Article).filter(Article.id == article_id).first()


def get_articles(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Article).offset(skip).limit(limit).all()


def get_all_articles(db: Session):
    return db.query(Article).all()


def update_article(db: Session, article_id: int, update_data: dict):
    article = get_article_by_id(db, article_id)
    if article:
        for key, value in update_data.items():
            setattr(article, key, value)
        db.commit()
        db.refresh(article)
    return article


def delete_article(db: Session, article_id: int):
    article = get_article_by_id(db, article_id)
    if article:
        db.delete(article)
        db.commit()
    return article
