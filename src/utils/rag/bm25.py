from whoosh.index import create_in
from whoosh.fields import Schema, TEXT
from whoosh.qparser import QueryParser
from whoosh import scoring
import numpy as np
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
import jieba
import os

# 创建索引
def create_index(index_dir):
    schema = Schema(title=TEXT(stored=True), content=TEXT(stored=True))
    if not os.path.exists(index_dir):
        os.mkdir(index_dir)
    ix = create_in(index_dir, schema)
    return ix

# 向索引添加文档
def add_document(ix, doc_number, title, content):
    writer = ix.writer()
    writer.add_document(title=title, content=content)
    writer.commit()

# 搜索文档
def search(ix, query_str):
    with ix.searcher(weighting=scoring.BM25F()) as searcher:
        query = QueryParser("content", ix.schema).parse(query_str)
        results = searcher.search(query)
        for result in results:
            print(result)

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

# 使用示例
index_dir = "my_index"
ix = create_index(index_dir)
add_document(ix, 1, "Document 1", "This is the content of document one.")
add_document(ix, 2, "Document 2", "This is the content of document two.")

search(ix, "content:document")