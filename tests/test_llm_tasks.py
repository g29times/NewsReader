import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.models.models import Base, Article
from src.models.llm_tasks import summarize_and_extract_keypoints
from src.utils.file_input_handler import FileInputHandler
from datetime import datetime
from src.models.article_crud import create_article, get_article_by_id, get_articles, update_article, delete_article

class TestLLMTasks(unittest.TestCase):
    def setUp(self):
        # Create an in-memory SQLite database
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def test_summarize_and_extract_keypoints(self):
        session = self.Session()

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
        updated_article = summarize_and_extract_keypoints(session, article)

        # Check if the summary and key points are updated
        self.assertIsNotNone(updated_article.summary)
        self.assertIsNotNone(updated_article.key_points)

        session.close()

    def test_get_all_articles(self):
        session = self.Session()
        articles = get_articles(session)
        print(articles)
        session.close()

    def tearDown(self):
        Base.metadata.drop_all(self.engine)

if __name__ == '__main__':
    unittest.main()
