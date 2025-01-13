import logging
import os
import sys
import re
from dataclasses import dataclass, field
from typing import Optional
from sqlalchemy.orm import Session

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.utils.llms.models import LLMResponse
from src.utils.llms.gemini_client import GeminiClient
from src.utils.llms.minimax_client import MinimaxClient
from src.models.article import Article
from src.utils.llms.llm_common_utils import LLMCommonUtils

logger = logging.getLogger(__name__)

class ArticleTasks:
    """处理各种文章相关的任务"""
    
    # 文本总结
    @staticmethod
    def summarize_and_key_topics(content: str) -> LLMResponse:
        """
        使用LLM总结内容并提取关键点
        Args:
            content: 需要处理的文本内容
            
        Returns:
            LLMResponse 包含处理结果
        """
        # minimax = MinimaxClient()
        # response = minimax.query_openai_with_history(question=f"```{content}```", history=[], system_prompt=os.getenv("SUMMARY_PROMPT"))
        # return LLMCommonUtils._extract_summary(response)
        gemini = GeminiClient()
        return gemini.summarize_text(content)

    # 查找文章关系
    @staticmethod
    def find_relations(db: Session, articles: list[Article]):
        """查找文章关系"""
        # TODO: 实现关系查找逻辑
        pass

    # 提取关键点
    @staticmethod
    def extract_key_topics(content: str) -> LLMResponse:
        """提取关键点"""
        # TODO: 实现关键点提取逻辑
        pass

    # 翻译文本
    @staticmethod
    def translate_text(content: str, target_language: str) -> LLMResponse:
        """翻译文本"""
        # TODO: 实现文本翻译逻辑
        pass

if __name__ == '__main__':
    # 测试用例
    result = ArticleTasks.summarize_and_key_topics("2024 年在年初被称为“RAG 发展元年”，虽然这并非共识性的说法，但事实证明，全年的进展无愧于这一称号。在LLM 使用的场景中，RAG 自始至终都在扮演着不可或缺的重要角色。然而，自诞生以来关于 RAG 的争论就没有停止过。由上图可以看到，2023 年 RAG 的称呼并不流行，一种看起来就非常临时的说法“外挂记忆体”、“外挂知识库”是普遍的替代称谓，在当时，主要争论还在于究竟应该用临时的“外挂”还是“永久性的”微调，这个争论在 2024 年初已经终结：从成本和实时性角度，RAG 具有压倒性优势，而效果上相差也并不大，即使需要微调介入的场景，RAG  通常也不可或缺。")
    print(f"标题: {result.body.get('title')}")
    print(f"摘要: {result.body.get('summary')}")
    print(f"关键词: {result.body.get('key_topics')}")
