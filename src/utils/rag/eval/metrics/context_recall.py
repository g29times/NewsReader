from dataclasses import dataclass, field
import logging
import numpy as np
from typing import Dict, Set, List, Any

from ragas.metrics import MetricWithLLM, SingleTurnMetric
from ragas.metrics.base import MetricType

logger = logging.getLogger(__name__)

@dataclass
class EnhancedContextRecall(MetricWithLLM, SingleTurnMetric):
    """
    基于传统召回率定义的上下文召回评估
    R = |C∩G| / |G| = TP / total_relevant_docs
    
    Attributes:
        name: 指标名称
        _required_columns: 评估所需的数据列
    """
    name: str = "enhanced_context_recall"
    _required_columns: Dict[MetricType, Set[str]] = field(
        default_factory=lambda: {
            MetricType.SINGLE_TURN: {
                "user_input",           # 用于判断文档相关性
                "retrieved_contexts",   # 召回的文档集合 C
                "reference_contexts"    # 标准答案，用于判断应该检索的文档总数
            }
        }
    )
    output_type: Any = float
    max_retries: int = 1

    # 调整similarity这个阈值
    def _score(self, row: Dict[str, Any]) -> float:
        """
        计算单个样本的召回率
        Args:
            row: 包含检索结果和ground truth的字典
        Returns:
            召回率分数
        """
        # 1. 计算正确检索到的文档数量
        retrieved_docs = row["retrieved_contexts"]
        ground_truths = row["reference_contexts"]
        
        # 如果没有ground truth或者没有检索结果，返回0
        if not ground_truths or not retrieved_docs:
            return 0.0
            
        # 对每个ground truth，检查是否有相似的retrieved文档
        tp = 0
        for truth in ground_truths:
            for retrieved in retrieved_docs:
                similarity = self._calculate_similarity(retrieved, truth)
                if similarity >= 0.6:  # 可以调整这个阈值
                    tp += 1
                    break  # 找到一个匹配就继续检查下一个ground truth
                    
        # 召回率 = 匹配上的ground truth数量 / ground truth总数
        total_relevant = len(ground_truths)
        recall = tp / total_relevant if total_relevant > 0 else 0.0
        
        return recall
        
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两段文本的相似度，使用余弦相似度
        Args:
            text1: 第一段文本
            text2: 第二段文本
        Returns:
            相似度分数 (0-1)
        """
        if not text1 or not text2:
            return 0.0
            
        # 1. 获取所有唯一词
        words = set(text1.split()).union(set(text2.split()))
        
        # 2. 构建词频向量
        vec1 = np.zeros(len(words))
        vec2 = np.zeros(len(words))
        
        word_to_idx = {word: i for i, word in enumerate(words)}
        
        for word in text1.split():
            vec1[word_to_idx[word]] += 1
            
        for word in text2.split():
            vec2[word_to_idx[word]] += 1
            
        # 3. 计算余弦相似度
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)

    async def _single_turn_ascore(self, sample: Any, callbacks: Any = None) -> float:
        """单轮对话评分接口
        
        Args:
            sample: 评估样本
            callbacks: 回调函数
            
        Returns:
            float: 召回率分数
        """
        row = sample.to_dict()
        return self._score(row)  # 返回召回率作为主要指标

# 评估数据示例
data = {
    "user_input": "这份企业会计准则资料的作者是谁？",
    "retrieved_contexts": ["文档段1", "文档段2", ...],  # TopK个召回结果
    "reference_contexts": ["文档段3", "文档段4", ...]  # 标准答案
}