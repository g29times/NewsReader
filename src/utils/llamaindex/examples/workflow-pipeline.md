这是一篇关于pipeline和workflow经验的手册

# pipeline
    
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