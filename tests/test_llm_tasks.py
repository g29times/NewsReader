import os
import sys
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)

from src.models.article import Base
from src.utils.llms.article_service import ArticleTasks, LLMResponse

class TestArticleTasks(unittest.TestCase):
    """测试LLM任务相关功能"""

    def setUp(self):
        """设置测试环境"""
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def test_summarize_and_key_topics(self):
        """测试文章摘要和关键点提取功能"""
        session = self.Session()

        # 测试用的文本内容
        test_content = """
        Python is a high-level, interpreted programming language. 
        It emphasizes code readability with its notable use of significant whitespace. 
        Python's features include dynamic typing, dynamic binding, and high-level data structures.
        """

        # 调用LLM处理
        response = ArticleTasks.summarize_and_key_topics(test_content)

        # 验证响应格式
        self.assertIsInstance(response, LLMResponse)
        self.assertIsInstance(response.title, str)
        self.assertIsInstance(response.summary, str)
        self.assertIsInstance(response.key_topics, str)

        # 验证响应内容不为空
        self.assertTrue(response.title)
        self.assertTrue(response.summary)
        self.assertTrue(response.key_topics)

        session.close()

    def test_empty_content(self):
        """测试空内容处理"""
        response = ArticleTasks.summarize_and_key_topics("")
        self.assertEqual(response.title, "ERROR")
        self.assertEqual(response.summary, "")
        self.assertEqual(response.key_topics, "")

if __name__ == '__main__':
    unittest.main()
