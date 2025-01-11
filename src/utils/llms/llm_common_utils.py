import os
import sys
import json
import logging
from typing import List, Dict, Any
from datetime import datetime

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)

logger = logging.getLogger(__name__)

class LLMCommonUtils:
    """LLM通用工具类"""
    
    @classmethod
    def _get_system_prompt(cls) -> str:
        """获取包含当前时间的完整系统提示词
        Returns:
            str: 完整的系统提示词
        """
        try:
            # 从环境变量获取提示词
            system_prompt_i = os.getenv("SYSTEM_PROMPT_I", "")
            system_prompt_ii = os.getenv("SYSTEM_PROMPT_II", "")
            # 添加当前时间
            system_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000Z')
            system_prompt_iii = f"`<|current_time|>{system_time}<|current_time|>`"
            # 添加记忆
            try:
                from src.utils.memory.memory_service import NotionMemoryService
                memories = NotionMemoryService().get_memories()
                logger.info(f"Got memories: {len(memories)} chars")
                if memories:
                    system_prompt_i += memories
            except Exception as e:
                logger.error(f"Error getting memories: {str(e)}")
            # 组合提示词
            final_prompt = system_prompt_i + system_prompt_ii + system_prompt_iii
            # 记录日志
            logger.info("SYSTEM_PROMPT: " + final_prompt[:100] + "..." + final_prompt[-100:])
            return final_prompt
        except Exception as e:
            logger.error(f"Error in _get_system_prompt: {str(e)}")
            return ""

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
    def format_response(cls, response: str) -> dict:
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