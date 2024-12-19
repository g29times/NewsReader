import os
import re
import logging
import sys
from typing import Optional, Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv
import requests
from .models import LLMResponse

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.text_input_handler import TextInputHandler
from utils.file_input_handler import FileInputHandler

# Load environment variables and configure logging
load_dotenv()
logger = logging.getLogger(__name__)

# 配置生成参数
GENERATION_CONFIG = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}
SYSTEM_INSTRUCTION = (
    "You are an expert scientific researcher who has years of experience in "
    "conducting systematic literature surveys and meta-analyses of different topics. "
    "You pride yourself on incredible accuracy and attention to detail. "
    "You always stick to the facts in the sources provided, and never make up new facts."
)


class GeminiClient:
    """
    Google Gemini API 客户端
    静态方法集合，用于与Google Gemini API交互
    提供文本、媒体和查询的处理功能
    """
    API_KEY = os.getenv("GEMINI_API_KEY")
    MODEL = "gemini-1.5-flash-latest"
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/" + MODEL + ":generateContent"
    

    @classmethod
    def _validate_api_key(cls):
        """验证API密钥是否设置"""
        if not cls.API_KEY:
            raise ValueError("GEMINI_API_KEY not set")

    @classmethod
    def chat(cls, input_text: str) -> Optional[dict]:
        """
        使用Gemini API生成内容
        
        Args:
            input_text: 输入文本
            
        Returns:
            API响应的JSON数据，如果失败则返回错误信息和状态码
        """
        cls._validate_api_key()

        headers = {"Content-Type": "application/json"}
        data = {"contents": [{"parts": [{"text": input_text}]}]}

        try:
            response = requests.post(
                f"{cls.BASE_URL}?key={cls.API_KEY}",
                headers=headers,
                json=data,
                timeout=10
            )
            logger.info(f"Gemini Response Status: {response.status_code}")
            logger.debug(f"Gemini Response Body: {response.text}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to call Gemini API: {e}")
            if hasattr(e, 'response'):
                status_code = e.response.status_code if hasattr(e.response, 'status_code') else response.status_code # 500
                try:
                    error_detail = e.response.json() if hasattr(e.response, 'json') else {}
                    error_message = error_detail.get('error', {}).get('message', str(e))
                except:
                    error_message = str(e)
            else:
                status_code = response.status_code # 500
                error_message = str(e)
                
            return {
                'error': {
                    'message': error_message,
                    'status_code': status_code
                }
            }

    @classmethod
    def extract_title_summary_key(cls, response: str) -> LLMResponse:
        """
        从Gemini响应中提取结构化信息
        
        Args:
            response: Gemini API的原始响应文本
            
        Returns:
            LLMResponse 包含解析后的标题、摘要和关键词
        """
        try:
            # 使用正则表达式提取信息
            title_match = re.search(r'\*\*Title:\*\*\s*(.*?)(?=\n\n|$)', response)
            summary_match = re.search(r'\*\*Summarize:\*\*\s*(.*?)(?=\n\n|$)', response)
            key_points_match = re.search(r'\*\*Key-Words:\*\*\s*(.*?)(?=\n\n|$)', response)

            body = {
                'title': title_match.group(1).strip() if title_match else '',
                'summary': summary_match.group(1).strip() if summary_match else '',
                'key_points': key_points_match.group(1).strip() if key_points_match else ''
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

    @classmethod
    def summarize_text(cls, text: str, prompt_template: str = None) -> LLMResponse:
        """
        使用Gemini总结文本内容
        
        Args:
            text: 要总结的文本内容
            prompt_template: 可选的提示词模板
            
        Returns:
            LLMResponse 包含处理结果
        """
        if prompt_template is None:
            prompt_template = (
                "You have 3 tasks for the following content: "
                "1. Fetch the title from the content, its format should have a title like 'Title: ...' "
                "in its first line, if not, you will return 'NO TITLE' for a fallback); "
                "2. Summarize the content concisely in Chinese; "
                "3. Extract Key-Words(only words, no explanation) in a format like "
                "'**1. Primary Domains** Web Applications, ...(no more than 5) "
                "**2. Specific Topics** React, ...(no more than 10)'. "
                "Your response must contain the title, summarize and key words in the fix format: "
                "'**Title:** ...\n\n**Summarize:** ...\n\n**Key-Words:** ...'"
            )
        
        try:
            response = cls.chat(f"{prompt_template} : ```{text}```")
            # 成功返回例子 {'candidates': [{'content': {'parts': [{'text': '**Title:** Title: Scaling Test-Time Compute：向量模型上的思维链\n\n**Summarize:** 文章探讨了在向量模型推理阶段增加计算资源'}], 'role': 'model'}, 'finishReason': 'STOP', 'avgLogprobs': -0.21152597132737075}], 'usageMetadata': {'promptTokenCount': 6673, 'candidatesTokenCount': 246, 'totalTokenCount': 6919}, 'modelVersion': 'gemini-1.5-flash-latest'}
            
            # 检查是否有错误响应
            if 'error' in response:
                return LLMResponse(
                    state="ERROR",
                    desc=response['error'].get('message', 'Unknown error'),
                    status_code=response['error'].get('status_code', 500),
                    body={}
                )
                
            # 提取文本内容
            text_content = response.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
            # 解析格式出错
            if not text_content:
                return LLMResponse(
                    state="ERROR",
                    desc="LLM返回内容为空",
                    status_code=500,
                    body={}
                )
            
            # 解析响应
            return cls.extract_title_summary_key(text_content)
            
        except Exception as e:
            error_msg = f"Gemini处理失败: {str(e)}"
            logger.error(error_msg)
            return LLMResponse(
                state="ERROR",
                desc=error_msg,
                status_code=500,
                body={}
            )

    @classmethod
    def upload_file(cls, path: str, mime_type: Optional[str] = None) -> Optional[Any]:
        """
        上传文件到Gemini
        
        Args:
            path: 文件路径
            mime_type: MIME类型（可选）
            
        Returns:
            Gemini文件对象
        """
        try:
            file = genai.upload_file(path, mime_type=mime_type)
            logger.info(f"Uploaded file '{file.display_name}' as: {file.uri}")
            return file
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            return None

    @classmethod
    def wait_for_files_active(cls, files) -> None:
        """
        等待文件处理完成
        
        Args:
            files: 要等待的文件列表
        """
        for file in files:
            name = file.name
            file_status = genai.get_file(name)
            while file_status.state.name != "ACTIVE":
                logger.info(f"File {name} is still processing...")
                file_status = genai.get_file(name)
        logger.info("All files are ready.")

    @classmethod
    def query_with_content(cls, content: str, question: str, retries: int = 2) -> Optional[str]:
        """
        使用内容查询Gemini
        
        Args:
            content: 要处理的文本内容
            question: 要问的问题
            retries: 重试次数
            
        Returns:
            Gemini的响应文本
        """
        if not content or content.strip() == "":
            logger.error("Empty content provided")
            return None

        processed_text = TextInputHandler.preprocess_text(content)
        prompt = f"{question}\n\nContent: {processed_text}"

        for attempt in range(retries + 1):
            try:
                response = cls.chat(prompt)
                if response:
                    return response.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text')
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt == retries:
                    return None
                continue

    @classmethod
    def query_with_url(cls, url: str, question: str, retries: int = 2) -> Optional[str]:
        """
        使用URL内容查询Gemini
        
        Args:
            url: 网页URL
            question: 要问的问题
            retries: 重试次数
            
        Returns:
            Gemini的响应文本
        """
        try:
            content = FileInputHandler.jina_read_from_url(url, use_jina_reader=True)
            if content:
                return cls.query_with_content(content, question, retries)
        except Exception as e:
            logger.error(f"Error reading from URL {url}: {e}")
            return None

    @classmethod
    def query_with_file(cls, file_path: str, question: str, mime_type: Optional[str] = None, retries: int = 2) -> \
            Optional[str]:
        """
        使用文件内容查询Gemini，支持多媒体文件（文本、图片、PDF等）
        
        Args:
            file_path: 文件路径
            question: 要问的问题
            mime_type: 文件的MIME类型（可选，如果不指定会自动推断）
            retries: 重试次数
            
        Returns:
            Gemini的响应文本
        """
        try:
            uploaded_files = cls._upload_and_validate_file(file_path, mime_type)
            if not uploaded_files:
                return None

            model = cls._initialize_model()
            chat_session = cls._start_chat_session(model, question, uploaded_files[0])
            response = cls._get_response(chat_session, question)
            return response
        except Exception as e:
            logger.error(f"Error processing file with Gemini: {e}")
            return None

    @classmethod
    def _upload_and_validate_file(cls, file_path: str, mime_type: Optional[str]):
        """上传并验证文件"""
        files = [cls.upload_file(file_path, mime_type=mime_type)]
        if not files[0]:
            logger.error("Failed to upload file to Gemini")
            return []
        # 等待文件处理完成
        cls.wait_for_files_active(files)
        return files

    @classmethod
    def _initialize_model(cls) -> genai.GenerativeModel:
        """初始化Generative Model"""
        return genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=cls.GENERATION_CONFIG,
            system_instruction=cls.SYSTEM_INSTRUCTION,
        )

    @classmethod
    def _start_chat_session(cls, model: genai.GenerativeModel, question: str, file: Any):
        """启动聊天会话"""
        return model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": [question, file]
                }
            ]
        )

    @classmethod
    def _get_response(cls, chat_session, question: str) -> Optional[str]:
        """获取响应"""
        response = chat_session.send_message(question)
        return response.text


if __name__ == "__main__":
    # 配置命令行参数
    import argparse

    parser = argparse.ArgumentParser(description="Query Gemini with various inputs")
    parser.add_argument("--question", required=True, help="Question to ask Gemini")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", help="URL to process")
    group.add_argument("--file", help="File path to process")
    args = parser.parse_args()

    # 处理查询
    if args.url:
        response = GeminiClient.query_with_url(args.url, args.question)
    else:
        response = GeminiClient.query_with_file(args.file, args.question)

    if response:
        print(f"\nGemini Response:\n{response}")
    else:
        print("Failed to get response from Gemini")

# 作为 Python 模块
# from src.llms.gemini_client import GeminiClient

# 处理 URL
# response = GeminiClient.query_with_url("https://example.com", "What is this website about?")

# 通过命令行
# python src/llms/gemini_client.py --question "What is this about?" --url "https://example.com"
# # 或者
# python src/llms/gemini_client.py --question "Summarize this file" --file "path/to/file.pdf"

# 处理 PDF 文件
# response = GeminiClient.query_with_file(
#     "path/to/document.pdf",
#     "Summarize this document",
#     mime_type="application/pdf"
# )

# 处理图片
# response = GeminiClient.query_with_file(
#     "path/to/image.jpg",
#     "Describe this image",
#     mime_type="image/jpeg"
# )

# 处理文本文件（自动推断 mime_type）
# response = GeminiClient.query_with_file(
#     "path/to/text.txt",
#     "What is the main topic of this text?"
# )
