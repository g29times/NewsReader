import os
import sys
import time

from sqlalchemy import Connection
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import configparser
from dotenv import load_dotenv
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

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
# https://blog.csdn.net/luxinfeng666/article/details/131506186
# https://blog.csdn.net/csdn_xmj/article/details/143771359
# https://docs.zilliz.com.cn/docs/get-and-scalar-query#count-entities

from pymilvus.model.dense import VoyageEmbeddingFunction
from pymilvus.model.dense import JinaEmbeddingFunction
from pymilvus.model.dense import CohereEmbeddingFunction
from pymilvus import (
    MilvusClient,
    connections,
    utility,
    FieldSchema, CollectionSchema, DataType,
    Collection, AnnSearchRequest, RRFRanker, WeightedRanker
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
            retry_count = 0
            max_retries = 3
            while retry_count < max_retries:
                try:
                    self.client = MilvusClient(uri=milvus_uri, token=token)
                    log.info(f"Connected to Zilliz Cloud: {milvus_uri}")
                    break
                except Exception as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        log.warning(f"Failed to connect to Zilliz Cloud (attempt {retry_count}/{max_retries}): {str(e)}")
                        log.info(f"Retrying in 10 seconds...")
                        time.sleep(10)
                    else:
                        log.warning(f"Failed to connect to Zilliz Cloud after {max_retries} attempts, using local database instead")
                        self.client = MilvusClient("src/database/milvus_local.db")

        if embedding_fn is None:
            embedding_fn = VoyageEmbeddingFunction(
                model_name="voyage-3", # Defaults to `voyage-2`
                api_key=os.getenv('VOYAGE_API_KEY')
            )
        self.embedding_fn = embedding_fn

    def get_client(self):
        return self.client
# ------------------------------ collection level 操作 增删改查 ------------------------------
    
    # Create db self.embedding_fn.dim
    def create_collection(self, collection_name, dim=1024, schema=None, index_params=None):
        if self.has_collection(collection_name=collection_name):
            return# self.client.drop_collection(collection_name=collection_name)
        self.client.create_collection(
            collection_name=collection_name,
            dimension=int(os.getenv('EMBEDDING_DIM', dim)),
            schema=schema,
            index_params=index_params # 默认使用cosine similarity
        )
        log.info("create_db: ", collection_name)

    def has_collection(self, collection_name):
        return self.client.has_collection(collection_name=collection_name)

    def describe_collection(self, collection_name):
        return self.client.describe_collection(collection_name=collection_name)

    # milvus.client.load_collection(
    #     collection_name=collection_name
    # )
    # res = milvus.client.get_load_state(
    #     collection_name=collection_name
    # )
    # print(res.items)
    # res = milvus.client.describe_collection(
    #     collection_name=collection_name
    # )
    # print(res)

    # 获取Collection各类属性
    # from pymilvus import Collection
    # collection = Collection("book")  # Get an existing collection.
    # collection.schema                # Return the schema.CollectionSchema of the collection.
    # collection.description           # Return the description of the collection.
    # collection.name                  # Return the name of the collection.
    # collection.is_empty              # Return the boolean value that indicates if the collection is empty.
    # collection.num_entities          # Return the number of entities in the collection.
    # collection.primary_field         # Return the schema.FieldSchema of the primary key field.
    # collection.partitions            # Return the list[Partition] object.
    # collection.indexes               # Return the list[Index] object.
    # collection.properties		# Return the expiration time of data in the collection.

    # 重命名Collection
    # utility.rename_collection("old_collection", "new_collection") # Output: True

    # 修改Collection属性
    # collection.set_properties(properties={"collection.ttl.seconds": 1800})

    # delete collection
    def delete_collection(self, collection_name):
        res = self.client.drop_collection(collection_name=collection_name)
        # log.info("delete_collection: ", res)

# ------------------------------ collection 内的元素（document） level 操作 增删改查 ------------------------------

    # 将文本转换为milvus格式的向量表示 Each entity has id, vector representation, raw text, and a subject label to filtering metadata.
    # TODO build_data 应改为回调，由业务方决定
    def build_data(self, docs, docs_embeddings, subjects, metadatas):
        data = [
            {"id": i, "embedding": docs_embeddings[i], "text": docs[i], "subject": subjects[i], "metadata": metadatas[i]}
            for i in range(len(docs_embeddings))
        ]
        return data

    # Embed 语句
    def encode_query(self, query):
        query_vectors = self.embedding_fn.encode_queries(query)
        return query_vectors

    # Embed 文档
    def encode_documents(self, docs):
        docs_embeddings = self.embedding_fn.encode_documents(docs)
        log.info("encode_documents: ", len(docs))
        return docs_embeddings

    # Add、Update Data (入参data必须是向量表示)
    async def upsert_data(self, collection_name, data):
        res = self.client.upsert(collection_name=collection_name, data=data)
        log.info(f"upsert_id: {data[0].get('id')}")
        return res

    # Update Docs 聚合方法 subject可用于后续partition
    async def upsert_docs(self, collection_name, docs, embeddings, metadatas):
        if not self.has_collection(collection_name=collection_name):
            self.create_collection(collection_name)
        if not embeddings:
            docs_embeddings = self.encode_documents(docs)
        else:
            docs_embeddings = embeddings
        if not metadatas:
            metadatas = {"subjects": ["article"] * len(docs), "authors": [""] * len(docs)}
        data = self.build_data(docs, docs_embeddings, metadatas.get("subjects"), metadatas.get("authors"))
        res = await self.upsert_data(collection_name=collection_name, data=data)
        log.info("upsert_docs: ", res)
        return res

    # （上游暂时没用到）
    def get_by_ids(self, collection_name, ids, output_fields=["text"]):
        res = self.client.get(
            collection_name=collection_name,
            output_fields=output_fields,
            ids=ids
        )
        return res

    # Semantic Search
    def search(self, collection_name, query, limit=5, output_fields=["text"], search_params={}, filter=""):
        query_vectors = self.encode_query(query)
        res = self.client.search(
            collection_name=collection_name,  # target collection
            data=query_vectors,  # query vectors
            limit=limit,  # number of returned entities
            output_fields=output_fields,  # specifies fields to be returned
            search_params=search_params,
            filter=filter
        )
        return res

    # https://docs.zilliz.com.cn/docs/get-and-scalar-query#count-entities
    def count_items(self, collection_name):
        res = self.client.query(
            collection_name=collection_name,
            output_fields=["count(*)"]
        )
        return res[0]["count(*)"]

    # delete items
    def delete_items(self, collection_name, ids, filter):
        """此id是指vector db的id"""
        if ids:
            res = self.client.delete(collection_name=collection_name, ids=ids)
            log.info("delete_items: ", res)
        else:
            res = self.client.delete(collection_name=collection_name, filter=filter)
            log.info("delete_items: ", res)

# main
if __name__ == "__main__":
    milvus = Milvus()
    collection_name = "rag_basic"
    # milvus.create_collection(collection_name=collection_name, dim=1024, schema=None, index_params=None)
    count_items = milvus.count_items(collection_name)
    print(count_items)

    # print(milvus.search(collection_name, ["简易 RAG 管道中的 query_engine 使用的是什么算法？"]))
    # collection_name = "rag_context"
    # print(milvus.search(collection_name, ["简易 RAG 管道中的 query_engine 使用的是什么算法？"]))