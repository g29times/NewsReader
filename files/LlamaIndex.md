# LlamaIndex 集成文档
1. 入门：您现在所在的部分。我们可以让您从对 LlamaIndex 和 LLM 一无所知开始。安装库，用五行代码编写您的第一个演示，了解有关LLM 应用程序的高级概念的更多信息，然后了解如何自定义五行示例以满足您的需求。
https://docs.llamaindex.ai/en/stable/
https://docs.llamaindex.ai/en/stable/getting_started/starter_example/

2. 学习：完成入门部分后，下一步就是学习这个部分。在一系列简短的教程中，我们将引导您完成构建生产 LlamaIndex 应用程序的每个阶段，并帮助您逐步掌握库和 LLM 的一般概念。
https://docs.llamaindex.ai/en/stable/understanding/using_llms/using_llms/
https://docs.llamaindex.ai/en/stable/understanding/rag/

3. 用例：如果您是一名开发人员，想要弄清楚 LlamaIndex 是否适合您的用例，我们会概述您可以构建的事物类型。Structured Data Extraction、Query Engines、Chat Engines、Agents
https://docs.llamaindex.ai/en/stable/use_cases/

4. 示例：我们为几乎所有功能提供了丰富的笔记本示例。探索这些示例以查找和了解有关 LlamaIndex 的新知识。
https://docs.llamaindex.ai/en/stable/examples/
https://docs.llamaindex.ai/en/stable/examples/llama_hub/llama_hub/#using-a-data-loader

5. 组件指南：按照与我们的学习部分构建 LLM 应用程序的相同顺序排列，这些是针对 LlamaIndex 的各个组件及其使用方法的全面的、低级指南。
https://docs.llamaindex.ai/en/stable/module_guides/

6. 高级主题：已经有一个可以运行的 LlamaIndex 应用程序，并希望进一步完善它？我们的高级部分将引导您完成您应该尝试优化的首要事项，例如您的嵌入模型和块大小，以及逐步更复杂和更微妙的自定义，一直到微调您的模型。
https://docs.llamaindex.ai/en/stable/optimizing/production_rag/

7. API文档
https://docs.llamaindex.ai/en/stable/api_reference/

## 1. 概述
LlamaIndex是一个强大的数据框架，用于构建LLM应用。在我们的NewsReader项目中，我们主要使用它来实现RAG（检索增强生成）功能。
## Important: OpenAI Environment Setup
By default, we use the OpenAI gpt-3.5-turbo model for text generation and text-embedding-ada-002 for retrieval and embeddings. In order to use this, you must have an OPENAI_API_KEY set up as an environment variable. 

## 2. 主要组件
### 依赖汇总
pip install llama-index
pip install llama-index-readers-database
pip install llama-index-vector-stores-chroma
pip install llama-index-embeddings-voyageai
pip install llama-index-llms-gemini
### 2.1 数据加载
https://docs.llamaindex.ai/en/stable/understanding/loading/loading/
```python
pip install llama-index
from llama_index.core import Document
# 1 直接创建文档，您可以直接使用 Document。
doc = Document(text="text")

# 2 加载自文件夹
https://docs.llamaindex.ai/en/stable/understanding/loading/llamahub/
https://docs.llamaindex.ai/en/stable/examples/data_connectors/simple_directory_reader/
from llama_index.core import SimpleDirectoryReader
documents = SimpleDirectoryReader("./data").load_data()

# 3 加载自数据库
https://llamahub.ai/l/readers/llama-index-readers-database
pip install llama-index-readers-database
from llama_index.readers.database import DatabaseReader
reader = DatabaseReader(
    sql_database="<SQLDatabase Object>",  # Optional: SQLDatabase object
    engine="<SQLAlchemy Engine Object>",  # Optional: SQLAlchemy Engine object
    uri="<Connection URI>",  # Optional: Connection URI
    scheme="postgresql",  # Optional: Scheme
    host="localhost",  # Optional: Host
    port="5432",  # Optional: Port
    user="<Username>",  # Optional: Username
    password="<Password>",  # Optional: Password
    dbname="<Database Name>",  # Optional: Database Name
)
documents = reader.load_data(
    query="<SQL Query>"  # SQL query parameter to filter tables and rows
)

# 4 加载网络
pip install llama-index-readers-google
from llama_index.readers.google import GoogleDocsReader
loader = GoogleDocsReader()
documents = loader.load_data(document_ids=[...])

# 5 加载网页
pip install llama-index-readers-web
from llama_index.core import download_loader
from llama_index.readers.web import BeautifulSoupWebReader
BeautifulSoupWebReader = download_loader("BeautifulSoupWebReader")
loader = BeautifulSoupWebReader()
documents = loader.load_data(urls=["http://example.com"])
```

### 2.2 数据转换（索引（分块、提取元数据）和嵌入）
#### 索引
##### 拆分
[Document - Node 文本块(Chunk)] -> Index
###### High-level API（入门 底层处理分块）
from llama_index.core import VectorStoreIndex
vector_index = VectorStoreIndex.from_documents(documents)
###### Low-level API（自定义文本分割器）
TODO
##### 向量索引 (ChromaDB完整示例)
https://docs.llamaindex.ai/en/stable/api_reference/storage/vector_store/chroma/
pip install llama-index-vector-stores-chroma
```python
pip install chromadb
import chromadb
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext
# 初始化Chroma客户端
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection("news_reader")

# 创建向量存储
vector_store = ChromaVectorStore(chroma_collection=collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# 1 创建索引（首次索引）
# 加载文档
documents = SimpleDirectoryReader("./data").load_data()
index = VectorStoreIndex.from_documents(
    documents,
    show_progress=True,
    storage_context=storage_context
)
# or 2 加载索引
index = VectorStoreIndex.from_vector_store(
    vector_store, storage_context=storage_context
)

# 配置查询引擎
query_engine = index.as_query_engine()
response = query_engine.query("What is the document about?")
print(response)
```
##### 摘要索引(链式)
##### 树索引
##### 关键词表索引
TODO https://mp.weixin.qq.com/s/8_yJgADQfnaWByhHmlwy2A
#### 嵌入
易
https://docs.llamaindex.ai/en/stable/examples/embeddings/voyageai/
``` python
pip install llama-index-embeddings-voyageai
from llama_index.embeddings.voyageai import VoyageEmbedding
model_name = "voyage-3"
voyage_api_key = os.getenv("VOYAGE_API_KEY")
embed_model = VoyageEmbedding(
    model_name=model_name, voyage_api_key=voyage_api_key
)
embeddings = embed_model.get_query_embedding("What is llamaindex?")
```
难
https://docs.llamaindex.ai/en/stable/examples/embeddings/jinaai_embeddings/
https://docs.llamaindex.ai/en/stable/examples/embeddings/custom_embeddings/
https://docs.llamaindex.ai/en/stable/module_guides/models/embeddings/

### 2.3 存储索引
index.storage_context.persist(persist_dir="<persist_dir>")
#### 加载持久索引
from llama_index.core import StorageContext, load_index_from_storage
storage_context = StorageContext.from_defaults(persist_dir="<persist_dir>")
index = load_index_from_storage(storage_context)
#### 前面的向量索引也会存储到数据库里

### 2.4 查询引擎
#### 入门
query_engine = index.as_query_engine()
response = query_engine.query(
    "Write a poem about a magic backpack"
)
print(response)
#### 高级
- 检索
- 后处理
- 响应合成
##### 使用GEMINI查询
https://docs.llamaindex.ai/en/stable/api_reference/llms/gemini/
pip install llama-index-llms-gemini
```python
from llama_index import VectorStoreIndex
from llama_index.llms.gemini import Gemini
# 创建索引
index = VectorStoreIndex.from_documents(
    documents,
    show_progress=True,
    storage_context=storage_context
)
# 配置查询引擎
query_engine = index.as_query_engine(
    llm=Gemini(model="models/gemini-1.5-flash-latest", api_key="YOUR_API_KEY"),
    streaming=True
)
# 执行查询
response = query_engine.query("问题")
print(response)
```
#### 进阶查询
工作流 TODO
    TEXT2SQL
        https://medium.com/dataherald/how-to-connect-llm-to-sql-database-with-llamaindex-fae0e54de97c
        https://docs.llamaindex.ai/en/stable/examples/cookbooks/llama3_cookbook_groq/#4-text-to-sql
代理 TODO

## 3. 项目集成

### 3.1 依赖
```
llama-index>=0.12.7
chromadb>=0.5.23
google-generativeai>=0.8.3
```

### 3.2 配置
- 确保设置了必要的环境变量（如Google API密钥）
- 创建持久化存储目录
- 配置日志级别

### 3.3 使用流程
1. 初始化向量存储
2. 加载并处理文档
3. 创建索引
4. 配置查询引擎
5. 执行查询并处理响应

## 4. 性能优化
- 使用批量处理进行文档嵌入
- 实现缓存机制
- 优化文档分块策略
- 使用流式响应

## 5. 注意事项
- 定期维护向量数据库
- 处理大型文档时注意内存使用
- 实现错误处理和重试机制
- 监控API使用情况