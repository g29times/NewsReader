from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
import os, sys, json
import numpy as np

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
if project_root not in sys.path:
    sys.path.append(project_root)
from src.utils.llms.gemini_client import GeminiClient
from src.utils.llms.minimax_client import MinimaxClient
import src.utils.embeddings.voyager as voyager

llm = ChatOpenAI(model="gpt-4o-mini")

import logging
logger = logging.getLogger(__name__)

class RAG:
    
    def __init__(self):
        self.llm = llm
        self.gemini = GeminiClient()
        self.minimax = MinimaxClient()
        self.embeddings = OpenAIEmbeddings()
        self.doc_embeddings = None
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

    def get_evaluation_dataset(self, queries, answers=None, relevant_docs=None, references=None):
        dataset = []
        if answers is None:
            answers = [None]
        if references is None:
            references = [None]
        # for query, reference in zip(sample_queries, expected_responses):
        for query, answer, reference in zip(queries, answers, references):
            relevant_docs = relevant_docs or self.get_most_relevant_docs(query)
            response = answer or self.generate_answer(query, relevant_docs)
            if reference and reference != "":
                dataset.append(
                    {
                        "user_input": query,
                        "retrieved_contexts": relevant_docs,
                        "response": response,
                        "reference": reference
                    }
                )
            else:
                dataset.append(
                    {
                        "user_input": query,
                        "retrieved_contexts": relevant_docs,
                        "response": response
                    }
            )
        from ragas import EvaluationDataset
        evaluation_dataset = EvaluationDataset.from_list(dataset)
        print(" ------------------------- 打印第一条数据集观察 ------------------------- ")
        logger.info(evaluation_dataset[0])
        return evaluation_dataset

    def eval(self, evaluation_dataset):
        if not evaluation_dataset.samples:
            logger.warning("Evaluation dataset is empty.")
            return
        from ragas import evaluate
        from ragas.llms import LangchainLLMWrapper
        evaluator_llm = LangchainLLMWrapper(llm)
        # from ragas.metrics import LLMContextRecall, Faithfulness, FactualCorrectness
        # result = evaluate(dataset=evaluation_dataset,metrics=[LLMContextRecall(), Faithfulness(), FactualCorrectness()], llm=evaluator_llm)
        from ragas.metrics import AnswerRelevancy, ContextPrecision, ContextRecall, ContextUtilization, FactualCorrectness
        if evaluation_dataset.samples[0].reference:
            result = evaluate(dataset=evaluation_dataset, metrics=[AnswerRelevancy(), ContextPrecision(), FactualCorrectness()], llm=evaluator_llm)
        else:
            result = evaluate(dataset=evaluation_dataset, metrics=[AnswerRelevancy()], llm=evaluator_llm)
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
    real_docs = []
    real_queries = []
    real_references = []
    with open("./src/utils/rag/data/evaluation_set_011201_less.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        real_docs = [d["golden_chunk"] for d in data]
        real_queries = [d["question"] for d in data]
        real_references = [d["answer"] for d in data]
    print("Imported docs: " + str(len(real_docs)))

    # Initialize RAG instance
    rag = RAG()

    # 1 测试一条
    # Load documents
    rag.load_documents(real_docs) # sample_docs
    # Query and retrieve the most relevant document
    query = "万博宣伟韩国在2014年获得了哪个奖项？" # "Who introduced the theory of relativity?"
    relevant_doc = rag.get_most_relevant_docs(query)
    # Generate an answer
    answer = rag.generate_answer(query, relevant_doc)
    print(f"Query: {query}")
    print(f"Relevant Document: {relevant_doc}")
    print(f"Answer: {answer}")

    # Collect Evaluation Data
    sample_queries = [
        "Who introduced the theory of relativity?",
        "Who was the first computer programmer?",
        "What did Isaac Newton contribute to science?",
        "Who won two Nobel Prizes for research on radioactivity?",
        "What is the theory of evolution by natural selection?"
    ]
    expected_responses = [
        "Albert Einstein proposed the theory of relativity, which transformed our understanding of time, space, and gravity.",
        "Ada Lovelace is regarded as the first computer programmer for her work on Charles Babbage's early mechanical computer, the Analytical Engine.",
        "Isaac Newton formulated the laws of motion and universal gravitation, laying the foundation for classical mechanics.",
        "Marie Curie was a physicist and chemist who conducted pioneering research on radioactivity and won two Nobel Prizes.",
        "Charles Darwin introduced the theory of evolution by natural selection in his book 'On the Origin of Species'."
    ]

    # 2 进行批量测试
    evaluation_dataset = rag.get_evaluation_dataset(real_queries)
    # evaluation_dataset = rag.get_evaluation_dataset(real_queries, real_references)

    # Evaluate
    rag.eval(evaluation_dataset)