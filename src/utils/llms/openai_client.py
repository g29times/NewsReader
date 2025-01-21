# https://github.com/chatanywhere/GPT_API_free
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
from src import OPENAI_MODELS
from src.utils.llms.llm_common_utils import LLMCommonUtils

# 配置日志
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

class OpenAIClient:
    
    def __init__(self):
        """OpenAI API客户端"""
        self.API_KEY = os.getenv('OPENAI_API_KEY')
        self.API_BASE = os.getenv('OPENAI_API_BASE')
        self.MODEL = OPENAI_MODELS[0]
        self.max_tokens = os.getenv("LLM_MAX_TOKENS_NORMAL")
        self.temperature = os.getenv("LLM_TEMPERATURE")
        self.top_p = os.getenv("LLM_TOP_P")
        self.client = None

    def get_client(self, api_key: str = None, base_url: str = None) -> OpenAI:
        """获取OpenAI客户端实例"""
        if self.client is None:
            self.client = OpenAI(
                api_key=api_key or self.API_KEY,
                base_url=base_url or self.API_BASE
            )
        return self.client

    def _chat_complete(self, messages: List[dict], model: str = None, api_key: str = None, base_url: str = None) -> Optional[str]:
        """GPT API流式调用
        Args:
            messages: 消息列表
        Returns:
            str: 响应内容
        """
        try:
            # 创建聊天完成
            response = self.get_client(api_key, base_url).chat.completions.create(
                model=model or self.MODEL,
                messages=messages,
                stream=True,
                max_tokens=int(self.max_tokens),
                temperature=float(self.temperature),
                top_p=float(self.top_p),
            )
            # 处理流式响应
            content = ""
            for chunk in response:
                # print(chunk)
                if chunk.choices[0].delta.content:
                    content += chunk.choices[0].delta.content
            return content if content else None
        except Exception as e:
            logger.error(f"Error in _chat_complete: {str(e)}")
            raise e

    # 本方法是对chat方法的多次重试封装 其他方法该调用本方法
    def query_with_history(self, question: str, histories: List[Dict] = None, system_prompt: str = None, model: str = None, api_key: str = None, base_url: str = None) -> Dict:
        """使用历史记录查询
        Args:
            question: 问题
            histories: 历史记录
            system_prompt: 系统提示
        Returns:
            Dict: 响应结果
        """ 
        if base_url:
            logger.info("base_url: " + base_url)
        else:
            logger.info("base_url: " + self.API_BASE)
        if model:
            logger.info("MODEL: " + model)
        else:
            logger.info("MODEL: " + self.MODEL)
        if histories:
            logger.info("History: " + str(histories))
        # logger.info("Question: " + question[:100])
        if (len(question) > 200):
            logger.info("Question: " + question[:100] + " ..." + question[-100:])
        else:
            logger.info("Question: " + question)
        try:
            # 准备消息列表（OPENAI在这里设置系统提示词）
            messages = LLMCommonUtils._openai_format_msg(question, histories, system_prompt)
            # 添加重试机制
            for attempt in range(3):
                try:
                    content = self._chat_complete(messages, model, api_key, base_url)
                    if content:
                        if (len(content) > 200):
                            logger.info("Response: " + content[:100] + " ..." + content[-100:])
                        else:
                            logger.info("Response: " + content)
                        return content
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

if __name__ == '__main__':
    # hello world ok
    # messages = [{'role': 'user','content': '鲁迅和周树人的关系'},]
    # # 非流式调用
    # # gpt_api(messages)
    # # 流式调用
    # response = OpenAIClient._chat_complete(messages)
    # print(response)

    # ok
    # google_messages = [
    #     {"role": "user", "parts": ["讲个笑话？"]},
    #     {"role": "model", "parts": ["有只猴子在树上"]},
    # ]
    history = [{"role": "user", "content": "晚安，GEMI"},{"role": "assistant", "content": "晚安，Neo"}]
    opoenai = OpenAIClient()
    response = opoenai.query_with_history("早上好，GEMI", history, "GEMI智能助理是Neo的大型语言模型助手。")


# demo https://github.com/chatanywhere/GPT_API_free
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