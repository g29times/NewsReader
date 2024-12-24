import chromadb
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext
from llama_index.llms.gemini import Gemini
import os

# 初始化Chroma客户端
chroma_client = chromadb.PersistentClient(path="./src/database/chroma_db")
# chroma_client.delete_collection("news_reader_demo")
collection = chroma_client.get_or_create_collection("news_reader_demo") # 注意替换

# 创建向量存储
vector_store = ChromaVectorStore(chroma_collection=collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# 索引和嵌入
from llama_index.embeddings.voyageai import VoyageEmbedding
model_name = "voyage-3"
voyage_api_key = os.getenv("VOYAGE_API_KEY")
embed_model = VoyageEmbedding(
    model_name=model_name, voyage_api_key=voyage_api_key
)
# 阅读文档
documents = SimpleDirectoryReader("./src/utils/rag/docs").load_data()
# 1 创建索引（首次索引）
# index = VectorStoreIndex.from_documents(
#     documents,
#     show_progress=True,
#     storage_context=storage_context,
#     embed_model=embed_model
# )
# or 2 加载索引
index = VectorStoreIndex.from_vector_store(
    vector_store, storage_context=storage_context,
    embed_model=embed_model
)

# 配置查询引擎 - query
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL")
llm=Gemini(model="models/" + MODEL, api_key=API_KEY)
# 单次提问
# query_engine = index.as_query_engine(
#     chat_mode="condense_plus_context",
#     llm=llm,
#     streaming=True
# )
# response = query_engine.query("这篇文档说了什么? 中文回答")
# response.print_response_stream()
# print(response)


# 配置对话引擎 - chat 多轮对话
from llama_index.core.storage.chat_store import SimpleChatStore
from llama_index.core.memory import ChatMemoryBuffer
chat_store = SimpleChatStore()
chat_memory = ChatMemoryBuffer.from_defaults(
    token_limit=3000, # shape 相似
    chat_store=chat_store,
    chat_store_key="user1",
)
# https://docs.llamaindex.ai/en/stable/examples/chat_engine/chat_engine_repl/
# https://tarzan.blog.csdn.net/article/details/144108655
# https://blog.csdn.net/weixin_40986713/article/details/144510238
chat_engine = index.as_chat_engine(
    chat_mode="condense_plus_context",
    llm=llm,
    memory=chat_memory,
    verbose=False,
    # context_prompt=( # from_defaults https://docs.llamaindex.ai/en/stable/examples/cookbooks/llama3_cookbook_gaudi/#6-adding-chat-history-to-rag-chat-engine
        # "You are a chatbot, able to have normal interactions with the user.\n"
        # "Here are the relevant documents for the context:\n"
        # "{context_str}\n"
        # "Instruction: Use the previous chat history, or the context, to interact and help the user."
    # ),
)
response = chat_engine.chat("这篇文档说了什么? 中文回答") # stream_chat
print(response)
response = chat_engine.chat("小到大的第二种方式是什么?")
print(response)

# 持久化
chat_store.persist(persist_path="chat_store_test.json")
loaded_chat_store = SimpleChatStore.from_persist_path(
    persist_path="chat_store_test.json"
)