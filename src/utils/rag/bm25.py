import numpy as np
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
import jieba
import os

class BM25Search:
    def __init__(self):
        self.bm25 = None
        self.documents = []
        self.doc_ids = []
        
    def add_documents(self, documents: List[Dict[str, Any]]):
        """添加文档到BM25索引
        
        Args:
            documents: 文档列表，每个文档是一个字典，包含content和chunk_id字段
        """
        self.documents = []
        self.doc_ids = []
        
        # 对每个文档分词
        tokenized_docs = []
        for doc in documents:
            self.documents.append(doc["content"])
            self.doc_ids.append(doc["chunk_id"])
            # 使用jieba分词
            tokens = list(jieba.cut(doc["content"]))
            tokenized_docs.append(tokens)
            
        # 创建BM25索引
        self.bm25 = BM25Okapi(tokenized_docs)
        
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索文档
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            List[Dict[str, Any]]: 检索结果列表，每个元素包含chunk_id、content和score
        """
        if not self.bm25:
            return []
            
        # 对查询分词
        tokenized_query = list(jieba.cut(query))
        
        # 计算BM25分数
        scores = self.bm25.get_scores(tokenized_query)
        
        # 获取top_k的索引
        top_indices = np.argsort(scores)[-top_k:][::-1]
        
        # 组织返回结果
        results = []
        for idx in top_indices:
            results.append({
                "chunk_id": self.doc_ids[idx],
                "content": self.documents[idx],
                "score": float(scores[idx])  # 转换为Python float
            })
            
        return results
