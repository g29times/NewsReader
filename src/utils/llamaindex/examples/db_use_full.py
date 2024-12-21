from __future__ import absolute_import

# https://docs.llamaindex.ai/en/stable/examples/data_connectors/DatabaseReaderDemo/
# My OpenAI Key
import os
os.environ["OPENAI_API_KEY"] = ""

from sqlalchemy import (
    create_engine,
)
engine = create_engine("sqlite:///./src/database/articles.db")

from llama_index.core import SQLDatabase
sql_database = SQLDatabase(engine)

from llama_index.readers.database import DatabaseReader
from llama_index.core import VectorStoreIndex

# Initialize DatabaseReader object with the following parameters:
db = DatabaseReader(
    sql_database=sql_database,
    # engine=engine,
    # uri="<Connection URI>",  # Optional: Connection URI
    # scheme="sqlite",  # Database Scheme
    # host="localhost",  # Database Host
    # port="5432",  # Database Port
    # user="postgres",  # Database User
    # password="FakeExamplePassword",  # Database Password
    # dbname="postgres",  # Database Name
)

### DatabaseReader class ###
# db is an instance of DatabaseReader:
print("type(db): ", type(db))
# DatabaseReader available method:
print(type(db.load_data))

### SQLDatabase class ###
# db.sql is an instance of SQLDatabase:
print("type(db.sql_database): ", type(db.sql_database))
# SQLDatabase available methods:
print(type(db.sql_database.from_uri))
print(type(db.sql_database.get_single_table_info))
print(type(db.sql_database.get_table_columns))
print(type(db.sql_database.get_usable_table_names))
print(type(db.sql_database.insert_into_table))
print(type(db.sql_database.run_sql))
# SQLDatabase available properties:
print(type(db.sql_database.dialect))
print(type(db.sql_database.engine))

### Testing DatabaseReader
### from SQLDatabase, SQLAlchemy engine and Database URI:

# From SQLDatabase instance:
print("type(db.sql_database): ", type(db.sql_database))
db_from_sql_database = DatabaseReader(sql_database=db.sql_database)
print(type(db_from_sql_database))

# From SQLAlchemy engine:
print("type(db.sql_database.engine): ", type(db.sql_database.engine))
db_from_engine = DatabaseReader(engine=db.sql_database.engine)
print(type(db_from_engine))

# From Database URI:(Optional)
# print("type(db.uri): ", type(db.uri))
# db_from_uri = DatabaseReader(uri=db.uri)
# print(type(db_from_uri))

# The below SQL Query example returns a list values of each row
# with concatenated text from the name and age columns
# from the users table where the age is greater than or equal to 18
query = f"""
    SELECT id, title FROM articles LIMIT 5
    """

# Please refer to llama_index.utilities.sql_wrapper
# SQLDatabase.run_sql method
texts = db.sql_database.run_sql(command=query)
# Display type(texts) and texts
# type(texts) must return 
print("type(texts): ", type(texts))
# Documents must return a list of Tuple objects
print(texts)

# Please refer to llama_index.readers.database.DatabaseReader.load_data
# DatabaseReader.load_data method
documents = db.load_data(query=query)
# Display type(documents) and documents
# type(documents) must return 
print("type(documents): ", type(documents))
# Documents must return a list of Document objects
print(documents)



# 初始化Chroma客户端
import chromadb
chroma_client = chromadb.PersistentClient(path="./src/database/chroma_db")
collection = chroma_client.get_or_create_collection("articles")

# 创建向量存储
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext
vector_store = ChromaVectorStore(chroma_collection=collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# 索引和嵌入
from llama_index.embeddings.voyageai import VoyageEmbedding
model_name = "voyage-3"
voyage_api_key = os.getenv("VOYAGE_API_KEY")
embed_model = VoyageEmbedding(
    model_name=model_name, voyage_api_key=voyage_api_key
)
index = VectorStoreIndex.from_documents(
    documents,
    show_progress=True,
    storage_context=storage_context,
    embed_model=embed_model
)

# 配置查询引擎
from llama_index.llms.gemini import Gemini
API_KEY = os.getenv("GEMINI_API_KEY1")
MODEL = "gemini-1.5-flash-latest"
query_engine = index.as_query_engine(
    llm=Gemini(model="models/" + MODEL, api_key=API_KEY),
    streaming=True
)

# 提问
response = query_engine.query("What are these documents about?")
print(response)