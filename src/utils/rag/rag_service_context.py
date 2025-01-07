"""
Enhanced RAG service with Contextual Retrieval
基于 Anthropic 的上下文检索方法实现的增强版 RAG 服务

Features:
1. Contextual Embeddings - 上下文感知的文档嵌入
2. BM25 Retrieval - 基于 BM25 算法的检索（无 ES 依赖）
3. Hybrid Search - 语义检索与 BM25 检索的融合
4. Reranking - 使用 JINA rerank 接口进行结果重排序
"""

import os
import sys
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from chromadb import EmbeddingFunction
from chromadb.api.types import Documents, Embeddings
from llama_index.core import Document, SimpleDirectoryReader

from src.utils.rag.rag_service import RAGService
import src.utils.embeddings.voyager as voyager
from src.utils.rag.bm25 import BM25Search

# 配置日志
logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """检索结果数据类"""
    chunk_id: str
    score: float
    content: str
    metadata: Dict[str, Any]

class ContextualRAGService(RAGService):
    """上下文增强的RAG服务"""
    
    def __init__(self, vector_db_type: str = "milvus", vector_db_collection_name: str = "rag_context"):
        """Initialize contextual RAG service
        
        Args:
            vector_db_type: Type of vector database to use ("chroma" or "milvus")
            vector_db_collection_name: 当前collection名称
        """
        super().__init__(vector_db_type=vector_db_type)
        
        # 设置collection名称
        if vector_db_collection_name:
            self.vector_collection_name = vector_db_collection_name
        
        # 创建数据集生成器（用于文档分割和上下文生成）
        # self.dataset_generator = DatasetGenerator("./src/utils/rag/docs", gemini_api_key=os.getenv("GEMINI_API_KEY"))
        
        self.bm25 = None
        
    # 密集向量
    def semantic_search(self, query: str, top_k: int = 20) -> List[Dict]:
        """使用语义检索方法进行检索"""
        try:
            # 使用基类的retrieve方法进行语义搜索
            results = super().retrieve(self.vector_collection_name, query, top_k=top_k)
            logger.info(f" +++++++++++++++ semantic_search {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    # 稀疏
    def bm25_search(self, documents: List[Dict], query: str, top_k: int = 20) -> List[SearchResult]:
        """使用BM25算法进行检索"""
        
        # 使用BM25搜索前top_k个
        bm25_searcher = BM25Search()
        bm25_searcher.add_documents(documents)
        results = bm25_searcher.search(query, top_k)
        
        logger.info(f" +++++++++++++++ BM25 search returned {len(results)} results")
        
        # 转换为SearchResult格式
        search_results = []
        for result in results:
            search_results.append(SearchResult(
                chunk_id=result["chunk_id"],
                score=result["score"],
                content=result["content"],
                metadata={}
            ))
        return search_results
            
    def hybrid_search(self, documents: List[Dict], query: str, top_k: int = 20) -> List[SearchResult]:
        """混合检索方法，融合语义检索和BM25检索结果"""
        # 分别进行语义检索和BM25检索
        semantic_results = self.semantic_search(query, top_k=top_k)
        bm25_results = self.bm25_search(documents, query, top_k=top_k)
        
        # 合并结果，使用字典去重
        chunk_scores = {}
        
        # 归一化语义检索分数
        semantic_scores = np.array([r['score'] for r in semantic_results])
        if len(semantic_scores) > 0:
            semantic_max = np.max(semantic_scores)
            semantic_min = np.min(semantic_scores)
            if semantic_max > semantic_min:
                semantic_scores = (semantic_scores - semantic_min) / (semantic_max - semantic_min)
        
        # 归一化BM25分数
        bm25_scores = np.array([r.score for r in bm25_results])
        if len(bm25_scores) > 0:
            bm25_max = np.max(bm25_scores)
            bm25_min = np.min(bm25_scores)
            if bm25_max > bm25_min:
                bm25_scores = (bm25_scores - bm25_min) / (bm25_max - bm25_min)
        
        # 添加归一化后的语义检索结果
        for i, result in enumerate(semantic_results):
            chunk_scores[result['id']] = {
                'semantic_score': float(semantic_scores[i]) if i < len(semantic_scores) else 0.0,
                'bm25_score': 0.0,
                'content': result['content'],
                'metadata': {}
            }
            
        # 添加归一化后的BM25结果
        for i, result in enumerate(bm25_results):
            if result.chunk_id in chunk_scores:
                chunk_scores[result.chunk_id]['bm25_score'] = float(bm25_scores[i]) if i < len(bm25_scores) else 0.0
            else:
                chunk_scores[result.chunk_id] = {
                    'semantic_score': 0.0,
                    'bm25_score': float(bm25_scores[i]) if i < len(bm25_scores) else 0.0,
                    'content': result.content,
                    'metadata': {}
                }
                
        # 计算最终得分 (加权平均)
        alpha = 0.6  # 语义检索权重
        beta = 0.4   # BM25检索权重，增加BM25的权重以获得更多样的结果
        
        results = [] # 将两种查询的结果合并 hybrid
        for chunk_id, scores in chunk_scores.items():
            final_score = alpha * scores['semantic_score'] + beta * scores['bm25_score']
            results.append(SearchResult(
                chunk_id=chunk_id,
                score=final_score,
                content=scores['content'],
                metadata={
                    **scores['metadata'],
                    'semantic_score': scores['semantic_score'],
                    'bm25_score': scores['bm25_score']
                }
            ))
            
        # 按得分排序
        results.sort(key=lambda x: x.score, reverse=True)
        
        # 对结果进行重排序 results[:top_k]
        return self.rerank_results_voyage(query, results, top_k)
            
    def rerank_results_voyage(self, query: str, results: List[SearchResult], top_k: int = 20) -> List[SearchResult]:
        """使用voyage-ai的rerank对结果重排序"""
        if not results:
            return []
            
        # 准备rerank数据
        documents = [result.content for result in results]
        
        try:
            # 调用voyage rerank
            rerank_results = voyager.rerank_with_voyage(
                query=query,
                documents=documents,
                top_k=len(documents)  # rerank所有结果
            )
            
            # 获取rerank分数并归一化
            rerank_scores = np.array([r.relevance_score for r in rerank_results])
            if len(rerank_scores) > 0:
                rerank_max = np.max(rerank_scores)
                rerank_min = np.min(rerank_scores)
                if rerank_max > rerank_min:
                    rerank_scores = (rerank_scores - rerank_min) / (rerank_max - rerank_min)
                    
                # 使用softmax使分数分布更平滑
                rerank_scores = np.exp(rerank_scores) / np.sum(np.exp(rerank_scores))
            
            # 重新组织结果
            reranked = []
            gamma = 0.5  # rerank权重，降低以减少过度依赖rerank
            delta = 0.5  # 原始分数权重，增加以保留更多原始排序信息
            
            for i, result in enumerate(rerank_results):
                original_result = results[result.index]
                # 结合原始分数和rerank分数
                final_score = gamma * float(rerank_scores[i]) + delta * original_result.score
                
                reranked.append(SearchResult(
                    chunk_id=original_result.chunk_id,
                    score=final_score,
                    content=original_result.content,
                    metadata={
                        **original_result.metadata,
                        'reranked': True,
                        'rerank_method': 'voyage',
                        'rerank_score': float(rerank_scores[i]),
                        'original_score': original_result.score
                    }
                ))
            
            # 按最终得分排序
            reranked.sort(key=lambda x: x.score, reverse=True)
            return reranked[:top_k]
            
        except Exception as e:
            logger.error(f" -------------------------- Voyage rerank failed: {str(e)}")
            return results[:top_k]
            
    def retrieve(self, documents: List[Dict], query: str, top_k: int = 20) -> List[Dict]:
        """检索接口，返回检索结果"""
        results = self.hybrid_search(documents, query, top_k=top_k)
        return [{'id': r.chunk_id, 'score': r.score, 'content': r.content} for r in results]