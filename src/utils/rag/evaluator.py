import json
import logging
from math import log
from typing import List, Dict, Any, Optional
from pathlib import Path
import sys
import os

from scipy.linalg import basic
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.utils.rag.dataset_generator import DatasetGenerator
from src.utils.rag.context_generator import ContextGenerator
from src.database.milvus_client import Milvus
from llama_index.core import Document, SimpleDirectoryReader
from src.utils.rag.rag_service_context import ContextualRAGService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGEvaluator:
    def __init__(self):
        """初始化评估器"""
        self.evaluation_set_path = "./src/utils/rag/data/evaluation_set.json"
        self.evaluation_set = self._load_evaluation_set(self.evaluation_set_path)
        self.metrics = {
            'basic_rag': {'pass@5': 0, 'pass@10': 0, 'pass@20': 0},
            'contextual_rag': {'pass@5': 0, 'pass@10': 0, 'pass@20': 0}
        }
        
        # 初始化Milvus客户端
        self.milvus_basic = Milvus()
        self.milvus_context = Milvus()
        
        # 设置collection名称
        self.rag_basic = "rag_basic"
        self.rag_context = "rag_context"
        
        # 初始化数据集生成器和上下文生成器
        self.dataset_generator = DatasetGenerator("./src/utils/rag/docs", gemini_api_key=os.getenv("GEMINI_API_KEY"))
        self.context_generator = ContextGenerator()

        self.rag_context_service = ContextualRAGService()
            
    def _load_evaluation_set(self, path: str) -> List[Dict[str, Any]]:
        """加载评估数据集
        
        Args:
            path: 评估集文件路径
            
        Returns:
            评估集列表
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载评估集失败: {e}")
            return []
    # 使用文本相似度计算Pass@k
    def _calculate_pass_at_k(self, retrieved_chunks: List[Dict], golden_chunk: str) -> Dict[str, float]:
        """使用文本相似度计算Pass@k
        
        Args:
            retrieved_chunks: 检索到的文档块列表
            golden_chunk: 黄金标准文档块内容
            
        Returns:
            各k值的Pass@k指标
        """
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity
        
        # 初始化编码器（如果还没初始化）
        if not hasattr(self, '_encoder'):
            self._encoder = SentenceTransformer('all-MiniLM-L6-v2')
            
        # 编码golden_chunk GPU convert_to_tensor=True
        golden_embedding = self._encoder.encode([golden_chunk], convert_to_tensor=False)
        
        results = {}
        for k in [5, 10, 20]:
            top_k_chunks = retrieved_chunks[0][:k]
            
            # 获取检索结果的文本内容
            chunk_texts = [chunk.get('entity', chunk.get('text', '')) for chunk in top_k_chunks]
            
            if not chunk_texts:
                results[f'pass@{k}'] = 0.0
                continue
                
            # 计算每个检索结果与golden_chunk的相似度
            chunk_embeddings = self._encoder.encode(chunk_texts, convert_to_tensor=False)
            similarities = cosine_similarity(golden_embedding, chunk_embeddings)[0]
            # FOR GPU : similarities = cosine_similarity(golden_embedding.cpu().numpy(), 
            #                               chunk_embeddings.cpu().numpy())[0]
            
            # 如果最高相似度超过阈值，认为找到了正确答案
            threshold = 0.8  # 可以根据实际情况调整阈值
            results[f'pass@{k}'] = 1.0 if max(similarities) > threshold else 0.0
            
            # 记录日志
            max_sim = max(similarities)
            logger.info(f"Top similarity for k={k}: {max_sim:.4f}")
            if max_sim > threshold:
                max_idx = similarities.argmax()
                logger.info(f"Found matching chunk with similarity {max_sim:.4f}")
                # logger.info(f"Retrieved: {chunk_texts[max_idx][:20]}...")
                logger.info(f"Ground Truth Golden: {golden_chunk[:20].encode('utf-8').decode('utf-8')}...")
        
        return results
        
    def evaluate_basic_rag(self):
        """评估基础RAG系统"""
        total_samples = len(self.evaluation_set)
        
        for qa_pair in self.evaluation_set:
            query = qa_pair['question']
            golden_chunk = qa_pair['golden_chunk']  # 直接使用golden_chunk内容
            
            # 使用基础RAG进行检索
            retrieved_chunks = self.milvus_basic.search(query, limit=20)
            
            # 计算指标
            sample_metrics = self._calculate_pass_at_k(retrieved_chunks, golden_chunk)
            
            # 累加指标
            for k, v in sample_metrics.items():
                self.metrics['basic_rag'][k] += v
                
        # 计算平均值
        for k in self.metrics['basic_rag']:
            self.metrics['basic_rag'][k] /= total_samples
            
    def evaluate_contextual_rag(self):
        """评估上下文增强RAG系统"""
        total_samples = len(self.evaluation_set)
        
        for qa_pair in self.evaluation_set:
            query = qa_pair['question']
            golden_chunk = qa_pair['golden_chunk']  # 直接使用golden_chunk内容
            
            # 使用上下文增强RAG进行检索
            retrieved_chunks = self.milvus_context.search(query, limit=20)
            
            # 计算指标
            sample_metrics = self._calculate_pass_at_k(retrieved_chunks, golden_chunk)
            
            # 累加指标
            for k, v in sample_metrics.items():
                self.metrics['contextual_rag'][k] += v
                
        # 计算平均值
        for k in self.metrics['contextual_rag']:
            self.metrics['contextual_rag'][k] /= total_samples
            
    def evaluate(self) -> Dict[str, Dict[str, float]]:
        """评估RAG系统的性能
        
        Returns:
            Dict[str, Dict[str, float]]: 包含Pass@5、Pass@10、Pass@20的评估结果
        """
        # 初始化评估指标
        metrics = {
            'basic_rag': {'pass@5': 0, 'pass@10': 0, 'pass@20': 0},
            'contextual_rag': {'pass@5': 0, 'pass@10': 0, 'pass@20': 0}
        }
        
        total_queries = len(self.evaluation_set)
        logger.info(f'Evaluating {total_queries} queries.')
        
        # 遍历每个评估样本
        for eval_item in self.evaluation_set:  
            query = eval_item['question']
            golden_chunk = eval_item['golden_chunk']
            # 新的一轮
            logger.info(f' ???????? Question: {query} ???????? ')
            logger.info(f' ============= Ground truth: {golden_chunk} ============= ')

            # 使用基础RAG进行检索
            retrieved_results = self.milvus_basic.search("rag_basic", query, limit=20)
            logger.info(f' +++++++++++++++ Basic Retrieved {len(retrieved_results[0])}')
            # 计算指标
            sample_metrics = self._calculate_pass_at_k(retrieved_results, golden_chunk)
            # 累加指标
            for k, v in sample_metrics.items():
                metrics['basic_rag'][k] += v
            logger.info(f' +++++++++++++++ Basic metrics: {metrics}')

            # 使用上下文增强RAG进行检索
            retrieved_results = self.rag_context_service.retrieve(query, top_k=20)
            logger.info(f' +++++++++++++++ Contextual Retrieved {len(retrieved_results[0])}')
            # 计算指标
            sample_metrics = self._calculate_pass_at_k(retrieved_results, golden_chunk)
            # 累加指标
            for k, v in sample_metrics.items():
                metrics['contextual_rag'][k] += v
            logger.info(f'----------------- Contextual metrics: {metrics}')
        
        # 计算平均值
        for k in metrics:
            for sub_k in metrics[k]:
                metrics[k][sub_k] = metrics[k][sub_k] / total_queries if total_queries > 0 else 0
                logger.info(f'{k} {sub_k}: {metrics[k][sub_k]:.4f}')
            
        return metrics
        
    def _add_documents_to_vector_store(self, collection_name: str, with_context: bool = False):
        """将文档添加到向量库
        
        Args:
            collection_name: 集合名称
            with_context: 是否添加上下文（使用answer作为上下文）
        """
        logger.info(f"Adding documents to vector store {collection_name}...")
        
        # # 加载文档目录下的所有文件
        # docs_dir = "./src/utils/rag/docs"
        # reader = SimpleDirectoryReader(docs_dir)
        # raw_documents = reader.load_data()
        # 处理每个文档
        # self._add_document
        
        # 选择对应的Milvus实例
        milvus_instance = self.milvus_context if with_context else self.milvus_basic
        
        # 创建collection
        milvus_instance.create_collection(collection_name)
        
        # 准备文档
        documents = []
        for item in self.evaluation_set:
            if with_context:
                # context版本：使用answer作为上下文
                content = self.context_generator.add_context_to_chunk(
                    chunk_content=item['golden_chunk'],
                    context=item['answer']
                )
            else:
                # basic版本：直接使用golden_chunk
                content = item['golden_chunk']
            
            documents.append(content)
        
        # 批量添加到Milvus
        milvus_instance.upsert_docs(
            collection_name=collection_name,
            docs=documents,
            subject="evaluation_set",  # 统一的subject
            author="evaluation"        # 统一的author
        )
            
        logger.info(f"Added {len(documents)} documents to {collection_name}")
    
    def _add_document(self, milvus_instance: Milvus, collection_name: str, 
                     document_id: str, document: Document, 
                     metadata: Optional[Dict] = None, with_context: bool = False) -> bool:
        """添加单个文档到向量数据库
        
        Args:
            milvus_instance: Milvus实例
            collection_name: 集合名称
            document_id: 文档ID
            document: 文档对象
            metadata: 元数据
            with_context: 是否添加上下文
        """
        try:
            # 分割文档
            chunks = self.dataset_generator._split_document(document)
            chunk_texts = []
            
            # 处理每个chunk
            for i, chunk in enumerate(chunks):
                content = chunk.text if hasattr(chunk, 'text') else chunk
                
                # 如果需要上下文，则生成
                if with_context:
                    context = self.context_generator.generate_context(content, document.text)
                    content = self.context_generator.add_context_to_chunk(content, context)
                
                chunk_texts.append(content)
            
            # 使用upsert_docs添加到Milvus
            # metadata会被自动添加到每个chunk中
            milvus_instance.upsert_docs(
                collection_name=collection_name,
                docs=chunk_texts,
                subject=document_id,  # 用document_id作为subject便于后续查询
                author=metadata.get('file_name', '') if metadata else ''
            )
            
            logger.info(f"DocumentId: {document_id} saved into {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add document: {str(e)}")
            return False

if __name__ == "__main__":
    # 初始化评估器
    evaluator = RAGEvaluator()

    # # 1. 初始化数据库
    # # 基础版本（不带上下文）
    # evaluator._add_documents_to_vector_store("rag_basic", with_context=False)
    # # 上下文增强版本
    # evaluator._add_documents_to_vector_store("rag_context", with_context=True)

    # 2. 评估
    results = evaluator.evaluate()
    print(results)