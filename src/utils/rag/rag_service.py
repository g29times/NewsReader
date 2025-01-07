"""
RAG service for handling multi-document conversations
"""
from math import log
import os
import sys
import logging
import time
import asyncio
import requests
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple, Union
from chromadb.utils import embedding_functions
from llama_index.core import Settings
from llama_index.llms.gemini import Gemini
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

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)
from src.database.connection import db_session
from src.database.milvus_client import Milvus
from src.models.article import Article
from src.models.article_crud import *
from src import VECTOR_DB_ARTICLES, VECTOR_DB_CHATS, VECTOR_DB_NOTES
import src.utils.embeddings.voyager as voyager
import src.utils.embeddings.jina as jina
from src.utils.text_input_handler import TextInputHandler
from models.chat import Base, Chat
from models.chat_crud import *

logger = logging.getLogger(__name__)
# 向量数据库抽象接口
class VectorDB(ABC):
    @abstractmethod
    def create_collection(self, collection_name: str, embedding_fn=None):
        pass
        
    @abstractmethod
    def get_collection(self, collection_name: str, embedding_fn=None):
        pass
        
    @abstractmethod
    def add_documents(self, collection_name: str, documents: List[Dict[str, Any]], embeddings: Optional[List[List[float]]] = None):
        pass
        
    @abstractmethod
    def search(self, collection_name: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def delete_items(self, collection_name: str, item_ids: List[str]):
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
        
    def create_collection(self, collection_name: str, embedding_fn=None):
        return self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_fn
        )
        
    def get_collection(self, collection_name: str, embedding_fn=None):
        return self.client.get_collection(
            name=collection_name,
            embedding_function=embedding_fn
        )
        
    def add_documents(self, collection_name: str, documents: List[Dict[str, Any]], embeddings: Optional[List[List[float]]] = None):
        collection = self.get_collection(collection_name)
        collection.upsert(
            documents=[doc["text"] for doc in documents],
            metadatas=[{k: v for k, v in doc.items() if k != "text"} for doc in documents],
            embeddings=embeddings
        )
        
    def search(self, collection_name: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        collection = self.get_collection(collection_name)
        results = collection.query(
            query_texts=[query],
            n_results=limit
            #  include=["documents", "distances", "metadatas"]
        )
        return results

    def delete_items(self, collection_name: str, item_ids: List[str]):
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
        
    def create_collection(self, collection_name: str, embedding_fn=None):
        return self.client.create_collection(collection_name)
        
    def get_collection(self, collection_name: str, embedding_fn=None):
        return None # self.client.get_collection(collection_name)
        
    async def add_documents(self, collection_name: str, documents: List[Dict[str, Any]], embeddings: Optional[List[List[float]]] = None):
        await self.client.upsert_docs(collection_name, documents)
        
    def search(self, collection_name: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        return self.client.search(collection_name, query, limit=limit)

    def delete_items(self, collection_name: str, item_ids: List[str]):
        self.client.delete_items(collection_name, item_ids)
        
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
        self.genimi = Gemini(
            system_prompt=os.getenv("SYSTEM_PROMPT"),
            model="models/" + self.GEMINI_MODEL,
            api_key=self.google_api_key,
            temperature=1,
            max_tokens=16000 # 8192
        )
        # 模块3 存储 Initialize Chroma client
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
            redis_url=os.getenv("REDIS_URL"),
            redis_token=os.getenv("REDIS_TOKEN"),
            # ttl=300,  # Optional: Time to live in seconds
        )
        local_chat_store = SimpleChatStore.from_persist_path(
            persist_path="chat_store.json"
        )
        self.chat_store = remote_chat_store if remote_chat_store else local_chat_store
        self.chat_memory = ChatMemoryBuffer.from_defaults(
            token_limit=10000, # shape 相似
            chat_store=self.chat_store,
            chat_store_key="user1", # TODO user_id
        )

        # 全局配置 Global 默认值
        Settings.llm = self.genimi
        Settings.embed_model = self.voyage
        # Settings.context_window=8192
        # Settings.text_splitter = SentenceSplitter(chunk_size=1024) # JINA 1024 最佳
        Settings.chunk_size = 1024
        Settings.chunk_overlap = 50
        # Settings.Callbacks https://docs.llamaindex.ai/en/stable/module_guides/supporting_modules/settings/
    
    def get_chat_engine(self, chat_store_key: str):
        chat_memory = ChatMemoryBuffer.from_defaults(
            token_limit=2000000, # 1206 200w | think 3w
            chat_store=self.chat_store,
            chat_store_key=chat_store_key,
        )
        chat_engine = SimpleChatEngine.from_defaults(
            system_prompt=os.getenv("SYSTEM_PROMPT"),
            memory=chat_memory,
            # llm=genimi
        )
        return chat_engine

    # 直接聊天
    # 一级 - 短期记忆（对话窗口）
    # 二级 - 长期记忆（笔记区）
    def chat(self, conversation_id: str, query: str) -> str:
        # 方式1 直接调用LLM对话
        # resp = self.genimi.complete(query)
        # logger.info(f"LLM response: {resp}")
        # return resp
        # logger.info(f"Query: {query}")
        if not conversation_id:
            raise ValueError("no conversation_id")
        logger.info(f"Conversation ID: {conversation_id}")
        # 方式2 使用LlamaIndex框架对话
        chat_store_key = "user1_conv" + conversation_id
        chat_engine = self.get_chat_engine(chat_store_key)
        # chat_engine.chat_repl()
        response = chat_engine.chat(query)
        logger.info(f"LLM response: {response}")
        # LLM response 格式：纯字符串
        # LlamaIndex 会自动保存持久化（本地json或redis）
        # self.save_chat(chat_store_key, chat_engine.chat_history)
        # self.chat_store.persist(persist_path="chat_store.json")
        return response
    
    def chat_with_file(self, conversation_id: str, file_content: str, question: str) -> str:
        # 1. 构建上下文
        context = f"文件内容：\n{file_content}\n问题：{question}"
        # 2. 使用现有的chat方法
        return self.chat(conversation_id, context)

    # 对话知识库（资料） TODO 待改造
    def chat_with_articles(self, conversation_id: str, article_ids: List[int], query: str) -> str:
        """Chat with selected articles
        Args:
            article_ids: List of article IDs
            query: User query
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
            # response = query_engine.query(query)
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
            response = chat_engine.chat(query)
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
    
    # 异步方法 将文章添加到向量数据库
    async def add_articles_to_vector_store(self, articles: List[Article], collection_name: Optional[str] = None):
        try:
            # 获取或创建collection
            if collection_name is None:
                collection_name = f"{self.current_collection_name}_{int(time.time())}"
            
            # 切分文本并入库
            for article in articles:
                chunks = await TextInputHandler.split_text(article.content or article.summary, max_chunk_length=2000)
                if not chunks:
                    logger.warning(f"文章 {article.id} 没有有效内容可切分")
                    continue
                # 为每个chunk生成唯一ID
                chunk_ids = [f"article_{article.id}_chunk_{i}" for i in range(len(chunks))]
                logger.info(f"JINA 将文章 <{article.title}> 切分成 {len(chunks)} 个chunk")
                # TODO chunk 用LLM增加上下文
                await self.vector_db.add_documents(collection_name, chunks)
                # 更新sqlite数据库 文章的vector_ids
                article.vector_ids = ",".join(chunk_ids)
                update_article(db_session, article.id, {"vector_ids": article.vector_ids})

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
            # collection = self.chroma_client.get_collection(name=collection_name)
            
            for article in articles:
                if not article.vector_ids:
                    continue
                    
                # 获取文章的所有向量ID
                vector_ids = article.vector_ids.split(",")
                
                # 从VectorDB中删除
                # collection.delete(ids=vector_ids)
                self.vector_db.delete_items(collection_name, vector_ids)
                
                # 清空文章的vector_ids
                update_article(db_session, article.id, {"vector_ids": None})
                
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

    # ------------------------------ 聊天记录管理 ------------------------------
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
    def load_conversations(self, user_id: str):
        try:
            # 获取用户的所有对话(仅is_active的)
            user_conversations = get_user_chats(self.session, int(user_id))
            if not user_conversations:
                return []
            # 转换为前端需要的格式
            conversations = []
            for chat in user_conversations:
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
    def save_chat(self, conversation_id: str, messages: json) -> bool:
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
            self.chat_store.set_messages(conversation_id, chat_messages)
            return True
        except Exception as e:
            logger.error(f"Error in save_chat: {e}")
            return False

    # 编辑消息
    def edit_chat(self, conversation_id: str, message_index: int, new_content: str, role: str) -> bool:
        try:
            chat_store_key = "user1_conv" + conversation_id
            chat_engine = self.get_chat_engine(chat_store_key)
            chat_history = chat_engine.chat_history
            chat_history[message_index] = ChatMessage(content=new_content, role=role)
            self.save_chat(chat_store_key, chat_history)
        except Exception as e:
            logger.error(f"Error in edit_chat: {e}")
            return False
        return True
    
    # 删除消息
    def delete_chat(self, conversation_id: str, message_index: int) -> bool:
        try:
            # 取自 engine history
            chat_store_key = "user1_conv" + conversation_id
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
    asyncio.run(rag.main())

    # 清理向量库脚本 如果调整了向量维度 也可通过这重置
    # 正常响应 2024-12-27 00:26:47,042 - INFO     - posthog.py[line:22] - Anonymized telemetry enabled. 
    # See https://docs.trychroma.com/telemetry for more information.
    # chroma_client = chromadb.PersistentClient(path="src/database/chroma_db")
    # chroma_client = chromadb.HttpClient(host='localhost', port=8000)
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