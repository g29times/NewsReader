这是理解 llamaindex 关键概念，搭建RAG的pipeline和workflow的经验手册

# basic
https://docs.llamaindex.ai/en/stable/optimizing/basic_strategies/basic_strategies/
Prompt Engineering

Embeddings
		https://docs.llamaindex.ai/en/stable/examples/finetuning/embeddings/finetune_embedding/
		https://blog.csdn.net/m0_59614665/article/details/144290464
		https://luxiangdong.com/2023/09/27/ftembedding/
		https://zhuanlan.zhihu.com/p/680517874
		https://www.datalearner.com/blog/1051721552379699
Chunk Sizes

Hybrid Search

Metadata Filters
Document/Node Usage
Multi-Tenancy RAG

# pipeline
	Load - index - store - query

index
https://docs.llamaindex.ai/en/stable/understanding/indexing/indexing/#top-k-retrieval


# workflow

## Basic LLM chat flow
    (Cohere) Retrieve - Prompt Aug - Generate
    https://mmbiz.qpic.cn/mmbiz_png/VtGaZVqpDn2r9ydkre32F1vPQjyyUlUWibDqpiaMdMTfJWFEYNUjOpOOLiaORw4mh3Aw4cibGVmtzyIhdHibJKOAuLg/640?wx_fmt=png&from=appmsg&tp=wxpic&wxfrom=5&wx_lazy=1&wx_co=1
## RAG flow
    voyageai https://www.voyageai.com/
    Embedding - vectorDB - Reranker - relevant files - LLM - response
		
## RAG + Reranking flow
    https://docs.llamaindex.ai/en/stable/examples/workflow/rag/
    RAG + Reranking consists of some clearly defined steps
        1 Indexing data, creating an index
        2 Using that index + a query to retrieve relevant text chunks
        3 Rerank the text retrieved text chunks using the original query
        4 Synthesizing a final response
## observability
	Verbose mode
	https://docs.llamaindex.ai/en/stable/understanding/workflows/observability/#verbose-mode