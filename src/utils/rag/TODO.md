# 已实现 RAG基本管道
我们之前已经在 @rag_service.py 实现了 
- db 存储
- 文档切分
- 向量索引
- 查询
- LLM对话

# 未实现
在新文件 rag_service_context.py 里实现，不要污染原有代码
- 1 上下文黄金块 'golden chunk' 切片方法
- 2 bm25（自己实现，不用es）
- 3 融合
- 4 rerank（使用JINA接口）

主要功能还差：1 做笔记 2 笔记反向生成文章
1 看debug日志，retriver返回的信息只有100字符，不知是不是切片的问题
2 Agent模型 - 让大模型在后台自己决定是否RAG，而不是给用户一个RAG - Agent
	场景1 用户不选择知识
		1.1聊与知识无关的问题 - 如：今天天气怎么样
		1.2与知识有关的问题   - 如：JINA最近有什么新研究？
			- 先RAG，然后大模型判断相关程度，如果很低，说明库里没有资料
	2 用户有勾选
		2.1与知识无关的问题 如：今天天气怎么样 - 大模型自己判断无关性
		与知识有关的问题 如：
			2.2聚焦：JINA最近有什么新研究？同1.2
			2.3发散：这几篇文章讲了什么？不做RAG，直接用大模型合并回答
3 配合2，落实5级提示词模板
4 问题：llamaindex文 ：engine 和 retriver 的召回区别？
将所有标题和摘要 压缩为一个新的向量 加入每次的查询
基于项目的横切，是否提供通用知识库？


# 整体流程
## 基本对话
优势：流程轻便简单
问题：
    1 LLM不具备领域知识
    For an AI model to be useful in specific contexts, it often needs access to background knowledge. For example, customer support chatbots need knowledge about the specific business they're being used for, and legal analyst bots need to know about a vast array of past cases.
    2 如果传文件，会话窗口大小限制
    For larger knowledge bases that don't fit within the context window, RAG is the typical solution. RAG works by preprocessing a knowledge base using the following steps:
    Break down the knowledge base (the “corpus” of documents) into smaller chunks of text, usually no more than a few hundred tokens;
    Use an embedding model to convert these chunks into vector embeddings that encode meaning;
    Store these embeddings in a vector database that allows for searching by semantic similarity.

## 优化：基本RAG
优势：扩展性
At runtime, when a user inputs a query to the model, the vector database is used to find the most relevant chunks based on semantic similarity to the query. Then, the most relevant chunks are added to the prompt sent to the generative model.
问题：不精确
While embedding models excel at capturing semantic relationships, they can miss crucial exact matches. Fortunately, there’s an older technique that can assist in these situations. BM25 (Best Matching 25) is a ranking function that uses lexical matching to find precise word or phrase matches. It's particularly effective for queries that include unique identifiers or technical terms.

## 优化：向量语义 + BM25精确
优势：
RAG solutions can more accurately retrieve the most applicable chunks by combining the embeddings and BM25 techniques using the following steps:

Break down the knowledge base (the "corpus" of documents) into smaller chunks of text, usually no more than a few hundred tokens;
Create TF-IDF encodings and semantic embeddings for these chunks;
Use BM25 to find top chunks based on exact matches;
Use embeddings to find top chunks based on semantic similarity;
Combine and deduplicate results from (3) and (4) using rank fusion techniques;
Add the top-K chunks to the prompt to generate the response.
By leveraging both BM25 and embedding models, traditional RAG systems can provide more comprehensive and accurate results, balancing precise term matching with broader semantic understanding.

问题：上下文丢失
This approach allows you to cost-effectively scale to enormous knowledge bases, far beyond what could fit in a single prompt. But these traditional RAG systems have a significant limitation: they often destroy context.

The context conundrum in traditional RAG
In traditional RAG, documents are typically split into smaller chunks for efficient retrieval. While this approach works well for many applications, it can lead to problems when individual chunks lack sufficient context.

For example, imagine you had a collection of financial information (say, U.S. SEC filings) embedded in your knowledge base, and you received the following question: "What was the revenue growth for ACME Corp in Q2 2023?"

A relevant chunk might contain the text: "The company's revenue grew by 3% over the previous quarter." However, this chunk on its own doesn't specify which company it's referring to or the relevant time period, making it difficult to retrieve the right information or use the information effectively.

## 优化：上下文检索
优势：为每个chunk增加上下文

### Implementing Contextual Retrieval
Of course, it would be far too much work to manually annotate the thousands or even millions of chunks in a knowledge base. To implement Contextual Retrieval, we turn to Claude. We’ve written a prompt that instructs the model to provide concise, chunk-specific context that explains the chunk using the context of the overall document. We used the following Claude 3 Haiku prompt to generate context for each chunk:

<document> 
{{WHOLE_DOCUMENT}} 
</document> 
Here is the chunk we want to situate within the whole document 
<chunk> 
{{CHUNK_CONTENT}} 
</chunk> 
Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else. 
The resulting contextual text, usually 50-100 tokens, is prepended to the chunk before embedding it and before creating the BM25 index.

### Performance improvements
Our experiments showed that:
Contextual Embeddings reduced the top-20-chunk retrieval failure rate by 35% (5.7% → 3.7%).
Combining Contextual Embeddings and Contextual BM25 reduced the top-20-chunk retrieval failure rate by 49% (5.7% → 2.9%).

# Implementation considerations
When implementing Contextual Retrieval, there are a few considerations to keep in mind:

Chunk boundaries: Consider how you split your documents into chunks. The choice of chunk size, chunk boundary, and chunk overlap can affect retrieval performance1.
Embedding model: Whereas Contextual Retrieval improves performance across all embedding models we tested, some models may benefit more than others. We found Gemini and Voyage embeddings to be particularly effective.
Custom contextualizer prompts: While the generic prompt we provided works well, you may be able to achieve even better results with prompts tailored to your specific domain or use case (for example, including a glossary of key terms that might only be defined in other documents in the knowledge base).
Number of chunks: Adding more chunks into the context window increases the chances that you include the relevant information. However, more information can be distracting for models so there's a limit to this. We tried delivering 5, 10, and 20 chunks, and found using 20 to be the most performant of these options (see appendix for comparisons) but it’s worth experimenting on your use case.

# Further boosting performance with Reranking
In a final step, we can combine Contextual Retrieval with another technique to give even more performance improvements. In traditional RAG, the AI system searches its knowledge base to find the potentially relevant information chunks. With large knowledge bases, this initial retrieval often returns a lot of chunks—sometimes hundreds—of varying relevance and importance.

Reranking is a commonly used filtering technique to ensure that only the most relevant chunks are passed to the model. Reranking provides better responses and reduces cost and latency because the model is processing less information. The key steps are:

Perform initial retrieval to get the top potentially relevant chunks (we used the top 150);
Pass the top-N chunks, along with the user's query, through the reranking model;
Using a reranking model, give each chunk a score based on its relevance and importance to the prompt, then select the top-K chunks (we used the top 20);
Pass the top-K chunks into the model as context to generate the final result.