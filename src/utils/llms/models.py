"""LLM 相关的数据模型"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class LLMResponse:
    """LLM响应的数据类"""
    state: str  # SUCCESS 或 ERROR
    desc: str  # 状态描述
    body: Dict[str, Any]  # 响应内容
    status_code: int = 200  # LLM 服务提供方 API 原始返回的状态码 200 300 400 500 等
