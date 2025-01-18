import os
import re
import logging
import sys
import time
import requests
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional, Tuple, Union
import google.generativeai as genai

# 添加项目根目录到 Python 路径 标准方式
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)
from src.utils.llms.llm_common_utils import LLMCommonUtils
from src.utils.llms.models import LLMResponse
from src.utils.file_input_handler import FileInputHandler

# Load environment variables and configure logging
load_dotenv()
logger = logging.getLogger(__name__)

# 实例工具类，应用中可能有多个实例
class GeminiClient:
    """
    Google Gemini API 客户端
    静态方法集合，用于与Google Gemini API交互
    提供文本、媒体和查询的处理功能
    """
    API_KEY = os.getenv("GEMINI_API_KEY")
    MODEL = os.getenv("GEMINI_MODEL")
    BEST_MODEL = os.getenv("GEMINI_BEST_MODEL")
    THINKING_MODEL = os.getenv("GEMINI_THINKING_MODEL")
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/"
    
    # 配置生成参数
    SYSTEM_INSTRUCTION = os.getenv("SYSTEM_PROMPT")
    GENERATION_CONFIG = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 64, # 官方的64会偶现报错
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
    def _initialize_model(cls, system_prompt) -> genai.GenerativeModel:
        if system_prompt:
            logger.info("GEMINI SYSTEM_PROMPT: " + system_prompt)
        system_prompt = system_prompt or LLMCommonUtils._get_time_prompt()
        return genai.GenerativeModel(
            model_name=cls.MODEL,
            generation_config=cls.GENERATION_CONFIG,
            system_instruction=system_prompt,
        )

    # 多轮对话 TODO 未完成 
    @classmethod
    def _start_chat_session(cls, model: genai.GenerativeModel, messages: List[dict]):
        """启动聊天会话"""
        return model.start_chat(
            history=messages
            # // for messages  user = message.get("user"), model = message.get("model")
            # history = [
            #         {"role": "user", "parts": [file, context]},
            #         {"role": "model", "parts": [response]}
            #     ]
        )

    # 获取响应
    @classmethod
    def _get_response(cls, chat_session, question: str) -> Optional[str]:
        response = chat_session.send_message(question)
        return response

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
    def _chat(cls, question: str, histories: List[dict] = [], system_prompt: str = "") -> Optional[dict]:
        try:
            if not question:
                logger.error("No question provided")
                return None
            logger.info("MODEL: " + cls.MODEL)
            # 方式1 request 返回详细的json，含模型信息
            # print("--------------------------------------------------------")
            # print("--------------------------- 方式一 -----------------------------")
            # cls._validate_api_key()
            # headers = {"Content-Type": "application/json"}
            # data = {"contents": [{"parts": [{"text": question}]}]}
            # print(data)
            # url = cls.BASE_URL + cls.MODEL + ":generateContent?key=" + cls.API_KEY
            # # url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=AIzaSyAaWkpfMwLNcznXuOb8G0m4xtx79gU1APQ"
            # # print(url)
            # print("CALL ------------ " + cls.BASE_URL)
            # response = requests.post(
            #     url,
            #     headers=headers,
            #     json=data,
            #     timeout=30
            # )
            # print(response.json())
            print("--------------------------------------------------------")
            print("--------------------------- 方式二 -----------------------------")
            # 方式2 SDK 直接 返回字符串
            # 1 初始化模型
            model = cls._initialize_model(system_prompt)
            # 2 启动时加载历史对话上下文
            # 解析历史对话和多文件，放入历史记录  # TODO
            # // for messages  user = message.get("user"), model = message.get("model")
            # history = [
            #         {"role": "user", "parts": [file, context]},
            #         {"role": "model", "parts": [response]}
            #     ]
            if (len(question) > 200):
                logger.info("Question: " + question[:100] + " ..." + question[-100:])
            else:
                logger.info("Question: " + question)
            if histories:
                logger.info("History: " + str(histories))
            chat_session = cls._start_chat_session(model, histories)
            # 3 真正开始本轮对话
            response = cls._get_response(chat_session, question)
            if response and response.text:
                response = response.text
                if (len(response) > 200):
                    logger.info("Response: " + response[:100] + " ..." + response[-100:])
                else:
                    logger.info("Response: " + response)
            else:
                return None
            return {
                'message': response,
                'status_code': 200
            }
        except Exception as e:
            print("_chat Exception ------------ ")
            error_message = str(e)
            status_code = 400
            logger.error(f"Failed to call Gemini API: {error_message}")
            return {
                'error': {
                    'message': error_message,
                    'status_code': status_code
                }
            }

    # 使用内容查询，本方法是对chat方法的重试封装 业务类应该调用本方法
    @classmethod
    def query_with_history(cls, question: str, histories: List[dict] = None, system_prompt: str = None) -> Optional[dict]:
        """查询内容
        Args:
            question: 问题
            histories: 历史记录
            system_prompt: 系统提示词
        Returns:
            dict: 响应数据
        """
        for attempt in range(10):
            try:
                query = question
                response = cls._chat(query, histories, system_prompt)
                if response and response.get('status_code') == 200:
                    logger.info("query_with_history SUCCESS ------------ ")
                    return response.get('message')
                else:
                    logger.warning("query_with_history ERROR ------------ ")
                    if attempt < 2:
                        logger.info(f"Retrying after 5 seconds (attempt {attempt + 1})")
                        time.sleep(5)  # 等待5秒后重试
                        continue
                    return None
            except Exception as e:
                logger.error("query_with_history Exception ------------ ")
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    logger.info(f"Retrying after 5 seconds (attempt {attempt + 1})")
                    time.sleep(5)  # 等待5秒后重试
                    continue
                return None

    # 业务方法：总结文本 含提示词 PROMPT 重要方法
    @classmethod
    def summarize_text(cls, content: str, language: str = "Chinese") -> LLMResponse:
        prompt = os.getenv("SUMMARY_PROMPT")
        logger.info(f"Answer in {language}")
        try:
            # 成功返回例子 {'candidates': [{'content': {'parts': [{'text': '**Title:** Title: Scaling Test-Time Compute：向量模型上的思维链\n\n**Summarize:** 文章探讨了在向量模型推理阶段增加计算资源'}], 'role': 'model'}, 'finishReason': 'STOP', 'avgLogprobs': -0.21152597132737075}], 'usageMetadata': {'promptTokenCount': 6673, 'candidatesTokenCount': 246, 'totalTokenCount': 6919}, 'modelVersion': 'gemini-2.0-flash'}
            # response = cls.chat(f"{question} : ```{content}```")
            response = cls.query_with_history(f"{prompt}```{content}```")
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
            return LLMCommonUtils._extract_summary(response)
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
                return cls.query_with_history(content, question)
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
            # return cls.query_with_history(uploaded_files[0], question) # TODO 需要_start_chat_session支持多轮
            return cls.query_with_history(FileInputHandler.read_from_file(file_path), question)
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
    # messages=[
    #         {"role": "user", "parts": ["讲个笑话？"]},
    #         {"role": "model", "parts": ["有只猴子在树上"]},
    #     ]
    # GeminiClient.query_with_history("", "GEMI执行记忆管理", messages)

    # # OK
    print("TEST query_with_history -------------")
    GeminiClient.query_with_history("你好")

    # # OK
    # print("TEST query_with_url -------------")
    # response = GeminiClient.query_with_url("https://www.google.com", "这是什么网站？")
    # print(response)
    # 
    # # OK
    # print("TEST query_with_file -------------")
    # response = GeminiClient.query_with_file('src/utils/rag/docs/3B模型长思考后击败70B.txt', "这篇文章讲什么？")
    # print(response)
    # 
    # # OK
    # print("TEST summarize_text -------------")
    # response = GeminiClient.summarize_text(
    #     content=FileInputHandler.read_from_file('src/utils/rag/docs/Claude 的 5 层 Prompt 体系.txt'),
    #     language="Chinese", 
    # )
    # print(response)
