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
        try:
            text = response['candidates'][0]['content']['parts'][0]['text']
            
            # 使用分隔标记拆分响应的不同部分
            parts = text.split('\n\n')
            
            # 提取标题
            title = ""
            for part in parts:
                if part.startswith("**Title:**"):
                    title = part.replace("**Title:**", "").strip()
                    if title.startswith("Title:"):  # 处理可能的重复 "Title:" 前缀
                        title = title.replace("Title:", "", 1).strip()
                    break
            if not title:
                title = "EMPTY TITLE"
                
            # 提取摘要
            summary = ""
            for part in parts:
                if part.startswith("**Summarize:**"):
                    summary = part.replace("**Summarize:**", "").strip()
                    break
                    
            # 提取关键词
            key_points = ""
            for part in parts:
                if part.startswith("**Key-Words:**"):
                    key_points = part.strip()
                    break
            
            return GeminiResponse(
                title=title,
                summary=summary,
                key_points=key_points
            )
            
        except (KeyError, IndexError) as e:
            logging.error(f"Error extracting text from response: {e}")
            return GeminiResponse(
                title="ERROR",
                summary="",
                key_points=""
            )
    
    # 公共方法：通用
    # Use LLM to summarize and extract key points
    @staticmethod
    def summarize_and_keypoints(db: Session, article: Article):
        if not article:
            return None
        # TODO 2 allow switch LLM
        client = GeminiClient()
        # TODO 3 chat once
        response = client.chat(f"You have 3 tasks for the following content: 1. Fetch the title from the content, its format should have a title like 'Title: ...' in its first line, if not, you will return 'EMTPY TITLE' for a fallback); 2. Summarize the content concisely with its same language; 3. Extract Key-Words(only words, no explanation) in a format like '**1. Primary Keywords** Web Applications, ... **2. Secondary Keywords** React, ...', you should response Title, Summarize and Key-Words in deperate parts: ```{article.content}```")
        logging.info(f": {response}")
        
        response_data = LLMTasks.extract_response_from_genimi(response)
        title = response_data.title
        summary = response_data.summary
        key_points = response_data.key_points
        logging.info(f"Title: {title}")
        logging.info(f"Summary: {summary}")
        logging.info(f"Key Points: {key_points}")

        # Update the article with summary and key points
        article.title = title
        article.summary = summary
        article.key_points = key_points
        db.commit()
        db.refresh(article)
        return article

    # Use LLM to find relations between articles base on silimar key-points/ideas/questions/topics/lables
    @staticmethod
    def find_relations(db: Session, article: Article):
        pass

    # Use LLM to discover ideas support by relations. This job is not for every new article, but for a period of time.
    @staticmethod
    def discover_ideas(db: Session):
        pass