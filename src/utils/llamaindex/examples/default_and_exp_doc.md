# 关于LLAMAINDEX各种默认值和经验的文档

# 默认值
## 1. 文档切分默认值
The default chunk size is 1024, while the default chunk overlap is 20.
https://docs.llamaindex.ai/en/stable/optimizing/basic_strategies/basic_strategies/#chunk-sizes

## 2. 嵌入默认值
By default LlamaIndex uses text-embedding-ada-002
https://docs.llamaindex.ai/en/stable/understanding/indexing/indexing/

dimension=?
https://docs.llamaindex.ai/en/stable/module_guides/indexing/vector_store_index/#using-vectorstoreindex

## 3. 索引默认值
By default, the VectorStoreIndex will generate and insert vectors in batches of 2048 nodes.
https://docs.llamaindex.ai/en/stable/module_guides/indexing/vector_store_index/#using-vectorstoreindex

## 4 查询默认值
similarity_top_k=2
https://docs.llamaindex.ai/en/stable/examples/cookbooks/contextual_retrieval/#set-similarity_top_k



# 经验手册
## 基本策略（Prompt Embedding Chunk Search Metadata）
https://docs.llamaindex.ai/en/stable/optimizing/basic_strategies/basic_strategies/#chunk-sizes

## 评估 RAG 系统的理想块大小
https://www.llamaindex.ai/blog/evaluating-the-ideal-chunk-size-for-a-rag-system-using-llamaindex-6207e5d3fec5

## 引入上下文检索
https://www.anthropic.com/news/contextual-retrieval