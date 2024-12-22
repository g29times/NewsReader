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

# 配置查询引擎
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL")
query_engine = index.as_query_engine(
    llm=Gemini(model="models/" + MODEL, api_key=API_KEY),
    streaming=True
)

# 提问单篇
response = query_engine.query("What is the document about?")
response.print_response_stream()