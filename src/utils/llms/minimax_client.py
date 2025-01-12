# https://platform.minimaxi.com/examination-center/text-experience-center/cc_v2
import requests
import os
import re
import logging
import sys
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional, Tuple, Union

# 添加项目根目录到 Python 路径 标准方式
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)
from src.utils.llms.openai_client import OpenAIClient
from src.utils.llms.llm_common_utils import LLMCommonUtils

load_dotenv()
logger = logging.getLogger(__name__)

group_id = "1752243208567398407"
api_key = os.getenv("MINIMAX_API_KEY")

class MinimaxClient:
    
    default_system_prompt = "GEMI智能助理是Neo的大型语言模型助手。"
    max_tokens = os.getenv("LLM_MAX_TOKENS")
    temperature = os.getenv("LLM_TEMPERATURE")
    top_p = os.getenv("LLM_TOP_P")

    @classmethod
    def chat_completion(cls, messages: List[dict], max_tokens: int = 8192, temperature: float = 0.9) -> Optional[str]:
        url = f"https://api.minimax.chat/v1/text/chatcompletion_v2?GroupId={group_id}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": os.getenv("MINIMAX_MODEL"),
            "messages": messages,
            "stream": False,
            "max_tokens": max_tokens or int(cls.max_tokens),
            "temperature": temperature or float(cls.temperature),
            "top_p": float(cls.top_p)
        }
        response = requests.post(url, headers=headers, json=payload)
        return response.json()

    def __init__(self):
        """Minimax API客户端"""
        self.API_KEY = os.getenv('MINIMAX_API_KEY')
        self.API_BASE = os.getenv('MINIMAX_API_BASE')
        self.MODEL = os.getenv('MINIMAX_MODEL')

    def query_openai_with_history(self, question: str, history: List[dict], system_prompt: str = ""):
        openai = OpenAIClient()
        return openai.query_with_history(question, history, system_prompt, 
            self.MODEL, self.API_KEY, self.API_BASE)

    def query_with_history(self, question: str, history: List[dict], system_prompt: str = ""):
        return self.chat_completion(
            LLMCommonUtils._openai_format_msg(question, history, system_prompt),
            max_tokens=int(self.max_tokens),
            temperature=float(self.temperature)
        )

if __name__ == "__main__":
    # 1 原生demo
    # url = f"https://api.minimax.chat/v1/text/chatcompletion_v2?GroupId={group_id}"
    # headers = {
    #     "Authorization": f"Bearer {api_key}",
    #     "Content-Type": "application/json"
    # }
    # payload = {
    # "model": "abab7-chat-preview",
    # "messages": [
    #     {
    #     "content": "GEMI智能助理是Neo的大型语言模型助手。",
    #     "role": "system",
    #     "name": "GEMI"
    #     },
    #     {
    #     "content": "你好，GEMI",
    #     "role": "user",
    #     "name": "NEO"
    #     },
    #     {
    #     "content": "你好，Neo",
    #     "role": "assistant",
    #     "name": "GEMI"
    #     },
    #     {
    #     "content": "早上好，GEMI",
    #     "role": "user",
    #     "name": "NEO"
    #     }
    # ],
    # "stream": False,
    # "max_tokens": 8192,
    # "temperature": 0.9,
    # "top_p": 0.95
    # }
    # response = requests.post(url, headers=headers, json=payload)
    # print(response.status_code)
    # print(response.text)
    
    # 1 原生API封装
    minimax = MinimaxClient()
    history = [{"role": "user", "content": "晚安，GEMI"},{"role": "assistant", "content": "晚安，Neo"}]
    print(minimax.query_with_history("早上好，GEMI", history, "GEMI智能助理是Neo的大型语言模型助手。"))

    # 2 调用OpenAI DEMO https://platform.minimaxi.com/document/ChatCompletion%20v2?key=66701d281d57f38758d581d0#1XspWaYA7baUnFix0otJIQkt
    # from openai import OpenAI
    # client = OpenAI(api_key=api_key, base_url="https://api.minimax.chat/v1")
    # response = client.chat.completions.create(
    #     model="abab6.5t-chat",
    #     messages=[
    #         {"role": "system", "content": "GEMI智能助理是Neo的大型语言模型助手。"},
    #         {"role": "user", "content": "晚安，GEMI"},
    #         {"role": "assistant", "content": "晚安，Neo"},
    #         {"role": "user", "content": "早上好，GEMI"}
    #     ],
    #     stream=True
    # )
    # for chunk in response:
    #     print(chunk)

    # 2 调用OpenAI封装
    minimax.query_openai_with_history("现在几点了，Gemi", history, LLMCommonUtils._get_time_prompt())
    
    # 3 测试 记忆
    # print(LLMCommonUtils._get_memory_prompt())
    # minimax.query_openai_with_history("GEMI执行记忆管理", history, LLMCommonUtils._get_memory_prompt())
    
    # 4 测试 文本总结
    # content = "2024 年在年初被称为“RAG 发展元年”，虽然这并非共识性的说法，但事实证明，全年的进展无愧于这一称号。在LLM 使用的场景中，RAG 自始至终都在扮演着不可或缺的重要角色。然而，自诞生以来关于 RAG 的争论就没有停止过。由上图可以看到，2023 年 RAG 的称呼并不流行，一种看起来就非常临时的说法“外挂记忆体”、“外挂知识库”是普遍的替代称谓，在当时，主要争论还在于究竟应该用临时的“外挂”还是“永久性的”微调，这个争论在 2024 年初已经终结：从成本和实时性角度，RAG 具有压倒性优势，而效果上相差也并不大，即使需要微调介入的场景，RAG  通常也不可或缺。"
    # minimax.query_openai_with_history(question=f"```{content}```", history=[], system_prompt=os.getenv("SUMMARY_PROMPT"))