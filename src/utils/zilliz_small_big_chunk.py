from pymilvus import MilvusClient, DataType

import configparser
from dotenv import load_dotenv
import os

# 从配置文件读取uri
cfp = configparser.RawConfigParser()
cfp.read('src/database/zilliz_config.ini')
milvus_uri = cfp.get('example', 'uri')

# 从.env读取token
load_dotenv()
token = os.getenv('ZILLIZ_MILVUS_KEY')


client = MilvusClient(uri=milvus_uri, token=token)

schema = client.create_schema(
    auto_id=False,
    enable_dynamic_fields=True,
)

# 添加 JSON 字段
schema.add_field(field_name="metadata", datatype=DataType.JSON)
schema.add_field(field_name="pk", datatype=DataType.INT64, is_primary=True)
schema.add_field(field_name="embedding", datatype=DataType.FLOAT_VECTOR, dim=3)

# 创建 Collection

index_params = client.prepare_index_params()

index_params.add_index(
    field_name="embedding",
    index_type="AUTOINDEX",
    metric_type="COSINE"
)

# 使用定义好的 Schema 和索引参数来创建 Collection
client.drop_collection(
    collection_name="my_json_collection"
)
client.create_collection(
    collection_name="my_json_collection",
    schema=schema,
    index_params=index_params
)

# 插入数据
# data = [
#   {
#       "metadata": {"category": "electronics", "price": 99.99, "brand": "BrandA"},
#       "pk": 1,
#       "embedding": [0.12, 0.34, 0.56]
#   },
#   {
#       "metadata": {"category": "home_appliances", "price": 249.99, "brand": "BrandB"},
#       "pk": 2,
#       "embedding": [0.56, 0.78, 0.90]
#   },
#   {
#       "metadata": {"category": "furniture", "price": 399.99, "brand": "BrandC"},
#       "pk": 3,
#       "embedding": [0.91, 0.18, 0.23]
#   }
# ]
# 上下文提示：这是一篇已经分好段的文章，每段的分隔符是 --- 你需要为每段增加上下文，然后连同原段落一起返回，json形式，例如：。。。
# 插入数据 存储前预处理：加上下文，召回方式 1 大小都存 查两次；2 小的进向量 大的进缓存 向量找小 缓存找大
# 适用场景：当用户很发散的问，这个。。。跟哪篇文章有关系。
data = [
  {
      "metadata": {"category": "small", "chunk_id": 1, "text": "BrandA"},
      "pk": 1,
      "embedding": [0.12, 0.34, 0.56]
  },
  {
      "metadata": {"category": "small", "chunk_id": 1, "text": "BrandB"},
      "pk": 2,
      "embedding": [0.56, 0.78, 0.90]
  },
  {
      "metadata": {"category": "big", "chunk_id": 1, "text": "BrandA BrandB"},
      "pk": 3,
      "embedding": [0.91, 0.18, 0.23]
  }
]
# client.insert(
#     collection_name="my_json_collection",
#     data=data
# )

# 1 使用 JSON 字段进行标量过滤搜索和查询
# 过滤查询
# 您可以基于 JSON 属性过滤数据，例如匹配特定值或检查某个数字是否在特定范围内。
filter = 'metadata["category"] == "electronics" and metadata["price"] < 150'

res = client.query(
    collection_name="my_json_collection",
    filter=filter,
    output_fields=["metadata"]
)

print(res)

# Output
# data: ["{'metadata': {'category': 'electronics', 'price': 99.99, 'brand': 'BrandA'}, 'pk': 1}"] 

# 2 向量搜索与 JSON 过滤结合
filter = 'metadata["brand"] == "BrandA"'

res = client.search(
    collection_name="my_json_collection",
    data=[[0.3, -0.6, 0.1]],
    limit=5,
    search_params={"params": {"nprobe": 10}},
    output_fields=["metadata"],
    filter=filter
)

print(res)

# Output
# data: ["[{'id': 1, 'distance': -0.2479381263256073, 'entity': {'metadata': {'category': 'electronics', 'price': 99.99, 'brand': 'BrandA'}}}]"] 