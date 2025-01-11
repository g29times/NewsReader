from datetime import datetime, timedelta
import json
import logging
import logging
from math import log
import os
import re
import sys
import threading
import time
from typing import Dict, List, Optional, Union

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)
from src.utils.llms.gemini_client import GeminiClient
from src.utils.llms.openai_client import OpenAIClient

# 添加项目根目录到 Python 路径 标准方式
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)


# 创建一个日志记录器
logger = logging.getLogger(__name__)

class NotionMemoryService:
    """Notion based memory service for managing AI memories"""
    
    # 单例相关
    _instance = None
    _lock = threading.Lock()
    # 缓存相关
    _memories_cache = None
    _last_cache_time = None
    _cache_duration = 300  # 缓存时间5分钟
    # 文件缓存路径
    _cache_file = "memory.txt"
    _last_cache_clear_time = datetime.now()
    _cache_clear_interval = timedelta(minutes=5)
    page_id_dict = {}  # 将page_id_dict定义为类的全局属性
    
    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init_service()
        return cls._instance
        
    def _init_service(self):
        """初始化服务"""
        self.api_key = os.getenv("NOTION_API_KEY")
        if not self.api_key:
            raise ValueError("NOTION_API_KEY not found in environment variables")
            
        self.memory_db_id = os.getenv("NOTION_MEMORY_DB_ID", "17630c2067b480619d63f2e7710058a9")
        self.notion_token = self.api_key
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        # 初始化带重试机制的会话
        self.session = self._init_session()
        # 启动缓存清理线程
        self._start_cache_cleaner()
        
    def _init_session(self) -> requests.Session:
        """初始化带重试机制的会话"""
        session = requests.Session()
        # 配置重试策略
        retries = Retry(
            total=3,  # 最大重试次数
            backoff_factor=1,  # 重试间隔
            status_forcelist=[429, 500, 502, 503, 504],  # 需要重试的状态码
            allowed_methods=["GET", "POST"]  # 允许重试的请求方法
        )
        # 配置连接池
        adapter = HTTPAdapter(
            max_retries=retries,
            pool_connections=10,  # 连接池大小
            pool_maxsize=10,  # 最大连接数
            pool_block=False  # 连接池满时不阻塞
        )
        session.mount('https://', adapter)
        session.headers.update(self.headers)
        return session

    @classmethod
    def _should_refresh_cache(cls) -> bool:
        """判断是否需要刷新缓存"""
        if cls._memories_cache is None or cls._last_cache_time is None:
            return True
        return (time.time() - cls._last_cache_time) > cls._cache_duration

    def _read_file_cache(self) -> Optional[str]:
        """从文件读取缓存
        Returns:
            Optional[str]: 缓存内容，如果文件不存在或为空返回None
        """
        try:
            if os.path.exists(self._cache_file) and os.path.getsize(self._cache_file) > 0:
                with open(self._cache_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    logger.info(f"Read from file cache, length: {len(content)}")
                    return content
            return None
        except Exception as e:
            logger.error(f"Error reading file cache: {str(e)}")
            return None

    def _write_file_cache(self, content: str) -> None:
        """写入文件缓存
        Args:
            content: 要缓存的内容
        """
        try:
            with open(self._cache_file, 'w', encoding='utf-8') as f:
                f.write(content)
                logger.info(f"Written to file cache, length: {len(content)}")
        except Exception as e:
            logger.error(f"Error writing file cache: {str(e)}")

    def get_memories_from_db(self) -> List[Dict]:
        """获取数据库中的所有记忆条目"""
        url = f"https://api.notion.com/v1/databases/{self.memory_db_id}/query"
        response = self.session.post(url, json={})
        
        if response.status_code != 200:
            raise Exception(f"Failed to get memories: {response.text}")
            
        return response.json().get('results', [])
    
    def get_memory_content(self, page_id: str) -> List[Dict]:
        """获取特定页面的具体内容"""
        url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
        response = self.session.get(url)
        
        if response.status_code != 200:
            raise Exception(f"Failed to get memory content: {response.text}")
            
        return response.json().get('results', [])
        
    def format_memory(self, memories: List[Dict]) -> str:
        """将记忆数据格式化为系统提示词可用的格式"""
        memory_list = []
        
        for memory in memories:
            # 获取记忆的基本属性
            properties = memory.get('properties', {})
            # 页面id
            page_id = memory.get('id', '')
            # 数据id
            id = properties.get('ID', {}).get('unique_id', {}).get('number', 0)
            # 获取用户id
            user_id = properties.get('user_id', {}).get('rich_text', [{}])[0].get('plain_text', '1')

            # 提取事件标题
            event_title = properties.get('event', {}).get('title', [{}])[0].get('text', {}).get('content', '')
            
            # 获取页面详细内容
            content_blocks = self.get_memory_content(page_id)
            content = ""
            for block in content_blocks:
                # TODO 其他类型
                if block.get('type') == 'heading_2':
                    heading = block.get('heading_2', {}).get('rich_text', [])
                    for text in heading:
                        content += text.get('plain_text', '') + "\n"
                if block.get('type') == 'paragraph':
                    paragraph = block.get('paragraph', {}).get('rich_text', [])
                    for text in paragraph:
                        content += text.get('plain_text', '') + "\n"
            
            # 提取记忆层级
            layer = properties.get('layer', {}).get('select', {}).get('name', 'SHORT')
            
            # 提取最后编辑时间
            last_edited_time = memory.get('last_edited_time', '')
            if last_edited_time:
                last_edited_time = datetime.fromisoformat(last_edited_time.replace('Z', '+00:00'))
                last_edited_time = last_edited_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            
            # 组合完整的事件内容
            full_event = f"{event_title}\n{content}" if content else event_title
            
            # 构建一个 id: page_id 字典，放在类变量中
            # page_id_dict.id = page_id 在for循环中逐个加入 id : page_id 对
            NotionMemoryService.page_id_dict[id] = page_id
            # 创建记忆对象
            memory_obj = {
                'event': full_event,
                'user_id': user_id,
                'page_id': page_id,
                'id': id,
                'layer': layer,
                'last_edited_time': last_edited_time
            }
            
            memory_list.append(memory_obj)
        
        print(NotionMemoryService.page_id_dict)  
        # 将所有记忆打包成一个数组
        return f'`<|memory_START|>{json.dumps(memory_list)}<|memory_END|>`'
        
    def get_memories(self) -> str:
        """获取所有记忆，优先使用缓存"""
        # 先检查内存缓存
        if not self._should_refresh_cache():
            logger.debug("Using memory cache")
            return self._memories_cache

        # 检查文件缓存
        file_cache = self._read_file_cache()
        if file_cache:
            logger.info("Using file cache")
            # 更新内存缓存
            NotionMemoryService._memories_cache = file_cache
            NotionMemoryService._last_cache_time = time.time()
            return file_cache

        try:
            memories = self.get_memories_from_db()
            logger.info(f"Loaded memories: {len(memories)}")
            formatted_memories = self.format_memory(memories)
            
            # 更新内存缓存
            NotionMemoryService._memories_cache = formatted_memories
            NotionMemoryService._last_cache_time = time.time()
            
            # 更新文件缓存
            self._write_file_cache(formatted_memories)
            
            logger.info(f"Memory length: {len(formatted_memories)}")
            return formatted_memories
        except Exception as e:
            logger.error(f"Error getting memories: {str(e)}")
            # 如果获取失败但有文件缓存，则使用文件缓存
            if file_cache:
                logger.info("Fallback to file cache after error")
                return file_cache
            return ""
    
    def manage_memory(self, event: dict, id: str, layer: str = 'SHORT', user_id: str = '1', action: str = 'SAME') -> bool:
        """管理记忆
        Args:
            event: 事件内容
            id: 页面ID
            layer: 记忆层级
            user_id: 用户ID
            action: 操作类型 UPSERT|DELETE|SAME
        Returns:
            bool: 是否成功
        """
        try:
            # 根据简短的id查找完整的page_id
            full_page_id = self._get_full_page_id(int(id))
            if action == 'UPSERT':
                try:
                    # 检查是否为新建或更新
                    is_new = full_page_id == '0'
                    if is_new:
                        # 1. 创建新页面
                        create_page_data = {
                            "parent": {
                                "database_id": self.memory_db_id
                            },
                            "properties": {
                                "event": {
                                    "title": [
                                        {
                                            "text": {
                                                "content": event.get('title', 'Untitled')
                                            }
                                        }
                                    ]
                                },
                                "user_id": {
                                    "rich_text": [
                                        {
                                            "text": {
                                                "content": user_id
                                            }
                                        }
                                    ]
                                },
                                "layer": {
                                    "select": {
                                        "name": layer
                                    }
                                }
                            }
                        }
                        
                        # 创建页面
                        response = self.session.post(f"{self.base_url}/pages", json=create_page_data)
                        response.raise_for_status()
                        notion_page_id = response.json().get('id')
                        logger.info(f"成功创建记忆 Created page: {notion_page_id}")
                        
                        # 2. 添加页面内容
                        if event.get('body'):
                            blocks_data = {
                                "children": [
                                    {
                                        "object": "block",
                                        "type": "heading_2",
                                        "heading_2": {
                                            "rich_text": [
                                                {
                                                    "type": "text",
                                                    "text": {
                                                        "content": "Memory Content"
                                                    }
                                                }
                                            ]
                                        }
                                    },
                                    {
                                        "object": "block",
                                        "type": "paragraph",
                                        "paragraph": {
                                            "rich_text": [
                                                {
                                                    "type": "text",
                                                    "text": {
                                                        "content": event.get('body')
                                                    }
                                                }
                                            ]
                                        }
                                    }
                                ]
                            }
                            
                            # 新建内容块 https://developers.notion.com/reference/patch-block-children
                            content_response = self.session.patch(
                                f"{self.base_url}/blocks/{notion_page_id}/children",
                                json=blocks_data
                            )
                            content_response.raise_for_status()
                            logger.info(f"成功添加内容 Updated blocks for page: {notion_page_id}")
                    else:
                        # 1. 更新页面标题和属性
                        update_page_data = {
                            "properties": {
                                "event": {
                                    "title": [
                                        {
                                            "text": {
                                                "content": event.get('title', 'Untitled')
                                            }
                                        }
                                    ]
                                },
                                "layer": {
                                    "select": {
                                        "name": layer
                                    }
                                }
                            }
                        }
                        # 更新页面
                        response = self.session.patch(f"{self.base_url}/pages/{full_page_id}", json=update_page_data)
                        response.raise_for_status()
                        logger.info(f"成功更新记忆 Updated page: {full_page_id}")
                        
                        # 2. 更新页面内容
                        if event.get('body'):
                            blocks_data = {
                                "children": [
                                    {
                                        "object": "block",
                                        "type": "heading_2",
                                        "heading_2": {
                                            "rich_text": [
                                                {
                                                    "type": "text",
                                                    "text": {
                                                        "content": "Memory Content"
                                                    }
                                                }
                                            ]
                                        }
                                    },
                                    {
                                        "object": "block",
                                        "type": "paragraph",
                                        "paragraph": {
                                            "rich_text": [
                                                {
                                                    "type": "text",
                                                    "text": {
                                                        "content": event.get('body')
                                                    }
                                                }
                                            ]
                                        }
                                    }
                                ]
                            }
                            
                            # 更新内容块
                            content_response = self.session.patch(
                                f"{self.base_url}/blocks/{full_page_id}/children",
                                json=blocks_data
                            )
                            content_response.raise_for_status()
                            logger.info(f"成功更新内容 Updated blocks for page: {full_page_id}")
                    return True
                except Exception as e:
                    logger.error(f"Error in UPSERT operation: {str(e)}")
                    return False
            elif action == 'DELETE':
                try:
                    # 将页面标记为已归档（软删除）
                    delete_data = {
                        "archived": True
                    }
                    response = self.session.patch(f"{self.base_url}/pages/{full_page_id}", json=delete_data)
                    response.raise_for_status()
                    logger.info(f"成功删除记忆 Archived page: {full_page_id}")
                    return True
                except Exception as e:
                    logger.error(f"Error in DELETE operation: {str(e)}")
                    return False
            elif action == 'SAME':
                return True
            else:
                logger.error(f"Unknown action: {action}")
                return False
        except Exception as e:
            logger.error(f"Error in manage_memory: {str(e)}")
            return False
        
    def _get_full_page_id(self, short_id: int) -> str:
        """根据简短的id查找完整的page_id"""
        # 这里实现查找逻辑，可以是从内存、文件或数据库中获取
        print("-----------------------------------")
        print(NotionMemoryService.page_id_dict)
        # if NotionMemoryService.page_id_dict == {}:
        #     NotionMemoryService.page_id_dict = {54: '17830c20-67b4-8148-9f6b-dd359c2b6258', 44: '17830c20-67b4-80b5-95ba-f261859760e8', 42: '17830c20-67b4-8125-bc33-fa2e50a16745', 41: '17830c20-67b4-814c-bb7b-f710fd323ee8', 24: '17730c20-67b4-81eb-8c88-f9178f06d5f6', 23: '17730c20-67b4-819c-a6a8-fc6ba596ce05', 16: '17730c20-67b4-8118-b53e-ce7a5e2e8123', 14: '17730c20-67b4-8178-9273-eaabab2bfe00', 8: '17730c20-67b4-8178-9974-d81209e5b2b2', 3: '17630c20-67b4-80c1-8d9f-c2b132575f6a', 2: '17630c20-67b4-80c2-adde-e9c1a0f88ec4', 1: '17630c20-67b4-8081-ac85-f52c2aa3a4b5'}
        page_id = NotionMemoryService.page_id_dict.get(short_id, "")
        logger.info(f"根据简短的id查找完整的page_id，id: {short_id}, page_id: {page_id}")
        # log 根据简短的page_id查找完整的page_id，short_id: 42, page_id:
        return page_id
    
    def _extract_json_from_text(self, text: str) -> str:
        """从文本中提取 JSON 内容
        Args:
            text: 可能包含 Markdown 格式和注释的文本
        Returns:
            str: 提取出的 JSON 字符串
        """
        # 尝试匹配 ```json ... ``` 格式
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            return json_match.group(1)
            
        # 如果没有 Markdown 格式，尝试找到第一个 [ 和最后一个 ]
        start = text.find('[')
        end = text.rfind(']')
        if start != -1 and end != -1:
            return text[start:end+1]
            
        # 如果都没找到，返回原文本
        return text

    def update_memory_async(self, message: str, response: str) -> threading.Thread:
        """异步更新记忆
        Args:
            message: 用户消息
            response: AI回复
        Returns:
            threading.Thread: 异步线程对象，可用于等待完成
        """
        def update_memory():
            try:
                # 使用MEMORY_UPDATE_PROMPT提示词让LLM评估记忆
                memory_prompt = os.getenv("MEMORY_UPDATE_PROMPT", "GEMI执行记忆管理")
                # 构建对话历史
                messages = [
                    {"role": "user", "parts": [message]},
                    {"role": "model", "parts": [response]}
                ]
                # 调用LLM评估记忆
                memory_evaluation = self.call_llm(memory_prompt, messages)
                # print(json.dumps(memory_evaluation))
                if not memory_evaluation or "error" in json.dumps(memory_evaluation):
                    logger.error(f"Raw memory evaluation: {memory_evaluation}")
                    return
                
                try:
                    # 提取并解析 JSON
                    if isinstance(memory_evaluation, str):
                        memory_evaluation = self._extract_json_from_text(memory_evaluation)
                    memory_updates = json.loads(memory_evaluation)
                    if not isinstance(memory_updates, list):
                        memory_updates = [memory_updates]
                    # 处理每条记忆更新
                    for update in memory_updates:
                        if all(k in update for k in ['event', 'user_id', 'id', 'layer', 'action']):
                            # 调用manage_memory写入Notion数据库
                            self.manage_memory(
                                event=update['event'],
                                user_id=update['user_id'],
                                id=update['id'],
                                layer=update['layer'],
                                action=update['action']
                            )
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse memory evaluation: {memory_evaluation}\nError: {str(e)}")
                except Exception as e:
                    logger.error(f"Error processing memory updates: {str(e)}")
            except Exception as e:
                logger.error(f"Memory update thread error: {str(e)}")
        
        # 启动异步线程并返回线程对象
        thread = threading.Thread(target=update_memory, daemon=True)
        thread.start()
        return thread

    def call_llm(self, question: str, histories: List[dict] = []) -> Optional[dict]:
        """查询内容
        Args:
            question: 问题
            histories: 历史记录
            files: 文件（暂不支持）
        Returns:
            dict: 响应数据
        """
        try:
            # 尝试使用Gemini API
            response = GeminiClient.query_with_history(question, histories)
            if not response or "error" in json.dumps(response): # DEBUG
                # 如果Gemini失败，切换到OpenAI
                logger.warning("Gemini API failed, switching to OpenAI")
                response = OpenAIClient.query_with_history(question, histories)
            return response
        except Exception as e:
            logger.error(f"Error in call_llm: {str(e)}")
            return None

    def _start_cache_cleaner(self):
        """启动缓存清理线程"""
        def clean_cache():
            while True:
                time.sleep(60)  # 每分钟检查一次
                now = datetime.now()
                if now - self._last_cache_clear_time >= self._cache_clear_interval:
                    self._clear_cache()
                    self._last_cache_clear_time = now
        
        cleaner_thread = threading.Thread(target=clean_cache, daemon=True)
        cleaner_thread.start()
    
    def _clear_cache(self):
        """清理缓存"""
        try:
            # 清理内存缓存
            self._memories_cache = None
            self._last_cache_time = None
            # 清空文件缓存
            if os.path.exists(self._cache_file):
                with open(self._cache_file, 'w', encoding='utf-8') as f:
                    f.truncate(0)  # 清空文件内容
            logger.info("缓存已清理")
        except Exception as e:
            logger.error(f"清理缓存时出错: {str(e)}")


#
if __name__ == "__main__":
    memory_service = NotionMemoryService()

    # 插入 OK
    # memory_service.manage_memory(event="test event", layer="SHORT", user_id="1", action="UPSERT")

    # 查询 OK
    memories = memory_service.get_memories()

    # 异步更新 OK - 需要等待完成
    thread = memory_service.update_memory_async("阅读《The Wedding People》第二章更多内容", "好的")
    thread.join()  # 等待线程完成