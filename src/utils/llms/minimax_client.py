# https://platform.minimaxi.com/examination-center/text-experience-center/cc_v2
import requests
import os
import re
import logging
import sys
import time
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional, Tuple, Union

# 添加项目根目录到 Python 路径 标准方式
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)
from src import MINIMAX_MODELS
from src.utils.llms.openai_client import OpenAIClient
from src.utils.llms.llm_common_utils import LLMCommonUtils

load_dotenv()
logger = logging.getLogger(__name__)

class MinimaxClient:
    
    def __init__(self):
        """Minimax API客户端"""
        self.API_KEY = os.getenv('MINIMAX_API_KEY')
        self.GROUP_ID = os.getenv('MINIMAX_GROUP_ID')
        self.API_BASE = os.getenv('MINIMAX_API_BASE')
        self.OPENAI_BASE = os.getenv('MINIMAX_OPENAI_BASE')
        self.MODEL = MINIMAX_MODELS[0]  # 默认使用第一个模型
        self.max_tokens = os.getenv("LLM_MAX_TOKENS_NORMAL")
        self.temperature = os.getenv("LLM_TEMPERATURE")
        self.top_p = os.getenv("LLM_TOP_P")

    def _chat_complete(self, messages: List[dict], max_tokens: int = None, temperature: float = None) -> Optional[str]:
        try:
            url = f"{self.API_BASE}?GroupId={self.GROUP_ID}"
            headers = {
                "Authorization": f"Bearer {self.API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.MODEL,
                "messages": messages,
                "stream": False,
                "max_tokens": max_tokens or int(self.max_tokens),
                "temperature": temperature or float(self.temperature),
                "top_p": float(self.top_p)
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
                    response = self._chat_complete(messages)
                    if response:
                        content = response
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
    # 1 原生API封装 https://platform.minimaxi.com/examination-center/text-experience-center/cc_v2
    minimax = MinimaxClient()
    history = [{"role": "user", "content": "晚安，GEMI"},{"role": "assistant", "content": "晚安，Neo"}]
    minimax.query_with_history("早上好，GEMI", history, "GEMI智能助理是Neo的大型语言模型助手。")

    # 2 调用OpenAI封装 https://platform.minimaxi.com/document/ChatCompletion%20v2
    minimax.query_openai_with_history("现在几点了，Gemi", history, LLMCommonUtils._get_time_prompt())
    
    # 3 测试 记忆
    # print(LLMCommonUtils._get_memory_prompt())
    # minimax.query_openai_with_history("GEMI执行记忆管理", history, LLMCommonUtils._get_memory_prompt())
    
    # 4 测试 文本总结
    # content = "2024 年在年初被称为“RAG 发展元年”，虽然这并非共识性的说法，但事实证明，全年的进展无愧于这一称号。在LLM 使用的场景中，RAG 自始至终都在扮演着不可或缺的重要角色。然而，自诞生以来关于 RAG 的争论就没有停止过。由上图可以看到，2023 年 RAG 的称呼并不流行，一种看起来就非常临时的说法“外挂记忆体”、“外挂知识库”是普遍的替代称谓，在当时，主要争论还在于究竟应该用临时的“外挂”还是“永久性的”微调，这个争论在 2024 年初已经终结：从成本和实时性角度，RAG 具有压倒性优势，而效果上相差也并不大，即使需要微调介入的场景，RAG  通常也不可或缺。"
    # minimax.query_openai_with_history(question=f"```{content}```", history=[], system_prompt=os.getenv("SUMMARY_PROMPT"))