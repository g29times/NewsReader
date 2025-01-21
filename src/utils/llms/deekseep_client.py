import os
import time
import logging
import sys
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
import requests

# 添加项目根目录到 Python 路径 标准方式
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)

# 配置日志
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

from src import DEEPSEEK_MODELS
from src.utils.llms.openai_client import OpenAIClient
from src.utils.llms.llm_common_utils import LLMCommonUtils

class DeepseekClient:
    
    def __init__(self):
        """Deepseek API客户端"""
        self.API_KEY = os.getenv('DEEPSEEK_API_KEY')
        self.API_BASE = os.getenv('DEEPSEEK_API_BASE')
        self.OPENAI_BASE = os.getenv('DEEPSEEK_OPENAI_BASE')
        self.MODEL = DEEPSEEK_MODELS[0]  # 默认使用第一个模型
        self.max_tokens = os.getenv("LLM_MAX_TOKENS_NORMAL")
        self.temperature = os.getenv("LLM_TEMPERATURE")
        self.top_p = os.getenv("LLM_TOP_P")
        self.client = None

    def rest_demo(self):
        import json

        url = "https://api.deepseek.com/chat/completions"

        payload = json.dumps({
        "messages": [
            {
            "content": "You are a helpful assistant",
            "role": "system"
            },
            {
            "content": "Hi",
            "role": "user"
            }
        ],
        "model": "deepseek-chat",
        "frequency_penalty": 0,
        "max_tokens": 2048,
        "presence_penalty": 0,
        "response_format": {
            "type": "text"
        },
        "stop": None,
        "stream": False,
        "stream_options": None,
        "temperature": 1,
        "top_p": 1,
        "tools": None,
        "tool_choice": "none",
        "logprobs": False,
        "top_logprobs": None
        })
        headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Bearer <TOKEN>'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        print(response.text)

    def _chat_complete(self, messages: List[dict], max_tokens: int = None, temperature: float = None) -> Optional[str]:
        try:
            url = self.API_BASE
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': f'Bearer {self.API_KEY}'
            }
            payload = {
                "model": self.MODEL,
                "messages": messages,
                "frequency_penalty": 0,
                "max_tokens": max_tokens or int(self.max_tokens),
                "presence_penalty": 0,
                "response_format": {"type": "text"},
                "stop": None,
                "stream": False,
                "stream_options": None,
                "temperature": temperature or float(self.temperature),
                "top_p": float(self.top_p),
                "tools": None,
                "tool_choice": "none",
                "logprobs": False,
                "top_logprobs": None
            }
            response = requests.post(url, headers=headers, json=payload)
            return response.json()
        except Exception as e:
            logger.error(f"Error in _chat_complete: {str(e)}")
            raise e

    def query_with_history(self, question: str, histories: List[Dict] = None, system_prompt: str = None) -> Optional[str]:
        logger.info(f"MODEL: {self.MODEL}")
        if histories:
            logger.info(f"History: {str(histories)}")
        if len(question) > 200:
            logger.info(f"Question: {question[:100]} ... {question[-100:]}")
        else:
            logger.info(f"Question: {question}")
        try:
            messages = LLMCommonUtils._openai_format_msg(question, histories, system_prompt)
            for attempt in range(3):
                try:
                    content = self._chat_complete(messages)
                    if content:
                        if len(content) > 200:
                            logger.info(f"Response: {content[:100]} ... {content[-100:]}")
                        else:
                            logger.info(f"Response: {content}")
                        return content
                    else:
                        logger.warning(f"Empty response on attempt {attempt + 1}")
                        if attempt < 2:
                            time.sleep(5)
                            continue
                        return None
                except Exception as e:
                    logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                    if attempt < 2:
                        time.sleep(5)
                        continue
                    return None
        except Exception as e:
            logger.error(f"Error in query_with_history: {str(e)}")
            return None

    def query_openai_with_history(self, question: str, histories: List[Dict] = None, system_prompt: str = None) -> Optional[str]:
        """使用OpenAI格式的历史记录查询
        Args:
            question: 问题
            histories: 历史记录
            system_prompt: 系统提示
        Returns:
            str: 响应内容
        """
        openai = OpenAIClient()
        return openai.query_with_history(question, histories, system_prompt, self.MODEL, self.API_KEY, self.OPENAI_BASE)

if __name__ == "__main__":
    # 1 原生API封装 https://api-docs.deepseek.com/zh-cn/api/create-chat-completion
    deepseek = DeepseekClient()
    history = [{"role": "user", "content": "晚安，GEMI"},{"role": "assistant", "content": "晚安，Neo"}]
    deepseek.query_with_history("早上好，GEMI", history, "GEMI智能助理是Neo的大型语言模型助手。")

    # 2 OpenAI格式调用
    deepseek.query_openai_with_history("现在几点了，Gemi", history, LLMCommonUtils._get_time_prompt())