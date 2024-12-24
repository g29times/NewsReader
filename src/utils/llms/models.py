"""LLM 相关的数据模型"""

from typing import Dict, Any
from dataclasses import dataclass, field


@dataclass
class LLMResponse:
    """LLM响应的数据类"""
    state: str = "SUCCESS"  # LLM 服务提供方 API 返回状态 "SUCCESS" "ERROR"
    desc: str = ""  # LLM 服务提供方 API 返回的描述信息或自定义错误描述
    body: dict = field(default_factory=dict)  # LLM 服务提供方 API 返回的原始内容
    status_code: int = 200 # LLM 服务提供方 API 原始返回的状态码 200 300 400 500 等