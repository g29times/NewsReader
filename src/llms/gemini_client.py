import os
import sys
import requests
import logging
from typing import Optional, Union, List, Any
from dotenv import load_dotenv
import google.generativeai as genai

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.text_input_handler import TextInputHandler
from utils.file_input_handler import FileInputHandler

# Load environment variables and configure logging
load_dotenv()
logger = logging.getLogger(__name__)

class GeminiClient:
    """
    静态方法集合，用于与Google Gemini API交互
    提供文本、媒体和查询的处理功能
    """
    API_KEY = os.getenv('GEMINI_API_KEY')
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"

    @classmethod
    def _validate_api_key(cls):
        """验证API密钥是否已设置"""
        if not cls.API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable not set")

    @classmethod
    def chat(cls, input_text: str) -> Optional[dict]:
        """
        使用Gemini API生成内容
        
        Args:
            input_text: 输入文本
            
        Returns:
            API响应的JSON数据，如果失败则返回None
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
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to call Gemini API: {e}")
            return None

    @staticmethod
    def upload_file(path: str, mime_type: Optional[str] = None) -> Optional[Any]:
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
    def wait_for_files_active(cls, files: List[Any]) -> None:
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
                    return response['candidates'][0]['content']['parts'][0]['text']
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
    def query_with_file(cls, file_path: str, question: str, mime_type: Optional[str] = None, retries: int = 2) -> Optional[str]:
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
            # 上传文件到Gemini
            files = [cls.upload_file(file_path, mime_type=mime_type)]
            if not files[0]:
                logger.error("Failed to upload file to Gemini")
                return None

            # 等待文件处理完成
            cls.wait_for_files_active(files)

            # 配置生成参数
            generation_config = {
                "temperature": 1,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 8192,
                "response_mime_type": "text/plain",
            }

            # 创建模型实例
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config=generation_config,
                system_instruction=(
                    "You are an expert scientific researcher who has years of experience in "
                    "conducting systematic literature surveys and meta-analyses of different topics. "
                    "You pride yourself on incredible accuracy and attention to detail. "
                    "You always stick to the facts in the sources provided, and never make up new facts."
                ),
            )

            # 启动聊天会话
            chat_session = model.start_chat(
                history=[
                    {
                        "role": "user",
                        "parts": [question, files[0]]
                    }
                ]
            )

            # 发送消息并获取响应
            response = chat_session.send_message(question)
            return response.text

        except Exception as e:
            logger.error(f"Error processing file with Gemini: {e}")
            return None

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