import os
import sys
import json
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
import re

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)
from src.utils.llms.models import LLMResponse

logger = logging.getLogger(__name__)

class LLMCommonUtils:
    """LLM通用工具类"""
    
    @classmethod
    def _get_time(cls):
        now = datetime.now()# 加上8小时
        time_plus_8_hours = now + timedelta(hours=4)
        # 格式化为 ISO 8601 格式
        return time_plus_8_hours.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    
    # 获取简单的系统时间提示词
    @classmethod
    def _get_time_prompt(cls) -> str:# 获取当前时间
        system_prompt_i = os.getenv("SYSTEM_PROMPT", "")
        system_prompt_ii = os.getenv("MEMORY_PROMPT_II", "")
        system_time = cls._get_time()
        system_prompt_iii = f"`<|current_time|>{system_time}<|current_time|>`"
        final_prompt = system_prompt_i + system_prompt_ii + system_prompt_iii
        # 记录日志
        logger.info("SYSTEM_PROMPT: " + final_prompt)
        return final_prompt
    
    # 获取复杂的个性化记忆管理提示词
    @classmethod
    def _get_memory_prompt(cls) -> str:
        """个性化记忆管理提示词"""
        try:
            # 从环境变量获取提示词
            system_prompt_i = os.getenv("MEMORY_PROMPT_FULL", "")
            system_prompt_ii = os.getenv("MEMORY_PROMPT_II", "")
            # 添加当前时间
            system_time = cls._get_time()
            system_prompt_iii = f"`<|current_time|>{system_time}<|current_time|>`"
            # # 添加记忆
            # try:
            #     from src.utils.memory.memory_service import NotionMemoryService
            #     memories = NotionMemoryService().get_memories()
            #     if memories:
            #         logger.info(f"Got memories: {len(memories)} chars")
            #         system_prompt_i += memories
            # except Exception as e:
            #     logger.error(f"Error getting memories: {str(e)}")
            # 组合提示词
            final_prompt = system_prompt_i + system_prompt_ii + system_prompt_iii
            # 记录日志
            logger.info("MEMORY_PROMPT: " + final_prompt[:100] + "..." + final_prompt[-100:])
            return final_prompt
        except Exception as e:
            logger.error(f"Error in _get_memory_prompt: {str(e)}")
            return ""

    # 提取结构化信息 包含解析后的标题、摘要和关键词
    @classmethod
    def _extract_summary(cls, response: str) -> LLMResponse:
        try:
            # 使用正则表达式提取信息
            title = re.search(r'\[TITLE\](.*?)\[/TITLE\]', response, re.DOTALL)
            summary = re.search(r'\[SUMMARY\](.*?)\[/SUMMARY\]', response, re.DOTALL)
            key_topics = re.search(r'\[KEY_TOPICS\](.*?)\[/KEY_TOPICS\]', response, re.DOTALL)
            authors = re.search(r'\[AUTHORS\](.*?)\[/AUTHORS\]', response, re.DOTALL)
            publication_date = re.search(r'\[PUBLICATION_DATE\](.*?)\[/PUBLICATION_DATE\]', response, re.DOTALL)
            source = re.search(r'\[SOURCES\](.*?)\[/SOURCES\]', response, re.DOTALL)

            authors = authors.group(1).strip() if authors else ''
            if authors.startswith('NO'):
                authors = ''
            publication_date = publication_date.group(1).strip() if publication_date else ''
            if publication_date.startswith('NO'):
                publication_date = ''
            body = {
                'title': title.group(1).strip() if title else '',
                'summary': summary.group(1).strip() if summary else '',
                'key_topics': key_topics.group(1).strip() if key_topics else '',
                'authors': authors,
                'publication_date': publication_date,
                'source': source.group(1).strip() if source else '',
            }
            return LLMResponse(
                state="SUCCESS",
                desc="成功解析LLM响应",
                status_code=200,
                body=body
            )
        except Exception as e:
            logger.error(f"解析Gemini响应失败: {e}")
            return LLMResponse(
                state="ERROR",
                desc=f"解析响应失败: {str(e)}",
                status_code=500,
                body={}
            )

    # 将消息格式化为openai格式
    @classmethod
    def _openai_format_msg(cls, question: str, histories: List[Dict] = None, system_prompt: str = None) -> List[Dict]:
        """histories FORMAT:[{"role": "system", "content": ""},{"role": "user", "content": ""},{"role": "assistant", "content": ""}]"""
        messages = []
        # 获取系统提示词
        messages.append({"role": "system", "content": system_prompt or os.getenv("SYSTEM_PROMPT")})
        if histories:
            messages.extend(histories)
        # 添加当前问题
        messages.append({"role": "user", "content": question})
        return messages

    @classmethod
    def turn_gemini_format_to_openai(cls, messages: List[dict]) -> List[dict]:
        """格式化消息列表，统一不同LLM的消息格式
        Args:
            messages: 原始消息列表
        Returns:
            List[dict]: 格式化后的消息列表
        """
        formatted_messages = []
        for msg in messages:
            if msg.get("role") == "user":
                formatted_messages.append({
                    "role": "user",
                    "content": msg.get("parts", [""])[0]
                })
            elif msg.get("role") == "model":
                formatted_messages.append({
                    "role": "assistant",
                    "content": msg.get("parts", [""])[0]
                })
            elif msg.get("role") == "system":
                formatted_messages.append({
                    "role": "system",
                    "content": msg.get("parts", [""])[0]
                })
        return formatted_messages

    @classmethod
    def turn_openai_format_to_gemini(cls, response: str) -> dict:
        """格式化响应，统一不同LLM的响应格式
        Args:
            response: 原始响应文本
        Returns:
            dict: 格式化后的响应
        """
        return {
            "candidates": [{
                "content": {
                    "parts": [response],
                    "role": "model"
                }
            }]
        }

if __name__ == '__main__':
    print(LLMCommonUtils._get_time_prompt())
    # print(LLMCommonUtils._get_memory_prompt())
