import os
import re
import logging
import sys
from typing import Optional, Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv
import requests

# 添加项目根目录到 Python 路径 标准方式
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)
from src.utils.llms.models import LLMResponse
from src.utils.text_input_handler import TextInputHandler
from src.utils.file_input_handler import FileInputHandler

# Load environment variables and configure logging
load_dotenv()
logger = logging.getLogger(__name__)

class GeminiClient:
    """
    Google Gemini API 客户端
    静态方法集合，用于与Google Gemini API交互
    提供文本、媒体和查询的处理功能
    """
    API_KEY = os.getenv("GEMINI_API_KEY")
    MODEL = os.getenv("GEMINI_MODEL")
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/" + MODEL + ":generateContent"
    
    # 配置生成参数
    SYSTEM_INSTRUCTION = os.getenv("SYSTEM_PROMPT")
    GENERATION_CONFIG = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 32, # 官方的64会偶现报错
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }

    # ----------------------------------- 内部方法 -----------------------------------
    # 验证API密钥是否设置
    @classmethod
    def _validate_api_key(cls):
        if not cls.API_KEY:
            raise ValueError("GEMINI_API_KEY not set")

    # 初始化Generative Model
    @classmethod
    def _initialize_model(cls) -> genai.GenerativeModel:
        return genai.GenerativeModel(
            model_name=cls.MODEL,
            generation_config=cls.GENERATION_CONFIG,
            system_instruction=cls.SYSTEM_INSTRUCTION,
        )

    # 多轮对话 TODO 未完成 
    @classmethod
    def _start_chat_session(cls, model: genai.GenerativeModel, context: str, file: Any):
        """启动聊天会话"""
        return model.start_chat(
            history=[
                # {
                    # "role": "user",
                    # "parts": [file, question]
                # }
            ]
        )

    # 获取响应
    @classmethod
    def _get_response(cls, chat_session, question: str) -> Optional[str]:
        response = chat_session.send_message(question)
        return response

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

    # 上传并验证文件
    @classmethod
    def _upload_and_validate_file(cls, file_path: str, mime_type: Optional[str]):
        files = [cls._upload_file(file_path, mime_type=mime_type)]
        if not files[0]:
            logger.error("Failed to upload file to Gemini")
            return []
        # 等待文件处理完成
        cls._wait_for_files_active(files)
        return files

    # 上传文件到Gemini
    @classmethod
    def _upload_file(cls, path: str, mime_type: Optional[str] = None) -> Optional[Any]:
        try:
            file = genai.upload_file(path, mime_type=mime_type)
            logger.info(f"Uploaded file '{file.display_name}' as: {file.uri}")
            return file
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            return None

    # 等待文件处理完成
    @classmethod
    def _wait_for_files_active(cls, files) -> None:
        logger.info("Waiting for file processing...")
        for name in (file.name for file in files):
            file = genai.get_file(name)
            while file.state.name == "PROCESSING":
                logger.info(".", end="", flush=True)
                time.sleep(10)
                file = genai.get_file(name)
            if file.state.name != "ACTIVE":
                raise Exception(f"File {file.name} failed to process")
        logger.info("All files are ready.")

    # ----------------------------------- 对外方法 -----------------------------------
    # 使用Gemini API生成内容 核心
    @classmethod
    def _chat(cls, question: str, context: str = None) -> Optional[dict]:
        try:
            cls._validate_api_key()
            headers = {"Content-Type": "application/json"}
            data = {"contents": [{"parts": [{"text": question}]}]}
            url = f"{cls.BASE_URL}?key={cls.API_KEY}"
            # print(url)
            # 方式1 request 返回详细的json，含模型信息
            # response = requests.post(
            #     url,
            #     headers=headers,
            #     json=data,
            #     timeout=30
            # )
            # 方式2 SDK 直接 返回字符串
            # 1 初始化模型
            model = cls._initialize_model()
            # 2 启动时加载历史对话上下文
            chat_session = cls._start_chat_session(model, context, None) # TODO File
            # 3 真正开始本轮对话
            response = cls._get_response(chat_session, question)
            if response and response.text:
                response = response.text

            logger.info(f"Gemini Response: {response}")
            # response.raise_for_status()
            # return response.json()
            return response
        except Exception as e:
            error_message = str(e)
            status_code = 400
            logger.error(f"Failed to call Gemini API: {error_message}, Status Code: {status_code}")
            return {
                'error': {
                    'message': error_message,
                    'status_code': status_code
                }
            }

    # 使用内容查询，本方法是对chat方法的多次重试封装 其他方法用该调用本方法
    @classmethod
    def query_with_content(cls, content: str, question: str, retries: int = 2) -> Optional[str]:
        if not content:
            logger.error("Empty content provided")
            return None

        # processed_text = TextInputHandler.preprocess_text(content)
        # prompt = f"{question}\n\nContent: {processed_text}"
        # prompt = f"{question} {content}"
        # prompt = question
        for attempt in range(retries + 1):
            try:
                response = cls._chat(f"{question} : ```{content}```")
                if response:
                    return response
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt == retries:
                    return None
                continue

    # 业务方法：使用Gemini总结文本 含提示词 PROMPT 重要
    @classmethod
    def summarize_text(cls, content: str, question: str = None, language: str = "Chinese") -> LLMResponse:
        if question is None:
            prompt = (
                "Process the following content, Main tasks: "
                "1. Get the title, if no title, return '[TITLE]NO TITLE[/TITLE]'"
                f", 2. Summarize the content concisely in {language} and use markdown to highlight important parts" 
                ", 3. Extract 5 Key-Topics(only words, no explanation)."
                "Your response must contain the title, summarize and key topics in the fix format: "
                "'[TITLE]...[/TITLE]\n[SUMMARY]...[/SUMMARY]\n[KEY_TOPICS]...[/KEY_TOPICS]\n'"
                ", Sub tasks(optional): "
                "4. Get the authors, publication date, and up to 3 sources(website, github or paper etc.) "
                "use the same format as above like: "
                "'[AUTHORS]...[/AUTHORS]\n[PUBLICATION_DATE]...[/PUBLICATION_DATE]\n[SOURCES]...[/SOURCES]\n'"
            )
        question = prompt
        logger.info(f"Answer in {language}")
        
        try:
            # 成功返回例子 {'candidates': [{'content': {'parts': [{'text': '**Title:** Title: Scaling Test-Time Compute：向量模型上的思维链\n\n**Summarize:** 文章探讨了在向量模型推理阶段增加计算资源'}], 'role': 'model'}, 'finishReason': 'STOP', 'avgLogprobs': -0.21152597132737075}], 'usageMetadata': {'promptTokenCount': 6673, 'candidatesTokenCount': 246, 'totalTokenCount': 6919}, 'modelVersion': 'gemini-2.0-flash-exp'}
            # response = cls.chat(f"{question} : ```{content}```")
            response = cls.query_with_content(content, question)
            # 检查是否有错误响应
            if not response or 'error' in response:
                return LLMResponse(
                    state="ERROR",
                    desc=response['error'].get('message', 'Unknown error'),
                    status_code=400,
                    body={}
                )

            # 方式一 提取文本内容
            # text_content = response.get('candidates', [{}])[0].get('content', {})
            # text_content = text_content.get('parts', [{}])[0].get('text', '')
            # # 解析格式出错
            # if not text_content:
            #     return LLMResponse(
            #         state="ERROR",
            #         desc="LLM返回内容为空",
            #         status_code=400,
            #         body={}
            #     )
            # 解析响应
            # return cls._extract_summary(text_content)

            # 方式二 直接返回字符串
            return cls._extract_summary(response)
        except Exception as e:
            error_msg = f"Gemini处理失败: {str(e)}"
            logger.error(error_msg)
            return LLMResponse(
                state="ERROR",
                desc=error_msg,
                status_code=500,
                body={}
            )

    # 询问Gemini关于URL
    @classmethod
    def query_with_url(cls, url: str, question: str) -> Optional[str]:
        try:
            content = FileInputHandler.jina_read_from_url(url)
            if content:
                return cls.query_with_content(content, question)
        except Exception as e:
            logger.error(f"Error reading from URL {url}: {e}")
            return None

    # 询问Gemini关于多媒体文件（文本、图片、PDF等） TODO
    @classmethod
    def query_with_file(cls, file_path: str, question: str, mime_type: Optional[str] = None):
        try:
            uploaded_files = cls._upload_and_validate_file(file_path, mime_type)
            if not uploaded_files:
                return None
            # return cls.query_with_content(uploaded_files[0], question) # TODO 需要_start_chat_session支持多轮
            return cls.query_with_content(FileInputHandler.read_from_file(file_path), question)
            # model = cls._initialize_model()
            # chat_session = cls._start_chat_session(model, question, uploaded_files[0])
            # response = cls._get_response(chat_session, question)
            # if response and response.text:
            #     response = response.text
            # return response
        except Exception as e:
            logger.error(f"Error processing file with Gemini: {e}")
            return None

if __name__ == "__main__":
    # OK
    print("TEST1 query_with_url -------------")
    response = GeminiClient.query_with_url("https://www.google.com", "这是什么网站？")
    print(response)
    # OK
    print("TEST2 query_with_file -------------")
    response = GeminiClient.query_with_file('src/utils/rag/docs/3B模型长思考后击败70B.txt', "这篇文章讲什么？")
    print(response)
    # OK
    print("TEST3 summarize_text -------------")
    response = GeminiClient.summarize_text(
        content=FileInputHandler.read_from_file('src/utils/rag/docs/Claude 的 5 层 Prompt 体系.txt'),
        language="Chinese", 
    )
    print(response)
