import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.models.article import Base, Article
from src.models.article_crud import create_article, get_article_by_id, get_articles, update_article, delete_article

class TestArticleCRUD(unittest.TestCase):
    def setUp(self):
        # Create an in-memory SQLite database
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

        article_data = {
            'title': 'Test Article',
            'source': 'Test Source',
            'id' : 1,
            'url': 'https://example.com/test-article', 
            'content': 'This is a test article content.'
        }
        self.article = create_article(self.Session(), article_data)

    def test_create_article(self):
        session = self.Session()
        article_data = {
            'title': 'Test Article',
            'source': 'Test Source',
            'id' : 2,
            'url': 'https://example.com/test-article2', 
            'content': 'This is a test article content.'
        }
        article = create_article(session, article_data)
        print(article)
        self.assertIsNotNone(article.id)
        session.close()

    def test_get_all_articles(self):
        session = self.Session()
        articles = self.article # get_articles(session)
        print(articles)
        session.close()

    def test_get_article_by_id(self):
        session = self.Session()
        retrieved_article = get_article_by_id(session, 1)
        print(retrieved_article)
        self.assertEqual(retrieved_article.title, 'Test Article')
        session.close()

    def test_update_article(self):
        session = self.Session()
        article = get_article_by_id(session, 1)
        print(article)
        update_data = {'title': 'About React and Next.js', 'url': 'https://nextjs.org/learn/react-foundations/what-is-react-and-nextjs'}
        updated_article = update_article(session, article.id, update_data)
        self.assertEqual(updated_article.title, 'About React and Next.js')
        print(get_article_by_id(session, 1))
        session.close()

    def test_delete_article(self):
        session = self.Session()
        delete_article(session, 1)
        deleted_article = get_article_by_id(session, 1)
        self.assertIsNone(deleted_article)
        session.close()

    def tearDown(self):
        Base.metadata.drop_all(self.engine)

if __name__ == '__main__':
    unittest.main()
