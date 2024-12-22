# https://docs.llamaindex.ai/en/stable/examples/cookbooks/llama3_cookbook_groq/#4-text-to-sql
from sqlalchemy import (
    create_engine,
)
engine = create_engine("sqlite:///./src/database/articles.db", echo=True)

from llama_index.core import SQLDatabase
sql_database = SQLDatabase(engine)

import os
from llama_index.embeddings.voyageai import VoyageEmbedding
model_name = "voyage-3"
voyage_api_key = os.getenv("VOYAGE_API_KEY")
embed_model = VoyageEmbedding(
    model_name=model_name, voyage_api_key=voyage_api_key
)

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL")
from llama_index.llms.gemini import Gemini
from llama_index.core.indices.struct_store import NLSQLTableQueryEngine
query_engine = NLSQLTableQueryEngine(
    sql_database=sql_database,
    tables=["articles"],
    llm=Gemini(model="models/" + MODEL, api_key=API_KEY),
    embed_model=embed_model
)

# 问题：打印数据库日志 内部查询语句较多 效率低
response = query_engine.query("What are some articles? Limit it to 5.")
print(response)