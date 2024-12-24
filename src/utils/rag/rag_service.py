"""
RAG service for handling multi-document conversations
"""
from math import log
import os
import logging
from typing import List, Optional
from llama_index.core import Settings
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.voyageai import VoyageEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import Document, VectorStoreIndex, ServiceContext, StorageContext
import chromadb
from llama_index.core.storage.chat_store import SimpleChatStore
from llama_index.core.memory import ChatMemoryBuffer

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
        self.google_api_key = os.getenv("GEMINI_API_KEY")
        self.GEMINI_MODEL = os.getenv("GEMINI_MODEL")
        
        if not self.voyage_api_key or not self.google_api_key:
            raise ValueError("Missing required API keys")
            
        # Initialize embedding model
        self.voyage = VoyageEmbedding(
            model_name = "voyage-3",
            voyage_api_key = self.voyage_api_key
        )
        
        # Initialize LLM
        self.genimi = Gemini(
            system_prompt=os.getenv("SYSTEM_PROMPT"),
            model="models/" + self.GEMINI_MODEL,
            api_key=self.google_api_key,
            temperature=1,
            max_tokens=8192
        )
        
        # Create service context - Deprecated Use Settings instead
        # self.service_context = ServiceContext.from_defaults(
        #     llm=self.llm,
        #     embed_model=self.embed_model
        # )
        # Global 默认值
        Settings.llm = self.genimi
        Settings.embed_model = self.voyage
        # Settings.context_window=8192
        # Settings.text_splitter = SentenceSplitter(chunk_size=1024)
        # Settings.chunk_size = 512
        # Settings.chunk_overlap = 20
        # Callbacks https://docs.llamaindex.ai/en/stable/module_guides/supporting_modules/settings/
        
        # Initialize Chroma client
        self.chroma_client = chromadb.PersistentClient(path="src/database/chroma_db")
        
        # Current collection name
        self.current_collection_name = "rag_collection"

        # Initialize ChatStore and ChatMemoryBuffer
        loaded_chat_store = SimpleChatStore.from_persist_path(
            persist_path="chat_store.json"
        )
        self.chat_store = loaded_chat_store if loaded_chat_store else SimpleChatStore()
        self.chat_memory = ChatMemoryBuffer.from_defaults(
            token_limit=10000, # shape 相似
            chat_store=self.chat_store,
            chat_store_key="user1",
        )

    def _articles_to_documents(self, articles: List[Article]) -> List[Document]:
        """Convert articles to LlamaIndex documents
        
        Args:
            articles: List of Article objects
            
        Returns:
            List of Document objects
        """
        documents = []
        for article in articles:
            # 主体由标题和内容构成
            text = f"标题: {article.title}\n"
            if article.content:
                text += f"内容: {article.content}\n"
            # 其他元数据
            metadata = {
                "id": article.id,
                "url": article.url, # 用于“参考来源”
                "summary": article.summary, # 摘要
                "key_topics": article.key_topics,
                "tags": article.tags # 标签
            }
            
            doc = Document(text=text, metadata=metadata)
            documents.append(doc)
            
        return documents
    
    # 直接聊天
    # 一级 - 短期记忆（对话窗口）
    # 二级 - 长期记忆（笔记区）
    def chat(self, query: str) -> str:
        """Chat with context"""
        # resp = self.genimi.complete(query)
        # logger.info(f"LLM response: {resp}")
        # return resp
        logger.info(f"Query: {query}")
        # genimi = Gemini(
        #     model="models/gemini-exp-1206",
        #     api_key=self.google_api_key,
        #     temperature=1,
        #     max_tokens=8192
        # )
        from llama_index.core.chat_engine import SimpleChatEngine
        chat_engine = SimpleChatEngine.from_defaults(
            system_prompt=os.getenv("SYSTEM_PROMPT"),
            memory=self.chat_memory,
            # llm=genimi
        )
        # chat_engine.chat_repl()
        response = chat_engine.chat(query)
        logger.info(f"LLM response: {response}")
        # 持久化
        self.chat_store.persist(persist_path="chat_store.json")
        return response

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
            # 以当天时刻对collection命名
            self.current_collection_name = f"chat_{int(time.time())}"
            collection = self.chroma_client.get_or_create_collection(self.current_collection_name)
            logger.info(f"Got collection: {self.current_collection_name}")
            
            # Create vector store and storage context
            vector_store = ChromaVectorStore(chroma_collection=collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            
            # Add documents to vector store
            # Create index with storage context
            index = VectorStoreIndex.from_documents(
                documents,
                storage_context=storage_context,
                show_progress=True,
                # embed_model=self.embed_model # default in Settings
            )
            # 文档追踪
            # print(index.ref_doc_info)
            
            # query_engine = index.as_query_engine(
            #     streaming=True
            #     # llm=self.llm, # default in Settings
            # )
            # # Get response
            # response = query_engine.query(query)
            # logger.info(f"LLM response: {response}")
            
            # TODO 方式一 简单 as_chat_engine 问题：聊多了之后，会忽略新加的documents信息
            chat_engine = index.as_chat_engine( # ChatMode.BEST
                chat_mode="condense_plus_context",
                memory=self.chat_memory,
                verbose=False,
            )
            # 方式二 from_defaults 问题：retriever尚不了解 有时候会导致信息被错误过滤
            # context_prompt = os.getenv("DOC_PROMPT")
            # from llama_index.core.vector_stores import MetadataInfo, VectorStoreInfo
            # vector_store_info = VectorStoreInfo(
            #     content_info="learning materials",
            #     metadata_info=[
            #         # MetadataInfo(
            #         #     name="title", = stan 待探明
            #         #     description="""
            #         #         The title of the document. 
            #         #     """,
            #         #     type="string",
            #         # )
            #     ],
            # )
            # from llama_index.core.retrievers import VectorIndexAutoRetriever
            # retriever = VectorIndexAutoRetriever(
            #     index,
            #     vector_store_info=vector_store_info,
            #     similarity_top_k=3,
            #     empty_query_top_k=10,  # if only metadata filters are specified, this is the limit
            #     verbose=True,
            # )
            # from llama_index.core.chat_engine import CondensePlusContextChatEngine
            # chat_engine = CondensePlusContextChatEngine.from_defaults(
            #     retriever=index.as_retriever(),
            #     memory=self.chat_memory,
            #     context_prompt=context_prompt
            # )

            response = chat_engine.chat(query)
            logger.info(f"LLM response: {response}")
            # 持久化
            self.chat_store.persist(persist_path="chat_store.json")
            
            # Format response with sources
            response_text = str(response)
            if response.source_nodes:
                response_text += "\n\n参考来源:\n"
                for node in response.source_nodes:
                    if "url" in node.metadata:
                        response_text += f"- {node.metadata['url']}\n"
            
            # 清理临时collection
            self.cleanup_collection()

            return response_text
            
        except Exception as e:
            logger.error(f"Error in chat_with_articles: {e}")
            return f"处理请求时发生错误: {str(e)}"
    
    def cleanup_collection(self):
        """Clean up temporary collection
        """
        try:
            if not self.current_collection_name:
                return
                
            self.chroma_client.delete_collection(self.current_collection_name)
            logger.info(f"Deleted collection: {self.current_collection_name}")
            self.current_collection_name = None
            
        except Exception as e:
            logger.error(f"Error cleaning up collection: {e}")
