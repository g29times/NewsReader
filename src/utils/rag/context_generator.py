import os
import logging
from typing import Dict, List, Optional
from google.generativeai import GenerativeModel
from google.generativeai.types import GenerateContentResponse

# 配置日志
logger = logging.getLogger(__name__)

class ContextGenerator:
    """使用Claude/Gemini为文档chunk生成上下文描述"""
    
    def __init__(self, model_name: str = "gemini"):
        """初始化上下文生成器
        
        Args:
            model_name: 使用的模型名称，默认为gemini
        """
        self.model = GenerativeModel(model_name)
    
    # 暂未启用 使用了evalset中的answer作为context
    def generate_context(self, chunk_content: str, document_content: str) -> str:
        """为chunk生成上下文描述
        
        Args:
            chunk_content: chunk的内容
            document_content: 完整文档的内容
            
        Returns:
            str: 生成的上下文描述
        """
        try:
            # 构建提示词
            prompt = f"""
                <document>
                {document_content}
                </document>

                Here is the chunk we want to situate within the whole document:
                <chunk>
                {chunk_content}
                </chunk>

                Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else. Keep the context under 100 tokens.

                Example:
                    original_chunk = "The company's revenue grew by 3% over the previous quarter."
                    contextualized_chunk = "This chunk is from an SEC filing on ACME corp's performance in Q2 2023; the previous quarter's revenue was $314 million. The company's revenue grew by 3% over the previous quarter."
            """
            # 调用模型生成上下文
            response = self.model.generate_content(prompt)
            
            if not response.text:
                logger.warning(f" -------------------------- Empty context generated for chunk")
                return ""
                
            # 返回生成的上下文
            return response.text.strip()
            
        except Exception as e:
            logger.error(f" -------------------------- Failed to generate context: {str(e)}")
            return ""
            
    def add_context_to_chunk(self, chunk_content: str, context: str) -> str:
        """将上下文添加到chunk中
        
        Args:
            chunk_content: chunk的原始内容
            context: 生成的上下文描述
            
        Returns:
            str: 添加了上下文的chunk内容
        """
        if not context:
            return f"Content: {chunk_content}"
            
        # 将上下文作为前缀添加到chunk
        return f"Context: {context}\n\nContent: {chunk_content}"
