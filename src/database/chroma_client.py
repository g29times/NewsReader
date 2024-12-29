import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import rag.voyager as voyager

# docs 集成Voyage后，效果不如milvus，原因不明
# https://docs.trychroma.com/guides#filtering-by-document-contents
# https://docs.trychroma.com/guides#changing-the-distance-function
# https://www.datacamp.com/tutorial/chromadb-tutorial-step-by-step-guide
# https://docs.trychroma.com/production/chroma-server/client-server-mode
# https://docs.trychroma.com/integrations/chroma-integrations
# API手册 https://zhuanlan.zhihu.com/p/680661442

# chroma的dimension维度将由第一个入库的数据决定
chroma_client = chromadb.Client()

class MyEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        return voyager.get_doc_embeddings(documents=input)

my_embed_func = MyEmbeddingFunction()
# documents=["This is a document about pineapple"]
# embeddings = my_embed_func(documents)
# print(embeddings)

# 已完成embedding 存储接入
collection_name = "my_collection"
# if chroma_client.get_collection(name=collection_name, embedding_function=my_embed_func):
#     chroma_client.delete_collection(name=collection_name, embedding_function=my_embed_func)
collection = chroma_client.get_or_create_collection(name=collection_name, 
                                                    embedding_function=my_embed_func,
                                                    metadata={"hnsw:space": "cosine"})
# https://docs.trychroma.com/docs/collections/configure
# cosine 0.11329090595245361, 0.11687445640563965, 0.11940479278564453, 0.13816648721694946
# l2     0.2265823781490326, 0.23374910652637482, 0.23881018161773682, 0.2763333022594452
# ip     0.11329144239425659, 0.11687445640563965, 0.11940491199493408, 0.1381669044494629
# 增，改
collection.upsert(
    documents=['This is a document about pineapple',
        'This is a document about oranges',
        ],
    metadatas = [{"tag": "chroma"},{"tag": "chroma"},
 ],
    ids=['id1', 'id2', 
    ]
)
print(collection.count())
print(collection.get(where={'tag': 'chroma'}))

query = ["元春和迎春的关系如何", 'This is a query document about florida']
# 查询
results = collection.query(
    query_texts=[query[0]], # Chroma will embed this for you
    n_results=3, # how many results to return
    # A WhereDocument type dict used to filter by the documents. E.g. `{$contains: {"text": "hello"}}` 
    # https://docs.trychroma.com/guides#filtering-by-document-contents
    # where_document={ "$and": [{"$contains":"春"}, {"$not_contains":"李"}] }
)
# 贾迎春 贾探春 李纨 集成Voyage后，效果不如milvus
print(results)

# 删
# 删表
# client.delete_collection(name="my_collection")
# 删数据
# collection.delete(
#     ids=["1"],
#     where={"author": {"$eq": "jack"}}, # 表示 metadata 中 "author" 字段值等于 "jack" 的文档
#     where_document={"$contains": "john"}, # 表示文本内容中包含 "john" 的文档
# )