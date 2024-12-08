from sqlalchemy.orm import Session
import os
import sys
import logging
from dataclasses import dataclass

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from llms.gemini_client import GeminiClient
from models.article import Article


@dataclass
class GeminiResponse:
    title: str
    summary: str
    key_points: str


class LLMTasks:
    """
    LLM tasks:
    1. Summarize and extract key points from the content of an article.
    2. Find relations between articles based on similar key-points/ideas/questions/topics/lables.
    3. Discover ideas support by relations. This job is not for every new article, but for a period of time.

    NOTE: These tasks are not automatically triggered by the system, but rather need to be called manually.
    """
    # 特殊方法：针对不同厂商定制
    # Gemini response 返回格式处理
    @staticmethod
    def extract_response_from_genimi(response) -> GeminiResponse:
        """
        从Gemini响应中提取标题、摘要和关键词，通过固定标记提取内容
        """
        try:
            text = response['candidates'][0]['content']['parts'][0]['text']
            
            # 提取标题（在**Title:** 和下一个**之间的内容）
            title = ""
            title_start = text.find("**Title:**")
            if title_start != -1:
                title_end = text.find("**", title_start + 10)  # 10 是 "**Title:**" 的长度
                if title_end != -1:
                    title = text[title_start + 10:title_end].strip()
                    if title.startswith("Title:"):  # 处理可能的重复 "Title:" 前缀
                        title = title.replace("Title:", "", 1).strip()
            if not title:
                title = "ERROR"
                
            # 提取摘要（在**Summarize:** 和下一个**之间的内容）
            summary = ""
            summary_start = text.find("**Summarize:**")
            if summary_start != -1:
                summary_end = text.find("**", summary_start + 14)  # 14 是 "**Summarize:**" 的长度
                if summary_end != -1:
                    summary = text[summary_start + 14:summary_end].strip()
                    
            # 提取关键词（在**Key-Words:** 之后的所有内容）
            key_points = ""
            key_points_start = text.find("**Key-Words:**")
            if key_points_start != -1:
                key_points = text[key_points_start + 14:].strip()
            
            return GeminiResponse(
                title=title,
                summary=summary,
                key_points=key_points
            )
            
        except Exception as e:
            logging.error(f"Error extracting text from response: {e}")
            return GeminiResponse(
                title="ERROR",
                summary="",
                key_points=""
            )

    # 公共方法：通用
    # Use LLM to summarize and extract key points
    @staticmethod
    def summarize_and_keypoints(content: str) -> GeminiResponse:
        """
        使用LLM处理文本内容，提取标题、摘要和关键词
        
        Args:
            content (str): 需要处理的文本内容
            
        Returns:
            GeminiResponse: 包含标题、摘要和关键词的响应对象
        """
        if not content:
            return None
            
        # TODO 2 allow switch LLM
        client = GeminiClient()
        # TODO 3 allow switch prompt
        response = client.chat(f"You have 3 tasks for the following content: 1. Fetch the title from the content, its format should have a title like 'Title: ...' in its first line, if not, you will return 'NO TITLE' for a fallback); 2. Summarize the content concisely and translate into Chinese; 3. Extract Key-Words(only words, no explanation) in a format like '**1. Primary Domains** Web Applications, ...(no more than 5) **2. Specific Topics** React, ...(no more than 10)'. Your response must contain the title, summarize and key words in the fix format: '**Title:** ...\n\n**Summarize:** ...\n\n**Key-Words:** ...' : ```{content}```")
        logging.debug(f"LLM Response: {response}")
        
        return LLMTasks.extract_response_from_genimi(response)

    # Use LLM to find relations between articles base on silimar key-points/ideas/questions/topics/lables
    @staticmethod
    def find_relations(db: Session, article: Article):
        pass

    # Use LLM to discover ideas support by relations. This job is not for every new article, but for a period of time.
    @staticmethod
    def discover_ideas(db: Session):
        pass

if __name__ == '__main__':
    # 测试用例
    test_response = '''{"candidates": [{"content": {"parts": [{"text": "**Title:** Title: 北航、字节和浙大最新发布Prompt Optimization优化框架ERM，让你的提示词优化更高效准确\\n\\n**Summarize:** This article introduces ERM (Example-Guided Reflection Memory mechanism), a new prompt optimization framework developed by researchers from Beihang University, ByteDance, and Zhejiang University.  ERM addresses shortcomings of existing methods by incorporating a feedback memory system and an example factory.  The framework uses a meta-prompt to guide the process, generating detailed solutions and targeted feedback.  Experiments across multiple datasets show significant performance improvements and efficiency gains compared to existing prompt optimization techniques. The article also discusses practical implications for prompt engineers, including better feedback management, optimized example selection, and improved optimization workflows.  Finally, it explores potential applications in AI products and the future scalability of ERM as a continuous learning system.\\n\\n**Key-Words:** **1. Primary Keywords** Prompt Optimization, ERM,  AI模型, 提示词优化, 大语言模型, 反馈记忆, 示例工厂,  强化学习,  启发式搜索\\n\\n**2. Secondary Keywords** 北航, 字节跳动, 浙江大学,  Doubao-pro, GPT4o,  meta-prompt,  Transformer,  LIAR数据集, BBH数据集, WebNLG数据集,  Prompt工程师\\n"}], "role": "model"}, "finishReason": "STOP", "avgLogprobs": -0.15637054162866929}], "usageMetadata": {"promptTokenCount": 5413, "candidatesTokenCount": 272, "totalTokenCount": 5685}, "modelVersion": "gemini-1.5-flash-latest"}'''
    # 先转换为JSON对象
    import json
    response = json.loads(test_response)
    # 测试提取方法
    result = LLMTasks.extract_response_from_genimi(response)
    print("提取结果：")
    print(f"标题: {result.title}")
    print(f"摘要: {result.summary}")
    print(f"关键词: {result.key_points}")