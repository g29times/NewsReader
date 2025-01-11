from math import log
import os
import sys
import json
import logging
from typing import List, Optional, Any, Dict
from dotenv import load_dotenv
import openai
from openai import OpenAI
import time

# 添加项目根目录到 Python 路径 标准方式
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)
from src.utils.llms.llm_common_utils import LLMCommonUtils

# 添加项目根目录到 Python 路径 标准方式
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)

# 配置日志
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

class OpenAIClient:
    """OpenAI API客户端"""
    API_KEY = os.getenv('OPENAI_API_KEY')
    API_BASE = os.getenv('OPENAI_API_BASE')
    MODEL = os.getenv('OPENAI_MODEL')
    client = None

    @classmethod
    def get_client(cls) -> OpenAI:
        """获取OpenAI客户端实例"""
        if cls.client is None:
            cls.client = OpenAI(
                api_key=cls.API_KEY,
                base_url=cls.API_BASE
            )
        return cls.client

    @classmethod
    def gpt_api_stream(cls, messages: List[dict]) -> Optional[str]:
        """GPT API流式调用
        Args:
            messages: 消息列表
        Returns:
            str: 响应内容
        """
        try:
            # 创建聊天完成
            response = cls.get_client().chat.completions.create(
                model=cls.MODEL,
                messages=messages,
                stream=True
            )
            
            # 处理流式响应
            content = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content += chunk.choices[0].delta.content
            
            return content if content else None
            
        except Exception as e:
            logger.error(f"Error in gpt_api_stream: {str(e)}")
            raise e

    @classmethod
    def query_with_history(cls, question: str, histories: List[Dict] = None, files: List[str] = None) -> Dict:
        """使用历史记录查询
        Args:
            question: 问题
            histories: 历史记录
            files: 文件列表
        Returns:
            Dict: 响应结果
        """ 
        logger.info("MODEL: " + cls.MODEL)
        logger.info("Question: " + question)
        logger.info("History: " + str(histories))
        try:
            # 准备消息列表
            messages = cls._prepare_messages(question, histories)
            
            # 添加重试机制
            for attempt in range(3):
                try:
                    content = cls.gpt_api_stream(messages)
                    
                    if content:
                        logger.info("OpenAI query successful")
                        return {
                            "candidates": [
                                {
                                    "content": {
                                        "parts": [content]
                                    }
                                }
                            ]
                        }
                    else:
                        logger.warning(f"Empty response on attempt {attempt + 1}")
                        if attempt < 2:
                            time.sleep(5)  # 等待5秒后重试
                            continue
                        return None
                        
                except Exception as e:
                    logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                    if attempt < 2:
                        time.sleep(5)  # 等待5秒后重试
                        continue
                    return None
                    
        except Exception as e:
            logger.error(f"Error in query_with_history: {str(e)}")
            return None

    @classmethod
    def _prepare_messages(cls, question: str, histories: List[Dict]) -> List[Dict]:
        messages = []
        
        # 获取系统提示词
        messages.append({"role": "system", "content": LLMCommonUtils._get_system_prompt()})
        
        # 格式化历史记录
        messages.extend(LLMCommonUtils.turn_gemini_format_to_openai(histories))
        
        # 添加当前问题
        messages.append({"role": "user", "content": question})
        
        return messages

if __name__ == '__main__':
    # hello world ok
    # messages = [{'role': 'user','content': '鲁迅和周树人的关系'},]
    # # 非流式调用
    # # gpt_api(messages)
    # # 流式调用
    # response = OpenAIClient.gpt_api_stream(messages)
    # print(response)

    # ok
    messages = [
        {"role": "user", "parts": ["讲个笑话？"]},
        {"role": "model", "parts": ["有只猴子在树上"]},
    ]
    response = OpenAIClient.query_with_history("GEMI执行记忆管理", messages)
    print(response)


# from openai import OpenAI
# import os
# from dotenv import load_dotenv

# # 加载环境变量
# load_dotenv()

# client = OpenAI(
#     # defaults to os.environ.get("OPENAI_API_KEY")
#     api_key= os.getenv('OPENAI_API_KEY'),
#     base_url=os.getenv('OPENAI_API_BASE')
# )

# def gpt_35_api_stream(messages: list):
#     """为提供的对话消息创建新的回答 (流式传输)

#     Args:
#         messages (list): 完整的对话消息
#     """
#     stream = client.chat.completions.create(
#         model='gpt-3.5-turbo',
#         messages=messages,
#         stream=True,
#     )
#     for chunk in stream:
#         if chunk.choices[0].delta.content is not None:
#             print(chunk.choices[0].delta.content, end="")