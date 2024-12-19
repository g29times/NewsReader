import logging
import os
import sys
import re
from dataclasses import dataclass, field
from typing import Optional
from sqlalchemy.orm import Session

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(project_root)

import json
import re
import logging
from typing import Optional
from sqlalchemy.orm import Session

from .models import LLMResponse
from .gemini_client import GeminiClient
from models.article import Article

logger = logging.getLogger(__name__)

@dataclass
class LLMResponse:
    """LLM响应的数据类"""
    body: dict = field(default_factory=dict)  # LLM 服务提供方 API 返回的原始内容
    state: str = "SUCCESS"  # LLM 服务提供方 API 返回状态 "SUCCESS" "ERROR"
    desc: str = ""  # LLM 服务提供方 API 返回的描述信息或自定义错误描述
    status_code: int = 200 # LLM 服务提供方 API 原始返回的状态码 200 300 400 500 等

class LLMTasks:
    """处理各种LLM相关任务的类"""
    
    @staticmethod
    def summarize_and_key_points(content: str) -> LLMResponse:
        """
        使用LLM总结内容并提取关键点
        
        Args:
            content: 需要处理的文本内容
            
        Returns:
            LLMResponse 包含处理结果
        """
        # TODO: 未来可以根据配置选择不同的LLM提供商
        gemini = GeminiClient()
        return gemini.summarize_text(content)

    @staticmethod
    def find_relations(db: Session, article: Article):
        """查找文章关系"""
        # TODO: 实现关系查找逻辑
        pass

    @staticmethod
    def extract_key_points(content: str) -> LLMResponse:
        """提取关键点"""
        # TODO: 实现关键点提取逻辑
        pass

    @staticmethod
    def translate_text(content: str, target_language: str) -> LLMResponse:
        """翻译文本"""
        # TODO: 实现文本翻译逻辑
        pass


if __name__ == '__main__':
    # 测试用例
    test_response = '''{"candidates": [{"content": {"parts": [{"text": "**Title:** Title: 北航、字节和浙大最新发布Prompt Optimization优化框架ERM，让你的提示词优化更高效准确\\n\\n**Summarize:** This article introduces ERM (Example-Guided Reflection Memory mechanism), a new prompt optimization framework developed by researchers from Beihang University, ByteDance, and Zhejiang University.  ERM addresses shortcomings of existing methods by incorporating a feedback memory system and an example factory.  The framework uses a meta-prompt to guide the process, generating detailed solutions and targeted feedback.  Experiments across multiple datasets show significant performance improvements and efficiency gains compared to existing prompt optimization techniques. The article also discusses practical implications for prompt engineers, including better feedback management, optimized example selection, and improved optimization workflows.  Finally, it explores potential applications in AI products and the future scalability of ERM as a continuous learning system.\\n\\n**Key-Words:** **1. Primary Keywords** Prompt Optimization, ERM,  AI模型, 提示词优化, 大语言模型, 反馈记忆, 示例工厂,  强化学习,  启发式搜索\\n\\n**2. Secondary Keywords** 北航, 字节跳动, 浙江大学,  Doubao-pro, GPT4o,  meta-prompt,  Transformer,  LIAR数据集, BBH数据集, WebNLG数据集,  Prompt工程师\\n"}], "role": "model"}, "finishReason": "STOP", "avgLogprobs": -0.15637054162866929}], "usageMetadata": {"promptTokenCount": 5413, "candidatesTokenCount": 272, "totalTokenCount": 5685}, "modelVersion": "gemini-1.5-flash-latest"}'''
    # 先转换为JSON对象
    import json

    response = json.loads(test_response)
    # 测试提取方法
    result = LLMTasks.summarize_and_key_points(response['candidates'][0]['content']['parts'][0]['text'])
    print("提取结果：")
    print(f"标题: {result.body.get('title')}")
    print(f"摘要: {result.body.get('summary')}")
    print(f"关键词: {result.body.get('key_points')}")
