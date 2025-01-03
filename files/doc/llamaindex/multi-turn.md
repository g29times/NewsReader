关于多轮对话的关键概念

	理解文档
		原始文档 - 切片 - Node
		https://docs.llamaindex.ai/en/stable/understanding/loading/loading/#splitting-your-documents-into-nodes
	理解嵌入
		https://docs.llamaindex.ai/en/stable/understanding/loading/loading/#adding-embeddings
		To insert a node into a vector index, it should have an embedding.
		可见，嵌入是将文档转为索引的动作
		https://docs.llamaindex.ai/en/stable/examples/embeddings/jinaai_embeddings/
	理解索引 index
		向量索引，摘要索引（list），知识图谱索引
		https://docs.llamaindex.ai/en/stable/module_guides/indexing/index_guide/
		https://docs.llamaindex.ai/en/stable/understanding/indexing/indexing/
	
		
	理解Retrieval：the process of getting something back from somewhere
		将知识和查询进行嵌入，再查找，就是召回
		https://www.anthropic.com/news/contextual-retrieval
	理解 小到大切分
		https://www.llamaindex.ai/blog/evaluating-the-ideal-chunk-size-for-a-rag-system-using-llamaindex-6207e5d3fec5
		https://docs.llamaindex.ai/en/stable/module_guides/querying/retriever/retrievers/#advanced-retrieval-and-search
		https://docs.llamaindex.ai/en/stable/optimizing/advanced_retrieval/advanced_retrieval/#main-advanced-retrieval-strategies
	理解查询 query
		https://docs.llamaindex.ai/en/stable/understanding/querying/querying/
	理解查询重写
		1. 多轮对话改写 见下
		2. *Auto-Retrieval
			https://blog.csdn.net/2401_84208172/article/details/143175290
			https://docs.llamaindex.ai/en/stable/examples/pipeline/query_pipeline/#1-rag-pipeline-with-query-rewriting
	理解 重排序 Reranking
        https://mp.weixin.qq.com/s/XKTvd1jW4Y0AH9w-s2NLVA
        https://docs.llamaindex.ai/en/stable/examples/workflow/rag/
	理解 多轮对话 multi-turn
		https://ywctech.net/ml-ai/langchain-vs-llamaindex-rag-chat/#the-top
		https://docs.llamaindex.ai/en/stable/examples/chat_engine/chat_engine_condense_plus_context/
	理解 记忆 memory 持久化
		https://blog.csdn.net/weixin_40986713/article/details/144510238



	高级：
	理解 CoT ReACT等
		https://ywctech.net/ml-ai/langchain-vs-llamaindex-simple-react/
		https://blog.csdn.net/letsgogo7/article/details/138197137（系列）
		https://blog.csdn.net/Attitude93/article/details/138072340（系列）
	理解 Agentic
		网页爬取 
		LangGraph 知识图谱
			https://ywctech.net/ml-ai/langchain-langgraph-agent-part1/
			https://cloud.tencent.com/developer/article/2375641
		Agents https://blog.csdn.net/Attitude93/article/details/139452945
	理解可观测
		https://zhuanlan.zhihu.com/p/681532023
		https://blog.csdn.net/zhishi0000/article/details/140964285
		https://docs.llamaindex.ai/en/stable/examples/observability/OpenInferenceCallback/
		https://docs.llamaindex.ai/en/stable/examples/cookbooks/oreilly_course_cookbooks/Module-5/Observability/
	理解评测
		https://docs.llamaindex.ai/en/stable/examples/cookbooks/oreilly_course_cookbooks/Module-3/Evaluating_RAG_Systems/
    https://www.llamaindex.ai/blog/evaluating-the-ideal-chunk-size-for-a-rag-system-using-llamaindex-6207e5d3fec5
		
		
# 论文
https://blog.closex.org/posts/1ab991f7
https://blog.csdn.net/u011426236/article/details/136811355
https://zhuanlan.zhihu.com/p/644443386


# 实践
RAG 小到大检索 + 评估 https://zhuanlan.zhihu.com/p/681532023
整合框架 chainlit https://blog.csdn.net/weixin_40986713/article/details/144510238
    https://github.com/Chainlit/chainlit
    https://docs.chainlit.io/integrations/llama-index
多轮对话 https://ywctech.net/ml-ai/langchain-vs-llamaindex-rag-chat/#the-top
    早期
        https://github.com/run-llama/llama_index/discussions/15146
        https://blog.csdn.net/weixin_44826203/article/details/131974846