"""
RAG service for handling multi-document conversations
"""
from math import log
import os
import sys
import logging
import time
import uuid
import numpy as np
import asyncio
import requests
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple, Union
from chromadb.utils import embedding_functions
from llama_index.core import Settings
from llama_index.llms.gemini import Gemini
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.voyageai import VoyageEmbedding
from llama_index.embeddings.jinaai import JinaEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.core import Document, VectorStoreIndex, ServiceContext, StorageContext
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from llama_index.core.storage.chat_store import SimpleChatStore
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage
from llama_index.core.chat_engine import SimpleChatEngine
import json
from pymilvus import DataType

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)
from src.models import article_crud
from src.utils.llms.llm_common_utils import LLMCommonUtils
from src.database.connection import db_session
from src.database.milvus_client import Milvus
from src.models.article import Article
from src.models.article_crud import *
from src import VECTOR_DB_ARTICLES, VECTOR_DB_CHATS, VECTOR_DB_NOTES
import src.utils.embeddings.voyager as voyager
import src.utils.embeddings.jina as jina
from src.utils.text_input_handler import TextInputHandler
from models.chat import Chat
from models.chat_crud import *
from src.utils.redis.redis_service import RedisService

redis_client = RedisService()

logger = logging.getLogger(__name__)
# 向量数据库抽象接口
class VectorDB(ABC):
    @abstractmethod
    def get_client(self):
        pass

    @abstractmethod
    def create_collection(self, collection_name: str, embedding_fn=None, schema=None, index_params=None):
        pass
        
    @abstractmethod
    def get_collection(self, collection_name: str, embedding_fn=None):
        pass
        
    @abstractmethod
    def add_documents(self, collection_name: str, documents: List[Dict[str, Any]], embeddings: Optional[List[List[float]]] = None, data=None):
        pass
        
    @abstractmethod
    def search(self, collection_name: str, query: str, limit: int = 5, output_fields=["text"], search_params={}, filter="") -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def delete_items(self, collection_name: str, item_ids: List[str], filter: str = None):
        pass

    @abstractmethod
    def delete_collection(self, collection_name: str):
        pass

    @abstractmethod
    def count_items(self, collection_name: str) -> int:
        pass

# Chroma实现
class ChromaDB(VectorDB):
    def __init__(self):
        self.client = chromadb.Client()
    
    def get_client(self):
        return self.client

    def create_collection(self, collection_name: str, embedding_fn=None, schema=None, index_params=None):
        return self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_fn
        )
        
    def get_collection(self, collection_name: str, embedding_fn=None):
        return self.client.get_collection(
            name=collection_name,
            embedding_function=embedding_fn
        )
        
    def add_documents(self, collection_name: str, documents: List[Dict[str, Any]], embeddings: Optional[List[List[float]]] = None, data=None):
        collection = self.get_collection(collection_name)
        collection.upsert(
            documents=[doc["text"] for doc in documents],
            metadatas=[{k: v for k, v in doc.items() if k != "text"} for doc in documents],
            embeddings=embeddings
        )
        
    def search(self, collection_name: str, query: str, limit: int = 5, output_fields=["text"], search_params={}, filter="") -> List[Dict[str, Any]]:
        collection = self.get_collection(collection_name)
        results = collection.query(
            query_texts=[query],
            n_results=limit
            #  include=["documents", "distances", "metadatas"]
        )
        return results

    def delete_items(self, collection_name: str, item_ids: List[str], filter: str = None):
        collection = self.get_collection(collection_name)
        collection.delete(ids=item_ids)
        
    def delete_collection(self, collection_name: str):
        self.client.delete_collection(name=collection_name)
        
    def count_items(self, collection_name: str) -> int:
        collection = self.get_collection(collection_name)
        return collection.count()

# Milvus实现
class MilvusDB(VectorDB):
    def __init__(self):
        self.client = Milvus()

    def get_client(self):
        return self.client.get_client()
        
    def create_collection(self, collection_name: str, embedding_fn=None, schema=None, index_params=None):
        return self.client.create_collection(collection_name, schema=schema, index_params=index_params)
        
    def get_collection(self, collection_name: str, embedding_fn=None):
        if self.client.has_collection(collection_name):
            return self.client.describe_collection(collection_name)
        else:
            return None

    async def add_documents(self, collection_name: str, documents: List[Dict[str, Any]], embeddings: Optional[List[List[float]]] = None, data=None):
        if data:
            await self.client.upsert_data(collection_name, data)
        else:
            await self.client.upsert_docs(collection_name, documents, embeddings)
        
    def search(self, collection_name: str, query: str, limit: int = 5, output_fields=["text"], search_params={}, filter="") -> List[Dict[str, Any]]:
        return self.client.search(collection_name, query, limit, output_fields, search_params, filter)

    def delete_items(self, collection_name: str, item_ids: List[str], filter: str = None):
        self.client.delete_items(collection_name, item_ids, filter)
        
    def delete_collection(self, collection_name: str):
        self.client.delete_collection(collection_name)
        
    def count_items(self, collection_name: str) -> int:
        return self.client.count_items(collection_name)

class RAGService:
    """RAG service for handling document-based conversations"""
    
    def __init__(self, vector_db_type: str = "milvus"):
        """Initialize RAG service
        Args:
            vector_db_type: 向量数据库类型，可选 "chroma" 或 "milvus"
        """
        # Load API keys
        self.voyage_api_key = os.getenv("VOYAGE_API_KEY")
        self.google_api_key = os.getenv("GEMINI_API_KEY")
        self.GEMINI_MODEL = os.getenv("GEMINI_MODEL")
        self.JINA_API_KEY = os.getenv("JINA_API_KEY")
        if not self.voyage_api_key or not self.google_api_key:
            raise ValueError("Missing required API keys")
        # 数据库
        self.session = db_session
        # 向量数据库
        self.vector_db_type = vector_db_type
        if vector_db_type == "chroma":
            self.vector_db = ChromaDB()
        elif vector_db_type == "milvus":
            self.vector_db = MilvusDB()
        else:
            raise ValueError(f"Unsupported vector database type: {vector_db_type}")
        # 模块1 嵌入 Initialize embedding model
        self.voyage = VoyageEmbedding(
            model_name = "voyage-3",
            voyage_api_key = self.voyage_api_key
        )
        self.jina = JinaEmbedding( # 推荐
            model_name = "jina-embeddings-v3",
            api_key = self.JINA_API_KEY,
            dimensions = 128, # MRL技术
            late_chunking = True # late_chunking 技术
        )

        # 模块2 大模型 Initialize LLM

        # 模块3 向量数据库
        # 向量数据库优化 https://docs.trychroma.com/docs/collections/configure
        # https://www.llamaindex.ai/blog/evaluating-the-ideal-chunk-size-for-a-rag-system-using-llamaindex-6207e5d3fec5
        # self.chroma_client = chromadb.PersistentClient(path="src/database/chroma_db")
        # Client_Server_Mode `chroma run --path /db_path`
        # self.chroma_client = chromadb.HttpClient(host='localhost', port=8000)
        # Current collection name
        self.current_collection_name = "news_reader_rag" # 默认值
        class DocEmbeddingJINA(EmbeddingFunction):
            def __call__(self, input: Documents) -> Embeddings:
                return jina.get_doc_embeddings_jina(documents=input, task="retrieval.passage")
        self._embed_doc_jina = DocEmbeddingJINA()
        class QueryEmbeddingJINA(EmbeddingFunction):
            def __call__(self, input: Documents) -> Embeddings:
                return jina.get_doc_embeddings_jina(documents=input, task="retrieval.query")
        self._embed_query_jina = QueryEmbeddingJINA()
        class DocEmbeddingVoyage(EmbeddingFunction):
            def __call__(self, input: Documents) -> Embeddings:
                return voyager.get_doc_embeddings(documents=input)
        self._embed_doc_voyage = DocEmbeddingVoyage()
        class QueryEmbeddingVoyage(EmbeddingFunction):
            def __call__(self, input: Documents) -> Embeddings:
                return voyager.get_query_embedding(query=input)
        self._embed_query_voyage = QueryEmbeddingVoyage()

        # 模块4 聊天记忆 Initialize ChatStore and ChatMemoryBuffer
        from llama_index.storage.chat_store.upstash import UpstashChatStore
        from llama_index.core.memory import ChatMemoryBuffer
        remote_chat_store = UpstashChatStore( # https://docs.llamaindex.ai/en/stable/module_guides/storing/chat_stores/#usage
            redis_url=os.getenv("UPSTASH_REDIS_REST_URL"),
            redis_token=os.getenv("UPSTASH_REDIS_REST_TOKEN"),
            # ttl=300,  # Optional: Time to live in seconds
        )
        local_chat_store = SimpleChatStore.from_persist_path(
            persist_path="chat_store.json"
        )
        self.chat_store = remote_chat_store if remote_chat_store else local_chat_store

        # 全局配置 Global 默认值
        # Settings.llm = self.gemini
        Settings.embed_model = self.voyage
        # Settings.context_window=8192
        # Settings.text_splitter = SentenceSplitter(chunk_size=1024) # JINA 1024 最佳
        Settings.chunk_size = 1024
        Settings.chunk_overlap = 50
        # Settings.Callbacks https://docs.llamaindex.ai/en/stable/module_guides/supporting_modules/settings/
    
    def get_chat_engine(self, chat_store_key: str, model: str = "", api_key: str = None):
        chat_memory = ChatMemoryBuffer.from_defaults(
            token_limit=2000000, # 1206 200w | think 3w
            chat_store=self.chat_store,
            chat_store_key=chat_store_key
        )
        system_prompt=LLMCommonUtils._get_time_prompt()
        logger.info(f"model: {model}")

        # 检查是否是配置模型（以CFG_开头）
        is_cfg_model = model.startswith('CFG_') if model else False
        model_name = model.replace('CFG_', '') if is_cfg_model else model

        # 配置模型 - Gemini
        if is_cfg_model and "gemini" in model_name.lower():
            model_name = "models/" + os.getenv(model_name)
            api_key = api_key or os.getenv("GEMINI_API_KEY")
            gemini = Gemini(
                system_prompt=system_prompt,
                model=model_name,
                api_key=api_key,
                temperature=float(os.getenv("LLM_TEMPERATURE")),
                max_tokens=int(os.getenv("LLM_MAX_TOKENS", 4096))
            )
            chat_engine = SimpleChatEngine.from_defaults(
                system_prompt=system_prompt,
                memory=chat_memory,
                llm=gemini
            )
        # 配置模型 - OpenAI
        elif is_cfg_model and "openai" in model_name.lower():
            openai = OpenAI(    
                model=os.getenv("OPENAI_MODEL"),
                api_key=api_key or os.getenv("OPENAI_API_KEY"),
                api_base=os.getenv("OPENAI_API_BASE"),
                temperature=float(os.getenv("LLM_TEMPERATURE")),
                max_tokens=int(os.getenv("LLM_MAX_TOKENS", 4096))
            )
            chat_engine = SimpleChatEngine.from_defaults(
                system_prompt=system_prompt,
                memory=chat_memory,
                llm=openai
            )
        # 配置模型 - MiniMax 暂不支持
        elif is_cfg_model and "minimax" in model_name.lower():
            from llama_index.llms.minimax import Minimax
            minimax = Minimax(
                model=os.getenv("MINIMAX_MODEL"),
                api_key=api_key or os.getenv("MINIMAX_API_KEY"),
                group_id=os.getenv("MINIMAX_GROUP_ID"),
                temperature=float(os.getenv("LLM_TEMPERATURE")),
                max_tokens=int(os.getenv("LLM_MAX_TOKENS", 4096))
            )
            chat_engine = SimpleChatEngine.from_defaults(
                system_prompt=system_prompt,
                memory=chat_memory,
                llm=minimax
            )
        # OpenRouter模型
        else:
            from llama_index.llms.openrouter import OpenRouter
            llm = OpenRouter(
                api_key=api_key or os.getenv("OPENROUTER_API_KEY"),
                max_tokens=int(os.getenv("LLM_MAX_TOKENS", 4096)),
                temperature=float(os.getenv("LLM_TEMPERATURE")),
                model=model or "google/gemini-2.0-flash-exp:free",  # 使用传入的模型名称或默认值
            )
            chat_engine = SimpleChatEngine.from_defaults(
                system_prompt=system_prompt,
                memory=chat_memory,
                llm=llm
            )
        return chat_engine
    
    # 直接聊天
    # 一级 - 短期记忆（对话窗口）
    # 二级 - 长期记忆（笔记区）
    def chat(self, conversation_id: str, question: str, model: str = "", api_key: str = None) -> str:
        # 方式1 直接调用LLM对话
        # resp = self.gemini.complete(query)
        # logger.info(f"LLM response: {resp}")
        # return resp
        # logger.info(f"Query: {query}")
        if not conversation_id:
            raise ValueError("no conversation_id")
        logger.info(f"Conversation ID: {conversation_id}")
        # 方式2 使用LlamaIndex框架对话
        chat_store_key = "user1_conv" + conversation_id
        chat_engine = self.get_chat_engine(chat_store_key, model, api_key)
        # chat_engine.chat_repl()
        logger.info(f"Query length: {len(question)}")
        response = chat_engine.chat(question)
        logger.info(f"LLM response: {response}") # LLM response 格式：纯字符串
        logger.info(f"Response length: {len(str(response))}")

        # LlamaIndex 会自动保存持久化（本地json或redis）
        # self.save_chat(chat_store_key, chat_engine.chat_history)
        # self.chat_store.persist(persist_path="chat_store.json")
        return response
    
    # 带附件（上下文）聊天 各种URL 文件等 图片另说
    def chat_with_context(self, conversation_id: str, context: str, question: str, model: str = "", api_key: str = None) -> str:
        # 1. 构建上下文
        prompt = ""
        if context:
            prompt += f"# 参考内容：\n<blockquote>{context}</blockquote>\n\n"
        prompt += f"\n{question}"
        # 2. 使用现有的chat方法
        return self.chat(conversation_id, prompt, model, api_key)

    # 对话数据库里的文章
    def chat_with_article(self, conversation_id: str, article_ids: List[int], question: str, model: str = "", api_key: str = None) -> str:
        # 1. 构建上下文
        articles = article_crud.get_article_by_ids(db_session, article_ids)
        if articles:
            articles_text = "\n".join([f"```标题：{article.title}\n内容：{article.content}```" for article in articles])
            return self.chat_with_context(conversation_id, articles_text, question, model, api_key)
        else:
            return self.chat_with_context(conversation_id, "暂无相关资料。", question, model, api_key)

    # 对话知识库（资料） TODO 待改造
    def chat_with_articles_old(self, conversation_id: str, article_ids: List[int], question: str) -> str:
        """Chat with selected articles
        Args:
            article_ids: List of article IDs
            question: User question
        Returns:
            Response from LLM
        """
        try:
            logger.info(f"用户选择了文章: {article_ids}")
            logger.info(f"Conversation ID: {conversation_id}")
            # Create collection for these documents
            collection = self.vector_db.get_collection(
                collection_name = VECTOR_DB_ARTICLES,
                embedding_fn = self._embed_doc_voyage
            )
            logger.info(f"Got DB collection: {VECTOR_DB_ARTICLES}")
            # Create vector store
            if self.vector_db_type == "chroma":
                vector_store = ChromaVectorStore(chroma_collection=collection)
            elif self.vector_db_type == "milvus": # TODO windows本地无法测试 远程报错
                vector_store = MilvusVectorStore(uri=os.getenv("ZILLIZ_MILVUS_URL"), token=os.getenv("ZILLIZ_MILVUS_KEY"), collection_name=VECTOR_DB_ARTICLES)
            else:
                raise ValueError(f"Unsupported vector database type: {self.vector_db_type}")
            # 如果collection不为空，从向量库加载索引
            if self.vector_db.count_items(collection_name=VECTOR_DB_ARTICLES) > 0:
                logger.info("使用现有向量表查询")
                index = VectorStoreIndex.from_vector_store(
                    vector_store # 从向量存储调出索引
                )
            else: # 如果collection为空，用文档创建索引（数据库转向量库）
                logger.info("创建新向量表")
                # Get articles from database
                articles = get_article_by_ids(db_session, article_ids)
                if not articles:
                    logger.info("No articles found")
                    return "未找到相关文章"
                logger.info(f"Got {len(articles)} articles")
                # Convert to documents
                documents = self._articles_to_documents(articles)
                logger.info(f"Got {len(documents)} documents")
                storage_context = StorageContext.from_defaults(vector_store=vector_store)
                index = VectorStoreIndex.from_documents(
                    documents,
                    storage_context=storage_context, # 将文档加入向量存储
                    show_progress=True,
                    # embed_model=self.embed_model
                )
            
            # 文档追踪 只支持 SimpleDirectoryReader 不支持 向量库
            # print(index.ref_doc_info)

            # Query 模式
            # query_engine = index.as_query_engine(
            #     streaming=True
            #     # llm=self.llm, # default in Settings
            # )
            # response = query_engine.query(question)
            # logger.info(f"LLM response: {response}")

            # Chat 模式
            # TODO 方式一 as_chat_engine 简单 high-level api 问题：聊多了，会忽略新的documents信息
            chat_engine = index.as_chat_engine(
                # https://docs.llamaindex.ai/en/stable/examples/chat_engine/chat_engine_context/
                # 1 first retrieve text from the index using the user message
                # 2 set the retrieved text as context in the system prompt
                # 3 return an answer to the user message
                chat_mode="context",
                memory=self.chat_memory,
				similarity_top_k=10,
                verbose=True,
                system_prompt=( # TODO 不确定是否生效
                    "对于学习类的问题，你会先看看你和用户的聊天历史（如有），然后再看看资料库（如有），然后，把它们作为上下文，总结出方法论，优点、缺点"
                ),
                context_prompt=( # TODO 不确定是否生效
                    "对于学习类的问题，你会先看看你和用户的聊天历史（如有），然后再看看资料库（如有），然后，把它们作为上下文，总结出方法论，优点、缺点"
                ),
            )

            # 方式二 from_defaults low-level api # https://docs.llamaindex.ai/en/stable/examples/llm/openai/#manual-tool-calling
            # from llama_index.core import PromptTemplate
            # from llama_index.core.llms import ChatMessage, MessageRole
            # from llama_index.core.chat_engine import CondenseQuestionChatEngine
            # custom_prompt = PromptTemplate(
            #     """\
            #     Given a conversation (between Human and Assistant) and a follow up message from Human, \
            #     rewrite the message to be a standalone question that captures all relevant context \
            #     from the conversation.

            #     <Chat History>
            #     {chat_history}

            #     <Follow Up Message>
            #     {question}

            #     <Standalone question>
            #     """
            # )
            # # list of `ChatMessage` objects
            # custom_chat_history = [
            #     ChatMessage(
            #         role=MessageRole.USER,
            #         content="Hello assistant, we are having a insightful discussion about Paul Graham today.",
            #     ),
            #     ChatMessage(role=MessageRole.ASSISTANT, content="Okay, sounds good."),
            # ]
            # query_engine = index.as_query_engine()
            # chat_engine = CondenseQuestionChatEngine.from_defaults(
            #     query_engine=query_engine,
            #     condense_question_prompt=custom_prompt,
            #     chat_history=custom_chat_history,
            #     verbose=True,
            # )
            # 方式二.1 增加retriever 问题：retriever尚不了解 有时候会导致信息被错误过滤
            # context_prompt = os.getenv("CONTEXT_PROMPT")
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
            #     retriever=index.as_retriever(similarity_top_k=2),
            #     memory=self.chat_memory,
            #     context_prompt=context_prompt
            # )
            # https://docs.llamaindex.ai/en/stable/examples/cookbooks/contextual_retrieval/#set-similarity_top_k
            response = chat_engine.chat(question)
            logger.info(f"LLM response: {response}")
            # 持久化
            self.chat_store.persist(persist_path="chat_store.json")
            # Format response with sources
            response_text = str(response)
            if response.source_nodes:
                response_text += "\n\n参考来源:\n"
                for node in response.source_nodes:
                    if "url" in node.metadata and node.metadata["url"] not in response_text:
                        response_text += f"- {node.metadata['url']}\n"
            # 清理 临时collection
            self.cleanup_collection()
            return response_text
        except Exception as e:
            logger.error(f"Error in chat_with_articles: {e}")
            return f"处理请求时发生错误: {str(e)}"
    
    # RAG测评用
    def retrieve(self, collection_name, query: str, top_k: int = 20) -> List[Dict]:
        """统一的检索接口，用于评估
        Args:
            query: 查询文本
            top_k: 返回结果数量
        Returns:
            List[Dict]: 检索结果列表，包含chunk_id和score
        """
        try:
            results = self.vector_db.search(collection_name, query, limit=top_k)
            # 格式化结果
            formatted_results = []
            if results and results[0]:
                results = results[0]
                for i in range(len(results)):
                    formatted_results.append({
                        'id': results[i].get('id'),
                        'score': results[i].get('distance'),
                        'content': results[i].get('entity').get('text')
                    })
            return formatted_results
        except Exception as e:
            logger.error(f"Error in retrieve: {e}")
            return []

    # ------------------------------ 文件管理 ------------------------------

    def _articles_to_documents(self, articles: List[Article]) -> List[Document]:
        """Convert articles to LlamaIndex documents
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
    
    def generate_id_with_time_and_random(self):
        timestamp = time.time_ns()
        random_part = uuid.uuid4().int & (1 << 32) - 1
        # 使用 numpy.int64
        timestamp_part = np.int64(timestamp & ((1 << 31) - 1))  # 取时间戳低 31 位
        return (timestamp_part << np.int64(32)) | np.int64(random_part)

    # 将文章添加到向量数据库
    async def add_articles_to_vector_store(self, articles: List[Article], collection_name: Optional[str] = None):
        try:
            # 获取或创建collection
            if collection_name is None:
                collection_name = f"{self.current_collection_name}_{int(time.time())}"
            # 切分内容或概要并入库 
            chunk_size = os.getenv("CHUNK_SIZE", 1000)
            overlap = os.getenv("OVERLAP", 100)
            for article in articles:
                chunks, nodes, small_big_dict = await TextInputHandler.split_text(article.content or article.summary, int(chunk_size), int(overlap))
                if not chunks:
                    logger.warning(f"文章 {article.id} 没有有效内容可切分")
                    continue
                # 为每个chunk生成唯一ID
                chunk_ids = [f"article_{article.id}_chunk_{i}" for i in range(len(chunks))]
                logger.info(f"<{article.title}> 文章切分成 {len(chunks)} 个chunk")
                # TODO chunk 用LLM增加上下文
                client = self.vector_db.get_client()
                schema = client.create_schema(
                    auto_id=False,
                    enable_dynamic_fields=True,
                )
                # 添加 JSON 字段
                schema.add_field(field_name="metadata", datatype=DataType.JSON)
                schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True)
                schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=2048)
                schema.add_field(field_name="embedding", datatype=DataType.FLOAT_VECTOR, dim=1024)
                # 创建 Collection
                index_params = client.prepare_index_params()
                index_params.add_index(
                    field_name="embedding",
                    index_type="AUTOINDEX",
                    metric_type="COSINE"
                )
                self.vector_db.create_collection(collection_name, None, schema, index_params)
                # 1 将子句保存到向量库
                doc_embeddings = voyager.get_doc_embeddings(nodes)
                vc_nodes = []
                for i, node in enumerate(nodes):
                    chunk_id = small_big_dict.get(i)
                    vc_nodes.append({
                        "metadata": {"article_id": article.id, "article_title": article.title, "chunk_id": f"article_{article.id}_chunk_{chunk_id}"},
                        "id": self.generate_id_with_time_and_random(),
                        "text": node,
                        "embedding": doc_embeddings[i] # 1024
                    })
                await self.vector_db.add_documents(collection_name, [], [], vc_nodes)
                # 更新sqlite数据库 文章的vector_ids
                article.vector_ids = ",".join(chunk_ids)
                update_article(db_session, article.id, {"vector_ids": article.vector_ids})
                # 2 将父文档缓存 save big chunk to redis {article_chunks: {article_1_chunk_19: "..."}}
                for i, big_chunk in enumerate(chunks):
                    chunk_id = f"article_{article.id}_chunk_{i}"
                    redis_client.set_hash(f"article_chunks", {chunk_id: big_chunk})
            logger.info(f"成功将 {len(articles)} 个文档添加到向量库 {collection_name} 集合中")
            return True
        except Exception as e:
            logger.error(f"添加文章到向量数据库失败: {str(e)}")
            return False

    # 后台异步添加文章到向量数据库
    def add_articles_to_vector_store_background(self, articles: List[Article], collection_name: Optional[str] = None):
        import threading
        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.add_articles_to_vector_store(articles, collection_name))
                logger.info(f"后台成功添加 {len(articles)} 篇文章到向量数据库")
            except Exception as e:
                logger.error(f"后台添加文章失败: {str(e)}")
            finally:
                loop.close()
        
        thread = threading.Thread(target=run_async)
        thread.daemon = True
        thread.start()

    def delete_articles_from_vector_store(self, articles: List[Article], collection_name: Optional[str] = None):
        try:
            if collection_name is None:
                collection_name = self.current_collection_name
            
            for article in articles:
                if not article.vector_ids:
                    continue
                    
                # 获取文章的所有向量ID
                vector_ids = article.vector_ids.split(",")
                
                # 从VectorDB中删除
                filter=f'metadata["article_id"] == {article.id}' # TODO 此条件可以优化
                self.vector_db.delete_items(collection_name, item_ids=None, filter=filter)
                
                # 清空文章的vector_ids
                update_article(db_session, article.id, {"vector_ids": None})
                
                # 删除redis缓存 # TODO 此循环可以优化
                for chunk_id in vector_ids:
                    redis_client.delete_hash_value("article_chunks", chunk_id)
                # async def inner_async_function():
                #     await redis_client.batch_delete_hash_fields(f"article_{article.id}_chunk_*")
                # asyncio.run(inner_async_function())

            logger.info(f"成功从向量库 {collection_name} 删除 {len(articles)} 个文档")
            return True
        except Exception as e:
            logger.error(f"从向量数据库删除文章失败: {str(e)}")
            return False

    def cleanup_collection(self):
        """Clean up temporary collection
        """
        try:
            if not self.current_collection_name:
                return
            # self.chroma_client.delete_collection(self.current_collection_name)
            self.vector_db.delete_collection(self.current_collection_name)
            logger.info(f"Deleted collection: {self.current_collection_name}")
            self.current_collection_name = None
        except Exception as e:
            logger.error(f"Error cleaning up collection: {e}")
    
    # ------------------------------ 聊天管理 ------------------------------
    # redis key设计：user1_conversation1
    # 加载用户的某次对话 id = user1_conversation1 DONE
    def load_conversation_from_redis(self, conversation_id: str):
        """从Redis加载单个对话内容"""
        try:
            messages = self.chat_store.get_messages(conversation_id)
            if not messages:
                return None
            logger.info(f"从Redis加载对话：{conversation_id}, 共 {len(messages)} 条消息")
            # 转换消息格式
            formatted_messages = []
            for msg in messages:
                formatted_message = {
                    "role": msg.role,
                    "additional_kwargs": {},
                    "blocks": [
                        {
                            "block_type": "text",
                            "text": msg.content
                        }
                    ]
                }
                formatted_messages.append(formatted_message)
            return formatted_messages
        except Exception as e:
            logger.error(f"Error loading conversation from redis: {e}")
            return None

    # 加载用户的所有对话列表（仅标题和基本信息） DONE
    def load_conversations(self, user_id: int, query: str="", conv_ids: List[str]=[]):
        try:
            # 1 获取数据库用户的所有对话(仅is_active的)
            user_conversations = search_chats(self.session, int(user_id), query, conv_ids, limit=100)
            if not user_conversations:
                return []
            from collections import OrderedDict
            dict = OrderedDict((chat.conversation_id, chat) for chat in user_conversations)
            # 2 数据同步校验 获取redis中的对话 如果redis已经删除或者过期，则不显示
            from src.utils.redis.redis_service import redis_service
            redis_keys = redis_service.get_keys(f"user{user_id}_conv*")
            if redis_keys:
                for chat in user_conversations: # user1_conv1
                    db_key = "user" + str(user_id) + "_conv" + chat.conversation_id
                    if db_key not in redis_keys:
                        dict.pop(chat.conversation_id)
            # 3 转换为前端需要的格式
            conversations = []
            for chat in dict.values():
                conversations.append({
                    'id': chat.id,
                    'title': chat.title or f'对话 {chat.id}',
                    'conversation_id': chat.conversation_id,
                })
            return conversations
        except Exception as e:
            logger.error(f"Error loading user histories: {e}")
            return []

    # 保存对话内容
    def save_chat(self, redis_key: str, messages: json) -> bool:
        try:
            # 转换为ChatMessage列表
            chat_messages = []
            for msg in messages:
                content = msg.content
                chat_messages.append(ChatMessage(
                    role=msg.role,
                    content=content
                ))
            # 保存到Redis
            self.chat_store.set_messages(redis_key, chat_messages)
            return True
        except Exception as e:
            logger.error(f"Error in save_chat: {e}")
            return False

    def delete_chat(self, redis_key: str) -> bool:
        try:
            self.chat_store.delete_messages(redis_key)
            return True
        except Exception as e:
            logger.error(f"Error in delete_chat: {e}")
            return False
            
    # 编辑消息 (注意 消息只是对话中的一段)
    def edit_chat_msg(self, redis_key: str, message_index: int, new_content: str, role: str) -> bool:
        try:
            chat_store_key = redis_key
            chat_engine = self.get_chat_engine(chat_store_key)
            chat_history = chat_engine.chat_history
            chat_history[message_index] = ChatMessage(content=new_content, role=role)
            self.save_chat(chat_store_key, chat_history)
        except Exception as e:
            logger.error(f"Error in edit_chat: {e}")
            return False
        return True
    
    # 删除消息 (注意 消息只是对话中的一段)
    def delete_chat_msg(self, redis_key: str, message_index: int) -> bool:
        try:
            # 取自 engine history
            chat_store_key = redis_key
            chat_engine = self.get_chat_engine(chat_store_key)
            chat_history = chat_engine.chat_history
            if len(chat_history) > message_index:
                chat_history.pop(message_index)
            # 更新远程持久化数据
            self.save_chat(chat_store_key, chat_history)
        except Exception as e:
            logger.error(f"Error in delete_chat: {e}")
            return False
        return True
    


    async def main(self):
        
        # Add messages
        messages = [
            ChatMessage(content="Hello", role="user"), # index = 0
            ChatMessage(content="Hi there!", role="assistant"),
            ChatMessage(content="Middle user", role="user"), # 待编辑 index = 2
            ChatMessage(content="Middle assistant", role="assistant"),
            ChatMessage(content="Last user", role="user"),
            ChatMessage(content="Last assistant", role="assistant"), # 待删除 index = 5
        ]
        await self.chat_store.async_set_messages("conversation1", messages)
        # 查看初始化情况 Retrieve messages
        retrieved_messages = await self.chat_store.async_get_messages("conversation1")
        print(retrieved_messages)
        # print结果：[ChatMessage(role=<MessageRole.USER: 'user'>, additional_kwargs={}, blocks=[TextBlock(block_type='text', text='Hello')]), ChatMessage(role=<MessageRole.ASSISTANT: 'assistant'>, additional_kwargs={}, blocks=[TextBlock(block_type='text', text='Hi there!')])]
        
        # 1 编辑效果：先删除再添加
        await self.chat_store.async_delete_message("conversation1", 2)
        # Add message
        message = ChatMessage(content="Middle user update", role="user")
        await self.chat_store.async_add_message("conversation1", message, 2)
        # 查看编辑结果 Retrieve messages
        retrieved_messages = await self.chat_store.async_get_messages("conversation1")
        print(retrieved_messages)

        # 2 重新回答效果
        # 删除最后一条（AI回复，用于重新回答）Delete last message
        deleted_message = await self.chat_store.async_delete_last_message("conversation1")
        print(f"Deleted message: {deleted_message}")
        await self.chat_store.async_add_message("conversation1", ChatMessage(content="Last assistant New!", role="assistant"), 5)
        # 查看重新回答结果
        retrieved_messages = await self.chat_store.async_get_messages("conversation1")
        print(retrieved_messages)

# main
if __name__ == "__main__":
    print("RAG service main")
    rag = RAGService()
    # asyncio.run(rag.main())

    rag.chat("conversation1", "hi,gemi，现在几点了", "CFG_GEMINI_MODEL")

    # 清理向量库脚本 如果调整了向量维度 也可通过这重置
    # 正常响应 2024-12-27 00:26:47,042 - INFO     - posthog.py[line:22] - Anonymized telemetry enabled. 
    # See https://docs.trychroma.com/telemetry for more information.
    # chroma_client = chromadb.PersistentClient(path="src/database/chroma_db")
    # chroma_client = chromadb.HttpClient(host='localhost', port=8000)
    # Current collection name
    # chroma_client.delete_collection(name=VECTOR_DB_ARTICLES)

    # 查询测试 chroma
    # chroma_client = chromadb.HttpClient(host='localhost', port=8000)
    # class EmbeddingVoyage(EmbeddingFunction):
    #         def __call__(self, input: Documents) -> Embeddings:
    #             return voyager.get_doc_embeddings(documents=input)
    # collection = chroma_client.get_collection("news_reader_rag",
    #     embedding_function = EmbeddingVoyage())
    # results = collection.query(
    #     query_texts=["RAGFlow 引入的第二个设计亮点是什么？"], # Chroma will embed this for you
    #     n_results=3 # how many results to return
    # )
    # print(results)