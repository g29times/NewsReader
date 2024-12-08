from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.file_input_handler import FileInputHandler
from llms.llm_tasks import LLMTasks
from models.article import Base, Article
from models.article_crud import create_article, get_article_by_id, get_articles, update_article, delete_article

def insert_first_article():
    # Create an in-memory SQLite database
    engine = create_engine('sqlite:///articles.db')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Fetch content from a URL
    url = 'https://nextjs.org/learn/react-foundations/what-is-react-and-nextjs'
    content = FileInputHandler.jina_read_from_url(url)

    # Add a sample article
    article = Article(title='About React and Next.js', content=content, url=url, source='Official', 
        collection_date=datetime.now()
    )
    session.add(article)
    session.commit()

    # Run the summarization task
    updated_article = LLMTasks.summarize_and_keypoints(session, article)

    # Check if the summary and key points are updated
    self.assertIsNotNone(updated_article.summary)
    self.assertIsNotNone(updated_article.key_points)

    session.close()

def get_init_articles():
    # Create an in-memory SQLite database
    engine = create_engine('sqlite:///articles.db')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    articles = get_articles(session)
    print(articles)
    session.close()

if __name__ == '__main__':
    # insert_first_article()
    get_init_articles()