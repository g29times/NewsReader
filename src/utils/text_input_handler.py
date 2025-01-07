from math import log
import re
import os
import sys
from typing import List, Dict, Any, Optional, Tuple
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import Document, TextNode, NodeWithScore

# 添加项目根目录到 Python 路径 标准方式
# 添加项目根目录到 Python 路径 标准方式
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)
# import src.utils.embeddings.jina as jina

import logging
logger = logging.getLogger(__name__)

class TextInputHandler:

    """
    Handler for processing text input for LLM processing
    """
    # TODO 文本清洗
    @staticmethod
    def preprocess_text(text):
        """
        Preprocess text data by cleaning and formatting
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove special characters
        text = re.sub(r'[^\w\s]', '', text)

        # Convert to lowercase
        text = text.lower()

        return text

    # 文本分割：默认使用JINA API，失败时自动切换到本地分割
    @staticmethod
    async def split_text(text: str, max_chunk_length: int = 500) -> List[str]:
        """智能分割文本，优先使用JINA API，失败时自动切换到本地分割器
        Args:
            text: 要分割的文本
            max_chunk_length: 最大块长度
        Returns:
            List[str]: 分割后的文本块列表
        """
        try:
            # JINA API 分的比较细 句子级别
            # chunks = await jina.split_text_with_jina(text, max_chunk_length)
            # if chunks:  # 如果成功获取到分块
            #     logger.info(f"JINA分割成功，切分成 {len(chunks)} 个chunk")
            #     return chunks
        #     raise Exception("JINA API returned empty chunks")
        # except Exception as e:
            # logger.warning(f"JINA分割失败，切换到本地分割器: {str(e)}")
            try:
                # return TextInputHandler._split_document(text, max_chunk_length)
                # 使用本地分割器作为后备方案
                doc = Document(text=text, metadata={})
                parser = SentenceSplitter(
                    chunk_size=max_chunk_length,
                    chunk_overlap=50,
                    separator=" ",
                    paragraph_separator="\n\n",
                )
                # 获取初始分块
                initial_nodes = parser.get_nodes_from_documents([doc])
                logger.info(f"本地分割初步切分成 {len(initial_nodes)} 个chunk")
                # 合并短句，确保语义完整性
                merged_nodes = []
                current_text = []
                current_length = 0
                for node in initial_nodes:
                    # merged_nodes.append(node.text)
                    # 不合并 则只保留这一行并 return merged_nodes
                    # 对于小型文件 不应合并 以保留足够多的chunk，大型文件 需要合并 以减少chunk
                    # 这个小型大型的阈值需要测试
                    
                    # 如果当前句子很短，尝试与下一句合并
                    if len(node.text.split()) < 10 and current_length < max_chunk_length:
                        current_text.append(node.text)
                        current_length += len(node.text.split())
                    else:
                        # 如果积累了一些短句，将它们合并
                        if current_text:
                            merged_text = " ".join(current_text)
                            merged_nodes.append(merged_text)
                            current_text = []
                            current_length = 0
                        # 将当前句子作为独立的块
                        merged_nodes.append(node.text)
                # 处理剩余的短句
                if current_text:
                    merged_text = " ".join(current_text)
                    merged_nodes.append(merged_text)
                logger.info(f"本地分割最终切分成 {len(merged_nodes)} 个chunk")
                return merged_nodes
            except Exception as e:
                logger.error(f"本地分割失败，使用简单长度分割: {str(e)}")
                # 如果本地分割也失败，使用最简单的长度分割作为最后的后备方案
                return [text[i:i+max_chunk_length] for i in range(0, len(text), max_chunk_length)]
        except Exception as e:
            logger.error(f"分割文本失败: {str(e)}")
            return []

    def _split_document_old(text: str, max_chunk_length: int = 500) -> List[NodeWithScore]:
        """智能分割文档，生成语义完整的黄金块
        Args:
            doc: 输入文档
        Returns:
            List[NodeWithScore]: 黄金块列表
        """
        doc = Document(text=text, metadata={})
        from llama_index.core.node_parser import SentenceSplitter
        # 使用句子级别的分割器
        parser = SentenceSplitter(
            chunk_size=max_chunk_length,
            chunk_overlap=50,
            separator=" ",
            paragraph_separator="\n\n",
        )
        # 获取初始分块
        try:
            initial_nodes = parser.get_nodes_from_documents([doc])
            logger.info(f"本地分割初步切分成 {len(initial_nodes)} 个chunk")
        except Exception as e:
            logger.error(f"Failed to split document: {str(e)}")
        # 合并短句，确保语义完整性
        merged_nodes = []
        current_text = []
        current_length = 0
        for node in initial_nodes:
            # 如果当前句子很短，尝试与下一句合并
            if len(node.text.split()) < 10 and current_length < max_chunk_length:
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
        logger.info(f"本地分割最终切分成 {len(merged_nodes)} 个chunk")
        return merged_nodes

# Example usage
if __name__ == "__main__":
    import embeddings.jina as jina # 测试时打开
    import asyncio

    async def main(filepath = None):
        sample_text = ''
        if not filepath:
            sample_text = "This is a SAMPLE text, with Special Characters! \n 这是一个 示例文本，带有特殊字符"
        else:
            with open(filepath, 'r', encoding='utf-8') as f:
                sample_text = f.read()
        # processed_text = TextInputHandler.preprocess_text(sample_text)
        # print(processed_text)  # Output: "this is a sample text with special characters"
        chunks = await TextInputHandler.split_text(sample_text)
        # print(chunks)
    # asyncio.run(main())
    asyncio.run(main("C:/Users/SWIFT/Desktop/temp/accouting.txt"))

