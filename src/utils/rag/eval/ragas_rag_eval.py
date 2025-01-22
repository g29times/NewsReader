from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
import os, sys, json
import numpy as np
import voyageai

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
if project_root not in sys.path:
    sys.path.append(project_root)
from src import GEMINI_MODELS
from src.utils.llms.gemini_client import GeminiClient
from src.utils.llms.minimax_client import MinimaxClient
import src.utils.embeddings.voyager as voyager

import logging
logger = logging.getLogger(__name__)

# https://docs.ragas.io/en/latest/getstarted/rag_eval/
class RAG:

    def __init__(self):
        llm = ChatOpenAI(model="gpt-4o-mini")

        # https://python.langchain.com/docs/integrations/llms/minimax/
        # pip install -U langchain-google-genai
        # https://python.langchain.com/docs/integrations/providers/google/
        from langchain_google_genai import ChatGoogleGenerativeAI
        gemini = ChatGoogleGenerativeAI(model=GEMINI_MODELS[0], google_api_key=os.getenv("GEMINI_API_KEY"))

        # pip install -qU langchain-voyageai
        # https://python.langchain.com/docs/integrations/text_embedding/
        from langchain_voyageai import VoyageAIEmbeddings
        voyageai = VoyageAIEmbeddings(model="voyage-3", api_key=os.getenv("VOYAGE_API_KEY"))

        self.llm = gemini
        self.gemini = GeminiClient()
        self.minimax = MinimaxClient()
        self.embeddings = voyageai
        self.doc_embeddings = voyageai
        self.docs = None

    # Load documents and compute their embeddings
    def load_documents(self, documents):
        """Load documents and compute their embeddings."""
        self.docs = documents
        self.doc_embeddings = voyager.get_doc_embeddings(documents) # self.embeddings.embed_documents(documents)

    # 可定制 通过本地实现相似度对比算法，对问题和docs进行比对，召回相似的文档
    def get_most_relevant_docs(self, query, topk=5):
        """Find the most relevant document for a given query."""
        if not self.docs or not self.doc_embeddings:
            raise ValueError("Documents and their embeddings are not loaded.")
        query_embedding = voyager.get_query_embedding(query) # self.embeddings.embed_query(query)
        similarities = [
            np.dot(query_embedding, doc_emb)
            / (np.linalg.norm(query_embedding) * np.linalg.norm(doc_emb))
            for doc_emb in self.doc_embeddings
        ]
        # 返回最接近的那一个文档
        # most_relevant_doc_index = np.argmax(similarities)
        # return [self.docs[most_relevant_doc_index]]
        # 返回topk个文档
        most_relevant_doc_indices = np.argsort(similarities)[::-1][:topk]
        return [self.docs[most_relevant_doc_index] for most_relevant_doc_index in most_relevant_doc_indices]

    # 可定制 将问题和参考文档传给 大模型 去回答
    def generate_answer(self, query, relevant_docs):
        """Generate an answer for a given query based on the most relevant document."""
        prompt = f"question: {query}\n\nDocuments: {relevant_docs}"
        system_prompt = "You are a helpful assistant that answers questions based on given documents only."
        messages = [
            ("system", system_prompt),
            ("human", prompt),
        ]
        # ragas官方 llm openai
        # ai_msg = self.llm.invoke(messages)
        # return ai_msg.content
        # 自定义 llm gemini google格式
        return self.gemini.query_with_history(question=prompt, histories=[], system_prompt=system_prompt)
        # 自定义 llm minimax openai格式
        # history = [{"role": "user", "content": "晚安，GEMI"},{"role": "assistant", "content": "晚安，Neo"}]
        # return self.minimax.query_openai_with_history(question=query, histories=[], system_prompt=system_prompt)

    # references: 参考答案  | answers: LLM实际回答 | reference_docs 参考文档 | retrieved_docs 实际召回的文档
    def get_evaluation_dataset(self, queries, references=[], answers=[], reference_docss=[], retrieved_docss=[]):
        dataset = []
        # 确保 references 与 queries 长度一致
        if references is None or len(references) == 0:
            references = [None] * len(queries)
        if answers is None or len(answers) == 0:
            answers = [None] * len(queries)
        if reference_docss is None or len(reference_docss) == 0:
            reference_docss = [None] * len(queries)
        if retrieved_docss is None or len(retrieved_docss) == 0:
            retrieved_docss = [None] * len(queries)
            
        for query, reference, response, reference_docs, retrieved_docs in zip(queries, references, answers, reference_docss, retrieved_docss):
            retrieved_docs = retrieved_docs or self.get_most_relevant_docs(query)
            response = response or self.generate_answer(query, retrieved_docs)
            if reference and reference != "": # 有参考答案
                dataset.append(
                    {
                        "user_input": query,
                        "response": response,
                        "reference": reference,
                        "retrieved_contexts": retrieved_docs,
                        # "reference_contexts": [reference_doc] # 手动开关
                    }
                )
            else:
                dataset.append(
                    {
                        "user_input": query,
                        "retrieved_contexts": retrieved_docs,
                        "reference_contexts": reference_docs,
                        "response": response
                    }
            )
        from ragas import EvaluationDataset
        evaluation_dataset = EvaluationDataset.from_list(dataset)
        print(" ------------------------- 打印第一条数据集观察 ------------------------- ")
        logger.info(evaluation_dataset[0])
        return evaluation_dataset

    # 指标选择 见vision.py
    def eval(self, evaluation_dataset):
        # 评估复杂度=指标*数据量 如 10个文档，3个指标，则要跑30轮
        if not evaluation_dataset.samples:
            logger.warning("Evaluation dataset is empty.")
            return
        from ragas import evaluate
        from ragas.llms import LangchainLLMWrapper
        evaluator_llm = LangchainLLMWrapper(self.llm)
        from ragas.embeddings import LangchainEmbeddingsWrapper
        evaluator_embeddings = LangchainEmbeddingsWrapper(self.embeddings)
        # 扩展评估 扩展参考答案reference - FactualCorrectness和参考资料reference_contexts - NonLLMContextRecall NonLLMContextPrecisionWithReference 
        if evaluation_dataset.samples[0].reference:
            from ragas.metrics import LLMContextRecall, ContextPrecision, FactualCorrectness
            result = evaluate(dataset=evaluation_dataset,metrics=[LLMContextRecall(), ContextPrecision(), FactualCorrectness()], llm=evaluator_llm)
        else:
        # 三角形评估基准
            from ragas.metrics import AnswerRelevancy, LLMContextPrecisionWithoutReference, Faithfulness
            from src.utils.rag.eval.metrics.context_recall import EnhancedContextRecall
            # 添加total_chunks字段
            # for sample in evaluation_dataset.samples:
            #     sample.reference_contexts = []  # 这里需要根据实际情况设置
            # 使用新的评估指标
            metrics = [
                AnswerRelevancy(llm=evaluator_llm),
                # LLMContextPrecisionWithoutReference(llm=evaluator_llm),
                # Faithfulness(llm=evaluator_llm),
                EnhancedContextRecall(llm=evaluator_llm)  # 添加新指标
            ]
            result = evaluate(embeddings=evaluator_embeddings, dataset=evaluation_dataset, metrics=metrics, llm=evaluator_llm)
        logger.info(result)

if __name__ == "__main__":
    # Load Documents
    sample_docs = [ # 全文？
        "Albert Einstein proposed the theory of relativity, which transformed our understanding of time, space, and gravity.",
        "Marie Curie was a physicist and chemist who conducted pioneering research on radioactivity and won two Nobel Prizes.",
        "Isaac Newton formulated the laws of motion and universal gravitation, laying the foundation for classical mechanics.",
        "Charles Darwin introduced the theory of evolution by natural selection in his book 'On the Origin of Species'.",
        "Ada Lovelace is regarded as the first computer programmer for her work on Charles Babbage's early mechanical computer, the Analytical Engine."
    ]
    # real_docs
    #  {
    #     "question": "万博宣伟韩国在2014年获得了哪个奖项？",
    #     "answer": "2014年度亚太顾问咨询大奖（Asia-Pacific Consultancy of the Year 2014）",
    #     "golden_chunk": "万博宣伟韩国 (Weber shandwick Korea)\n万博宣伟是 2001 年由万博集团 (Weber Group) (1987)、宣伟国际 (Shandwick International) \n(1974) 与 BSMG (2001) 合并而成的公关公司。总部位于首尔的万博宣伟也荣获了“2014 年度亚\n太顾问咨询大奖”(Asia-Pacifc Consultancy of the Year 2014)。\nd) 博雅韩国 (Burson-Marsteller Korea)\n博雅公关是一家全球性公关传播公司，总部位于纽约市。博雅公关在 6 大洲的 98 个国家设有 67\n间全资办事处和 61 间联营办事处。Merit/Burson-Marsteller 曾处理韩国重大全球性项目，包括\n1988 年首尔奥运会及韩国 2002 年世界杯申办的全球公关项目。Merit/Burson-Marsteller 目前与\n在韩国开展业务经营的主要跨国公司以及需要全球传播顾问的韩国客户合作。",
    #     "chunk_id": "43"
    #   },
    real_queries = []
    # real_answers = [] # 等待LLM回答
    real_references = []
    retrieved_docs = [] # RAG召回
    golden_chunks = [] # golden chunk
    with open("./src/utils/rag/data/rag_instruct_benchmark_20.jsonl", "r", encoding="utf-8") as f:
        data = json.load(f)
        real_queries = [d["question"] for d in data]
        real_references = [d["answer"] for d in data]
        retrieved_docs = [d["retrieved"] for d in data]
        golden_chunks = [d["golden_chunk"] for d in data]
    print("Imported docs: " + str(len(golden_chunks)))

    # Initialize RAG instance
    rag = RAG()

    # 1 测试一条
    # Load documents
    # rag.load_documents(sample_docs) # 注意启用
    # # Query and retrieve the most relevant document
    # query = "Who introduced the theory of relativity?"
    # relevant_doc = rag.get_most_relevant_docs(query)
    # # Generate an answer
    # answer = rag.generate_answer(query, relevant_doc)
    # print(f"Query: {query}")
    # print(f"Relevant Document: {relevant_doc}")
    # print(f"Answer: {answer}")

    # Collect Evaluation Data
    sample_queries = [
        "Who introduced the theory of relativity?",
        "Who was the first computer programmer?",
        "What did Isaac Newton contribute to science?",
        "Who won two Nobel Prizes for research on radioactivity?",
        "What is the theory of evolution by natural selection?"
    ]
    expected_responses = [ # reference
        "Albert Einstein proposed the theory of relativity, which transformed our understanding of time, space, and gravity.",
        "Ada Lovelace is regarded as the first computer programmer for her work on Charles Babbage's early mechanical computer, the Analytical Engine.",
        "Isaac Newton formulated the laws of motion and universal gravitation, laying the foundation for classical mechanics.",
        "Marie Curie was a physicist and chemist who conducted pioneering research on radioactivity and won two Nobel Prizes.",
        "Charles Darwin introduced the theory of evolution by natural selection in his book 'On the Origin of Species'."
    ]
    # 官方示例评测
    # evaluation_dataset = rag.get_evaluation_dataset(sample_queries)
    # {'answer_relevancy': 0.5467, 'llm_context_precision_without_reference': 1.0000, 'faithfulness': 0.9000}
    # evaluation_dataset = rag.get_evaluation_dataset(sample_queries, expected_responses)
    # {'context_recall': 1.0000, 'llm_context_precision_without_reference': 1.0000, 'factual_correctness': 0.7480}
    
    # 进行真实测试 指标说明：
    """评估方式一 只传query：
        对于每个查询（query）：
            answers 参数为 None，使用 [None] 作为默认值
            references 参数为 None，使用 [None] 作为默认值
            通过 get_most_relevant_docs 方法获取相关文档
            使用 generate_answer 方法生成回答
        构建数据集条目，包含三个字段：
            user_input: 用户输入的查询
            retrieved_contexts: 检索到的相关文档
            response: 生成的回答
        最终通过 ragas.EvaluationDataset.from_list 创建评估数据集
        在评估时（eval方法），由于没有参考答案，只能使用 AnswerRelevancy 指标进行评估 答案相关性
    """
    evaluation_dataset = rag.get_evaluation_dataset(real_queries, references=[], answers=real_references, 
        reference_docss=golden_chunks, retrieved_docss=retrieved_docs)
    # {'answer_relevancy': 0.4024, 'llm_context_precision_without_reference': 0.8182, 'faithfulness': 0.8182}
    # {'answer_relevancy': 0.3985, 'llm_context_precision_without_reference': 0.9347, 'faithfulness': 0.9545}
    """
    评估方式二：
    对于每个查询（query）和参考答案（reference）对：
        answers 参数为 None，使用 [None] 作为默认值
        通过 get_most_relevant_docs 方法获取相关文档
        使用 generate_answer 方法生成回答
    构建数据集条目，包含四个字段：
        user_input: 用户输入的查询
        retrieved_contexts: 检索到的相关文档
        response: 生成的回答
        reference: 参考答案（ground truth）
    最终通过 ragas.EvaluationDataset.from_list 创建评估数据集
    在评估时（eval方法），由于有参考答案，可以使用更多评估指标：
        AnswerRelevancy: 答案相关性
        ContextPrecision: 上下文精确度
        FactualCorrectness: 事实正确性
    """

    # Evaluate
    rag.eval(evaluation_dataset)