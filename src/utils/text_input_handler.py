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
import src.utils.embeddings.jina as jina

import logging
logger = logging.getLogger(__name__)

class TextInputHandler:
    """
    Handler for processing text input for LLM processing
    """
    # 文本清洗 
    @staticmethod
    def preprocess_text(text):
        """
        Preprocess text data by cleaning and formatting
        """
        try:
            # Remove [Image xxx](https://...) and [Image xxx: Image](https://...) type links
            # text = re.sub(r'\[Image\s*\d+(:?\s*Image)?\]\((https?:\/\/[^\s]+)\)', '', text)

            # Remove [Image xxx](https://...) and [Image xxx: Image](https://...) type links, allowing spaces and newlines inside the link
            text = re.sub(r'\[Image\s*\d+(:?\s*Image)?\]\(([\s\S]*?)\)', '', text)

            # # Remove HTML tags
            # text = re.sub(r'<[^>]*>', '', text)

            # Remove (image) type links
            text = re.sub(r'\((image)\)', '', text, flags=re.IGNORECASE)

            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text)

            # Remove leading and trailing whitespace
            text = text.strip()

        except Exception as e:
            logger.error(f"文本预处理异常：{e}")
        # logger.info(f"文本预处理后：{text}")
        logger.info(f"文本预处理后：{len(text)}")
        return text

    # 本地文本分割：简单按长度切分
    @staticmethod
    def split_text_simple(text: str, max_chunk_length: int = 1000) -> List[str]:
        return [text[i:i+max_chunk_length] for i in range(0, len(text), max_chunk_length)]

    # 文本长短父子分割：返回大块，小块，以及小块到大块的id映射
    @staticmethod
    async def split_text(text: str, max_chunk_length: int = 1000, chunk_overlap: int = 100) -> Tuple[List[str], List[str], Dict[int, int]]:
        max_node_length = max_chunk_length - chunk_overlap
        nodes = []
        nodes = await jina.split_text_with_jina(TextInputHandler.preprocess_text(text), max_chunk_length)
        logger.info(f"文章长度：{len(text)}，JINA分割初步切分成 {len(nodes)} 个chunk")
        # 合并短句，确保语义完整性
        big_chunks = []
        current_text = []
        current_length = 0
        small_big_dict = {} # node_id: big_chunk_id
        big_chunk_id = 0
        for i, node in enumerate(nodes):
            # 如果当前句子很短，尝试与下一句合并
            node_length = len(node)
            if node_length < max_node_length and current_length + node_length < max_chunk_length:
                current_text.append(node)
                current_length += node_length
                small_big_dict.update({i: big_chunk_id}) # NEW
            else:
                # 如果积累了一些短句，将它们合并
                if current_text:
                    merged_text = " ".join(current_text)
                    big_chunks.append(merged_text)
                    current_text = []
                    current_length = 0
                    big_chunk_id += 1  # NEW
                # 将当前句子作为独立的块
                # big_chunks.append(node)
                current_text.append(node) # NEW
                current_length = node_length # NEW
                small_big_dict.update({i: big_chunk_id}) # NEW
        # 处理剩余的短句
        if current_text:
            merged_text = " ".join(current_text)
            big_chunks.append(merged_text)
        logger.info(f"最终合并成 {len(big_chunks)} 个chunk")
        return big_chunks, nodes, small_big_dict

    # 文本分割：使用JINA API + 本地分割
    @staticmethod
    async def split_text_old(text: str, max_chunk_length: int = 1000, chunk_overlap: int = 100) -> List[str]:
        """智能分割文本，优先使用JINA API，失败时自动切换到本地分割器
        Args:
            text: 要分割的文本
            max_chunk_length: 最大块长度
        Returns:
            List[str]: 分割后的文本块列表
        """
        try:
            try: # TODO
                # JINA API 分的比较细 句子级别 小
                small_chunks = await jina.split_text_with_jina(text, max_chunk_length)
                if small_chunks:  # 如果成功获取到分块
                    logger.info(f"JINA分割成功，切分成 {len(small_chunks)} 个chunk")
                    return small_chunks
            except Exception as e:
                logger.warning(f"JINA分割失败，切换到本地分割器: {str(e)}")
            try:
                # return TextInputHandler._split_document(text, max_chunk_length)
                # 使用本地分割器作为大块
                doc = Document(text=text, metadata={})
                parser = SentenceSplitter(
                    chunk_size=max_chunk_length,
                    chunk_overlap=chunk_overlap,
                    separator=" ",
                    paragraph_separator="\n\n",
                )
                # 获取初始分块
                initial_nodes = parser.get_nodes_from_documents([doc])
                logger.info(f"本地分割初步切分成 {len(initial_nodes)} 个chunk")
                # 合并短句，确保语义完整性
                big_chunks = []
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
                        big_chunks.append(node.text)
                # 处理剩余的短句
                if current_text:
                    merged_text = " ".join(current_text)
                    big_chunks.append(merged_text)
                logger.info(f"本地分割最终切分成 {len(big_chunks)} 个chunk")
                return big_chunks
            except Exception as e:
                logger.error(f"本地分割失败，使用简单长度分割: {str(e)}")
                # 如果本地分割也失败，使用最简单的长度分割作为最后的后备方案
                return [text[i:i+max_chunk_length] for i in range(0, len(text), max_chunk_length)]
        except Exception as e:
            logger.error(f"分割文本失败: {str(e)}")
            return []

    @staticmethod
    def is_media(url: str) -> bool:
        """
        判断URL是否指向媒体文件（图片、视频、音频等）
        """
        # 常见媒体文件扩展名
        media_extensions = {
            # 图片
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg',
            # 视频
            '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm',
            # 音频
            '.mp3', '.wav', '.ogg', '.m4a', '.aac'
        }
        
        try:
            # 将URL转为小写以进行不区分大小写的匹配
            url_lower = url.lower()
            # 检查URL是否以任何媒体扩展名结尾
            return any(url_lower.endswith(ext) for ext in media_extensions)
        except Exception as e:
            logger.error(f"URL媒体类型检查异常：{e}")
            return False

    @staticmethod
    def generate_dataset(filepath: str, output_path: str, max_chunk_length: int = 1000):
        """生成评估数据集
        Args:
            filepath: 输入文件路径
            output_path: 输出JSON文件路径
            max_chunk_length: 每个chunk的最大长度
        """
        import json
        
        # 读取文件
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # 切分文本
        chunks = TextInputHandler.split_text_simple(text, max_chunk_length)
        print(f"切分成 {len(chunks)} 个chunk")
        
        # 生成数据集格式
        dataset = []
        for i, chunk in enumerate(chunks):
            item = {
                "id": i,
                "question": "",
                "answer": "",
                "golden_chunk": chunk
            }
            dataset.append(item)
        
        # 保存为JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)
        
        logger.info(f"已生成数据集，共{len(chunks)}条记录，保存至：{output_path}")

# Example usage
if __name__ == "__main__":
    import embeddings.jina as jina # 测试时打开
    import asyncio

    async def main(filepath = None):
        sample_text = ''
        if not filepath:
            sample_text = "This is a SAMPLE text, with Special Characters! \n 这是一个 示例文本，带有特殊字符。"
        else:
            with open(filepath, 'r', encoding='utf-8') as f:
                sample_text = f.read()
        chunks, nodes, small_big_dict = await TextInputHandler.split_text(sample_text, 10, 2)
        print(chunks)
        print(nodes)
    asyncio.run(main())

    #         # 输出到json
    #         handler = TextInputHandler()
    #         handler.generate_dataset(filepath, "output_dataset.json", 1000)
    # asyncio.run(main("C:/Users/SWIFT/Desktop/temp1/accouting.txt"))
