"""
RAG service for handling multi-document conversations
"""
from math import log
import os
import logging
from typing import List, Optional
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.voyageai import VoyageEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import Document, VectorStoreIndex, ServiceContext, StorageContext
import chromadb

from src.models.article import Article
from src.models.article_crud import get_article_by_ids
from src.database.connection import db_session

logger = logging.getLogger(__name__)

class RAGService:
    """RAG service for handling document-based conversations"""
    
    def __init__(self):
        """Initialize RAG service"""
        # Load API keys
        self.voyage_api_key = os.getenv("VOYAGE_API_KEY")
        self.google_api_key = os.getenv("GEMINI_API_KEY1")
        
        if not self.voyage_api_key or not self.google_api_key:
            raise ValueError("Missing required API keys")
            
        # Initialize embedding model
        self.embed_model = VoyageEmbedding(
            model_name="voyage-3",
            voyage_api_key=self.voyage_api_key
        )
        
        # Initialize LLM
        self.llm = Gemini(
            model="models/gemini-1.5-flash-latest",
            api_key=self.google_api_key,
            temperature=0.7,
            max_tokens=2048
        )
        
        # Create service context - Deprecated
        # self.service_context = ServiceContext.from_defaults(
        #     llm=self.llm,
        #     embed_model=self.embed_model
        # )
        
        # Initialize Chroma client
        self.chroma_client = chromadb.PersistentClient(path="src/database/chroma_db")
        
        # Current collection name
        self.current_collection_name = None

    def _articles_to_documents(self, articles: List[Article]) -> List[Document]:
        """Convert articles to LlamaIndex documents
        
        Args:
            articles: List of Article objects
            
        Returns:
            List of Document objects
        """
        documents = []
        # TODO content, key_points
        for article in articles:
            text = f"标题: {article.title}\n"
            # if article.summary:
            #     text += f"摘要: {article.summary}\n"
            # if article.tags:
            #     text += f"标签: {article.tags}\n"
            # if article.key_points:
            #     topics = article.key_points.split(',') if article.key_points else []
            if article.content:
                text += f"内容: {article.content}\n"

            metadata = {
                "id": article.id,
                # "title": article.title,
                "url": article.url,
                "summary": article.summary,
                "key_points": article.key_points,
                "tags": article.tags
            }
            
            doc = Document(text=text, metadata=metadata)
            documents.append(doc)
            
        return documents
    
    # 直接聊天
    def chat_single(self, query: str) -> str:
        """Chat with context"""
        API_KEY = os.getenv("GEMINI_API_KEY1")
        MODEL = "gemini-1.5-flash-latest"

        llm = Gemini(model="models/" + MODEL, api_key=API_KEY)
        resp = llm.complete(query)
        logger.info(f"LLM response: {resp}")
        return resp

    # 一级 - 短期记忆（对话窗口）
    def chat_with_histroy(self, history: str) -> str:
        """Chat with context"""
        pass

    # 二级 - 长期记忆（笔记区）
    def chat_with_memmory(self, memory: str) -> str:
        """Chat with context"""
        pass

    # 三级 - 知识库（资料）
    def chat_with_articles(self, article_ids: List[int], query: str) -> str:
        """Chat with selected articles
        
        Args:
            article_ids: List of article IDs
            query: User query
            
        Returns:
            Response from LLM
        """
        try:
            logger.info(f"Chatting with articles: {article_ids}")
            # Get articles from database
            articles = get_article_by_ids(db_session, article_ids)
            if not articles:
                logger.info("No articles found")
                return "未找到相关文章"
            
            logger.info(f"Got {len(articles)} articles")
            # Convert to documents
            documents = self._articles_to_documents(articles)
            logger.info(f"Got {len(documents)} documents")
            
            # Create collection for these documents
            import time
            self.current_collection_name = f"chat_{int(time.time())}"
            collection = self.chroma_client.get_or_create_collection(self.current_collection_name)
            logger.info(f"Got collection: {self.current_collection_name}")
            
            # Create vector store and storage context
            vector_store = ChromaVectorStore(chroma_collection=collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            
            # Create index with storage context
            index = VectorStoreIndex.from_documents(
                documents,
                storage_context=storage_context,
                # service_context=self.service_context,
                show_progress=True,
                embed_model=self.embed_model
            )
            
            # Create query engine with Chinese system prompt
            system_prompt = """你是一个专业的AI助手，负责帮助用户理解和分析文档内容。
            请基于检索到的相关文档回答用户的问题。
            如果文档中没有相关信息，请明确告知用户。
            回答应该：
            1. 准确且基于事实
            2. 清晰且结构化
            3. 适当引用来源
            4. 使用中文回答
            """
            
            query_engine = index.as_query_engine(
                llm=self.llm,
                # service_context=self.service_context,
                # system_prompt=system_prompt,
                streaming=True
            )
            
            # Get response
            response = query_engine.query(query)
            logger.info(f"LLM response: {response}")
            
            # Format response with sources
            response_text = str(response)
            if response.source_nodes:
                response_text += "\n\n参考来源:\n"
                for node in response.source_nodes:
                    if "title" in node.metadata:
                        response_text += f"- {node.metadata['title']}\n"
                        
            return response_text
            
        except Exception as e:
            logger.error(f"Error in chat_with_articles: {e}")
            return f"处理请求时发生错误: {str(e)}"
    
    def cleanup_collection(self, article_ids: List[int]):
        """Clean up temporary collection
        
        Args:
            article_ids: List of article IDs
        """
        try:
            if not self.current_collection_name:
                return
                
            self.chroma_client.delete_collection(self.current_collection_name)
            logger.info(f"Deleted collection: {self.current_collection_name}")
            self.current_collection_name = None
            
        except Exception as e:
            logger.error(f"Error cleaning up collection: {e}")
