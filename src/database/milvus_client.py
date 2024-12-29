from pymilvus import MilvusClient

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import configparser
from dotenv import load_dotenv

# Docs
# 版本 https://milvus.io/api-reference/pymilvus/v2.5.x/About.md
# 增删改查 https://zhuanlan.zhihu.com/p/617972545
# https://blog.csdn.net/weixin_41338279/article/details/144185954
# 使用 https://milvus.io/api-reference/pymilvus/v2.4.x/MilvusClient/Vector/get.md
# 原理 https://milvus.io/docs/metric.md?tab=floating
# 原理 https://milvus.io/docs/index.md?tab=sparse
# 使用模型 https://milvus.io/docs/embed-with-voyage.md
# 接入三方 https://docs.llamaindex.ai/en/stable/examples/vector_stores/MilvusHybridIndexDemo/?h=milvus
# 云服务器 https://docs.zilliz.com.cn/reference/restful/query-v2?_highlight=%E6%9F%A5%E8%AF%A2

from pymilvus.model.dense import VoyageEmbeddingFunction
from pymilvus.model.dense import JinaEmbeddingFunction
from pymilvus.model.dense import CohereEmbeddingFunction
from pymilvus import (
    utility,
    FieldSchema, CollectionSchema, DataType,
    Collection, AnnSearchRequest, RRFRanker, connections, WeightedRanker
)

class Milvus:

    def __init__(self, embedding_fn=None, client=None):
        # 从配置文件读取uri
        cfp = configparser.RawConfigParser()
        cfp.read('src/database/zilliz_config.ini')
        milvus_uri = cfp.get('example', 'uri')

        # 从.env读取token
        load_dotenv()
        token = os.getenv('ZILLIZ_MILVUS_KEY')

        # 优先使用传入的client，否则尝试连接云服务，如果配置文件不存在则使用本地数据库
        if client is not None:
            self.client = client
        else:
            try:
                self.client = MilvusClient(uri=milvus_uri, token=token)
                print(f"Connected to Zilliz Cloud: {milvus_uri}")
            except Exception as e:
                print(f"Failed to connect to Zilliz Cloud: {str(e)}, using local database instead")
                self.client = MilvusClient("src/database/milvus_demo.db")

        if embedding_fn is None:
            embedding_fn = VoyageEmbeddingFunction(
                model_name="voyage-3", # Defaults to `voyage-2`
                api_key="pa-ReOQxAJwGywtO4bfpQVnjyJv5uHsqnBTC0ym8DE73Yg"
            )
        self.embedding_fn = embedding_fn

    # 1 Create db self.embedding_fn.dim
    def create_collection(self, collection_name, dim=1024, schema=None, index_params=None):
        if self.client.has_collection(collection_name=collection_name):
            self.client.drop_collection(collection_name=collection_name)
        self.client.create_collection(
            collection_name=collection_name,
            dimension=dim,
            schema=schema,
            index_params=index_params
        )
        print("create_db with dimension", dim)

    # 2 Encode text
    def encode_documents(self, docs):
        docs_embeddings = self.embedding_fn.encode_documents(docs)
        print("Docs:", len(docs))
        # print("Docs Dim:", self.embedding_fn.dim, docs_embeddings[0].shape)
        return docs_embeddings
    
    def encode_query(self, query):
        query_vectors = self.embedding_fn.encode_queries(query)
        # print("Query Dim:", self.embedding_fn.dim, query_vectors[0].shape)
        return query_vectors

    # 3 Build Data 
    # Each entity has id, vector representation, raw text, and a subject label to filtering metadata.
    def build_data(self, docs, docs_embeddings):
        data = [
            {"id": i, "vector": docs_embeddings[i], "text": docs[i], "subject": "history"}
            for i in range(len(docs_embeddings))
        ]
        return data

    # 4 Update Insert Data
    def upsert_data(self, collection_name, data):
        res = self.client.upsert(collection_name=collection_name, data=data)
        print(res)

    # Public方法 Update Docs 聚合方法 subject可用于后续partition
    def upsert_docs(self, collection_name, docs, subject="criticism", author="Cao Xue Qin"):
        docs_embeddings = self.encode_documents(docs)
        data = [
            {"id": i, "vector": docs_embeddings[i], "text": docs[i], "subject": subject, "metadata": {"author": author}}
            for i in range(len(docs_embeddings))
        ]
        res = self.client.upsert(collection_name=collection_name, data=data)
        print(res)

    # Public方法
    def get_by_ids(self, collection_name, ids, output_fields=["text"]):
        res = self.client.get(
            collection_name=collection_name,
            output_fields=output_fields,
            ids=ids
        )
        return res

    # Public方法 Semantic Search client.search()是milvus 内部逻辑 默认使用cosine similarity
    def search(self, collection_name, query, limit=3, output_fields=["text"]):
        query_vectors = self.encode_query(query)
        res = self.client.search(
            collection_name=collection_name,  # target collection
            data=query_vectors,  # query vectors
            limit=limit,  # number of returned entities
            output_fields=output_fields,  # specifies fields to be returned
        )
        return res

    # Public方法 delete items
    def delete_items(self, collection_name, ids):
        res = self.client.delete(collection_name=collection_name, ids=ids)
        print(res)

    # Public方法 delete collection
    def delete_collection(self, collection_name):
        res = self.client.drop_collection(collection_name=collection_name)
        print(res)

    # Public方法 count collection
    def count_collection(self, collection_name):
        return self.get_collection(collection_name).num_entities

    def get_collection(self, collection_name):
        return Collection(collection_name)

# main
if __name__ == "__main__":
    milvus = Milvus()
    collection_name = "rag_basic"
    print(milvus.search(collection_name, ["简易 RAG 管道中的 query_engine 使用的是什么算法？"]))
    collection_name = "rag_context"
    print(milvus.search(collection_name, ["简易 RAG 管道中的 query_engine 使用的是什么算法？"]))