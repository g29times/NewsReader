from sqlalchemy.orm import Session
from .models import Article
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from llms.gemini_client import GeminiClient
import logging

# Use LLM to summarize and extract key points
def summarize_and_extract_keypoints(db: Session, article: Article):
    if not article:
        return None

    # Process Gemini response
    def extract_text_from_response(response):
        try:
            return response['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError) as e:
            logging.error(f"Error extracting text from response: {e}")
            return ""

    # Use LLM to summarize and extract key points
    client = GeminiClient()
    summary_response = client.generate_content(f"Summarize the following content concisely (with its same language e.g. If the article is in Chinese, then you will answer in Chinese): ```{article.content}```")
    summary = extract_text_from_response(summary_response)
    
    key_points_response = client.generate_content(f"Extract key words (2 layers: Primary Keywords (domain, topic) and Secondary Keywords (specific tech, analysis, method, ...)) from the following content with its same language (only layer and words, no explanation e.g. '**Layer 1: Primary Keywords** Web Applications, User Interface **Layer 2: Secondary Keywords** React, Next.js, JavaScript Library, ...'): ```{article.content}```")
    key_points = extract_text_from_response(key_points_response)

    # Log
    logging.info(f"Summary: {summary}")
    logging.info(f"Key Points: {key_points}")

    # Update the article with summary and key points
    article.summary = summary
    article.key_points = key_points
    db.commit()
    db.refresh(article)

    return article

# Use LLM to find relations between articles base on silimar key-points/ideas/questions/topics/lables
def find_relations(db: Session, article: Article):
    pass

# Use LLM to discover ideas support by relations. This job is not for every new article, but for a period of time.
def discover_ideas(db: Session):
    pass