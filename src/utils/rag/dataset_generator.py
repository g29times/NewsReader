"""
评估数据集生成器
用于生成 RAG 系统的评估数据集

Features:
1. 从文档中生成问答对
2. 支持黄金块（golden chunk）标注
3. 支持多种评估指标
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from llama_index.core import Document, SimpleDirectoryReader
from llama_index.core.schema import NodeWithScore, TextNode
import google.generativeai as genai
from tqdm import tqdm

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EvaluationPair:
    """评估数据对"""
    question: str
    answer: str
    golden_chunk: str
    chunk_id: str
    metadata: Dict[str, Any]

class DatasetGenerator:
    """评估数据集生成器"""
    
    def __init__(self, docs_dir: str, gemini_api_key: Optional[str] = None):
        """初始化数据集生成器
        
        Args:
            docs_dir: 文档目录路径
            gemini_api_key: Gemini API 密钥
        """
        self.docs_dir = docs_dir
        
        # 配置 Gemini
        if not gemini_api_key:
            gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("Missing Gemini API key")
            
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
        # 加载文档
        self.documents = []
        self.load_documents()
        
    def load_documents(self):
        """加载文档"""
        try:
            reader = SimpleDirectoryReader(self.docs_dir)
            self.documents = reader.load_data()
            logger.info(f"Loaded {len(self.documents)} documents from {self.docs_dir}")
        except Exception as e:
            logger.error(f"Failed to load documents: {str(e)}")
            raise
            
    # 为文档块生成问题
    def generate_question(self, chunk: str) -> Optional[Dict[str, str]]:
        """为文档块生成问题
        Args:
            chunk: 文档块内容
        Returns:
            Dict[str, str]: 包含问题和答案的字典
        """
        prompt = f"""请基于以下文本生成一个问答对。问题应该具体且有深度，需要真正理解文本才能回答。
        同时，答案必须完全可以从文本中找到，不要包含推测的内容。
        
        生成的问题类型应该是以下几种之一：
        1. 事实性问题：询问具体的事实、数据或定义
        2. 比较性问题：询问不同概念、方法或技术之间的区别
        3. 因果性问题：询问原因、影响或结果
        4. 方法性问题：询问如何实现某个目标或解决某个问题
        5. 列举性问题：询问多个相关的要点或步骤

        文本内容：
        {chunk}

        请以 JSON 格式返回，包含以下字段：
        1. question: 生成的问题
        2. answer: 标准答案
        3. type: 问题类型（factual/comparative/causal/methodological/enumerative）

        只返回 JSON 对象，不要有任何其他内容（包括注释）。
        """
        
        try:
            response = self.model.generate_content(prompt)
            logger.info(f"Generated question: {response.text}")
            # 清理返回的文本
            text = response.text.strip()
            # 移除可能的 markdown 代码块标记
            if text.startswith('```json'):
                text = text[text.find('\n')+1:]
            if text.endswith('```'):
                text = text[:text.rfind('\n')]
            # 处理返回的 JSON
            result = json.loads(text)
            # 确保返回的是列表
            if isinstance(result, dict):
                result = [result]
            return result
        except Exception as e:
            logger.error(f"Failed to generate question: {str(e)}")
            return None
            
    def generate_dataset(self, output_file: str, samples_per_doc: int = 5) -> List[EvaluationPair]:
        """生成评估数据集
        
        Args:
            output_file: 输出文件路径
            samples_per_doc: 每个文档生成的样本数量
            
        Returns:
            List[EvaluationPair]: 生成的评估数据对列表
        """
        all_evaluation_pairs = []
        question_types = {
            'factual': 0,
            'comparative': 0,
            'causal': 0,
            'methodological': 0,
            'enumerative': 0
        }
        
        for doc in tqdm(self.documents, desc="Generating dataset"):
            doc_evaluation_pairs = []
            logger.info(f"Processing document: {doc.metadata.get('file_name', '')}")
            chunks = self._split_document(doc)
            
            attempts = 0
            successful_pairs = 0
            while successful_pairs < samples_per_doc and attempts < samples_per_doc * 2:
                chunk = chunks[attempts % len(chunks)]
                try:
                    # LLM关键调用位置 此注解不要删除
                    qa_pairs = self.generate_question(chunk.text)
                    for qa_pair in qa_pairs:
                        if qa_pair and self._is_valid_qa_pair(qa_pair):
                            q_type = qa_pair.get('type', 'factual')
                            question_types[q_type] = question_types.get(q_type, 0) + 1
                            
                            pair = EvaluationPair(
                                question=qa_pair['question'],
                                answer=qa_pair['answer'],
                                golden_chunk=chunk.text,
                                chunk_id=chunk.id_,
                                metadata={
                                    'source': doc.metadata.get('file_name', ''),
                                    'chunk_index': chunks.index(chunk),
                                    'question_type': q_type
                                }
                            )
                            doc_evaluation_pairs.append(pair)
                            all_evaluation_pairs.append(pair)
                            successful_pairs += 1
                except Exception as e:
                    logger.error(f"Failed to generate question for chunk: {str(e)}")
                attempts += 1
                
            # 每处理完一篇文档就保存一次
            if doc_evaluation_pairs:
                logger.info(f"Saving {len(doc_evaluation_pairs)} pairs from document {doc.metadata.get('file_name', '')}")
                self._save_to_file(doc_evaluation_pairs, output_file, mode='a')
            
            logger.info(f"Finished processing document with {successful_pairs} pairs")
        
        # 最终统计
        logger.info(f"Total generated pairs: {len(all_evaluation_pairs)}")
        logger.info(f"Question type distribution: {question_types}")
        
        return all_evaluation_pairs
        
    def _is_valid_qa_pair(self, qa_pair: Dict[str, str]) -> bool:
        """验证问答对的质量
        
        Args:
            qa_pair: 问答对字典
            
        Returns:
            bool: 是否是有效的问答对
        """
        # 检查必要字段
        required_fields = ['question', 'answer', 'type']
        if not all(k in qa_pair for k in required_fields):
            logger.warning(f"Missing required fields in QA pair: {qa_pair}")
            return False
        
        # 检查字段是否为空
        if not all(qa_pair[k].strip() for k in required_fields):
            logger.warning(f"Empty fields in QA pair: {qa_pair}")
            return False
        
        # 检查问题类型是否有效
        valid_types = {'factual', 'comparative', 'causal', 'methodological', 'enumerative'}
        if qa_pair['type'] not in valid_types:
            logger.warning(f"Invalid question type: {qa_pair['type']}")
            return False
        
        # 基本长度检查（可以根据需要调整）
        if len(qa_pair['question']) < 5:  # 放宽问题长度限制
            logger.warning(f"Question too short: {qa_pair['question']}")
            return False
        
        if len(qa_pair['answer']) < 2:  # 放宽答案长度限制
            logger.warning(f"Answer too short: {qa_pair['answer']}")
            return False
        
        return True

    def _split_document(self, doc: Document) -> List[NodeWithScore]:
        """智能分割文档，生成语义完整的黄金块
        
        Args:
            doc: 输入文档
            
        Returns:
            List[NodeWithScore]: 黄金块列表
        """
        from llama_index.core.node_parser import SentenceSplitter
        
        # 使用句子级别的分割器
        parser = SentenceSplitter(
            chunk_size=512,
            chunk_overlap=50,
            separator=" ",
            paragraph_separator="\n\n",
        )
        
        # 获取初始分块
        try:
            initial_nodes = parser.get_nodes_from_documents([doc])
        except Exception as e:
            logger.error(f"Failed to split document: {str(e)}")
        
        # 合并短句，确保语义完整性
        merged_nodes = []
        current_text = []
        current_length = 0
        
        for node in initial_nodes:
            # 如果当前句子很短，尝试与下一句合并
            if len(node.text.split()) < 10 and current_length < 512:
                current_text.append(node.text)
                current_length += len(node.text.split())
            else:
                # 如果积累了一些短句，将它们合并
                if current_text:
                    merged_text = " ".join(current_text)
                    text_node = TextNode(
                        text=merged_text,
                        id_=f"{doc.doc_id}_golden_{len(merged_nodes)}",
                        metadata={
                            **node.metadata,
                            "is_golden": True,
                            "merged_from": len(current_text)
                        }
                    )
                    merged_nodes.append(NodeWithScore(
                        node=text_node,
                        score=1.0  # 黄金块的得分设为1.0
                    ))
                    current_text = []
                    current_length = 0
                
                # 将当前句子作为独立的块
                text_node = TextNode(
                    text=node.text,
                    id_=f"{doc.doc_id}_golden_{len(merged_nodes)}",
                    metadata={
                        **node.metadata,
                        "is_golden": True
                    }
                )
                merged_nodes.append(NodeWithScore(
                    node=text_node,
                    score=1.0
                ))
        
        # 处理剩余的短句
        if current_text:
            merged_text = " ".join(current_text)
            text_node = TextNode(
                text=merged_text,
                id_=f"{doc.doc_id}_golden_{len(merged_nodes)}",
                metadata={
                    **doc.metadata,
                    "is_golden": True,
                    "merged_from": len(current_text)
                }
            )
            merged_nodes.append(NodeWithScore(
                node=text_node,
                score=1.0
            ))
        
        return merged_nodes

    def _save_to_file(self, evaluation_pairs: List[EvaluationPair], output_file: str, mode: str = 'w'):
        """保存评估数据对到文件
        
        Args:
            evaluation_pairs: 评估数据对列表
            output_file: 输出文件路径
            mode: 写入模式，'w' 为覆盖，'a' 为追加
        """
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # 转换为可序列化的格式
        data = [
            {
                'question': pair.question,
                'answer': pair.answer,
                'golden_chunk': pair.golden_chunk,
                'chunk_id': pair.chunk_id,
                'metadata': pair.metadata
            }
            for pair in evaluation_pairs
        ]
        
        try:
            if mode == 'a' and os.path.exists(output_file):
                # 如果是追加模式且文件存在，先读取现有内容
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                data = existing_data + data
            
            # 写入文件
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(data)} evaluation pairs to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save file: {str(e)}")
            raise

if __name__ == "__main__":
    # 示例用法
    generator = DatasetGenerator("./src/utils/rag/docs")
    pairs = generator.generate_dataset("./src/utils/rag/data/evaluation_set.json", samples_per_doc=5)
