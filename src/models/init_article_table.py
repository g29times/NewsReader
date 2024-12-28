from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from connection import db_session
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.file_input_handler import FileInputHandler
from utils.llms.llm_tasks import LLMTasks
from models.article import Base, Article
from models.article_crud import create_article, get_article_by_id, get_articles, update_article, delete_article

def insert_first_article():
    # Create a SQLite database
    session = db_session

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
    updated_article = LLMTasks.summarize_and_key_topics(session, article)

    # Check if the summary and key points are updated
    self.assertIsNotNone(updated_article.summary)
    self.assertIsNotNone(updated_article.key_topics)

    session.close()

def get_init_articles():
    # Create an in-memory SQLite database
    session = db_session
    articles = get_articles(session,0,1)
    print(articles)
    session.close()

# 表变更，增加了publication_date ，type 字段

if __name__ == '__main__':
    get_init_articles()
    # insert_first_article()