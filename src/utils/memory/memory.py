import os
import requests
import json
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Union
import logging
import threading
import sys
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# 添加项目根目录到 Python 路径 标准方式
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)
from src.utils.llms.gemini_client import GeminiClient

# 创建一个日志记录器
logger = logging.getLogger(__name__)

class NotionMemoryService:
    """Notion based memory service for managing AI memories"""
    
    _instance = None
    _memories_cache = None
    _last_cache_time = None
    _cache_duration = 300  # 缓存有效期5分钟

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NotionMemoryService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
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
        self._initialized = True
        
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

    def _should_refresh_cache(self) -> bool:
        """判断是否需要刷新缓存"""
        if self._memories_cache is None or self._last_cache_time is None:
            return True
        return (time.time() - self._last_cache_time) > self._cache_duration

    def get_memories_from_db(self, user_id: str = '1') -> List[Dict]:
        """获取数据库中的所有记忆条目"""
        url = f"https://api.notion.com/v1/databases/{self.memory_db_id}/query"
        response = self.session.post(url, json={})
        
        if response.status_code != 200:
            raise Exception(f"Failed to get memories: {response.text}")
            
        return response.json().get('results', [])
    
    # 
    def get_memory_content(self, page_id: str, user_id: str = '1') -> List[Dict]:
        """获取特定页面的具体内容"""
        # full page link example: https://www.notion.so/novagen/17630c2067b480c18d9fc2b132575f6a?pvs=4
        # page_id = "17630c2067b480c18d9fc2b132575f6a"
        url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
        response = self.session.get(url)
        
        if response.status_code != 200:
            raise Exception(f"Failed to get memory content: {response.text}")
            
        return response.json().get('results', [])
        
    def format_memory(self, memories: List[Dict], user_id: str = '1') -> str:
        """将记忆数据格式化为系统提示词可用的格式"""
        memory_list = []
        
        for memory in memories:
            # 获取记忆的基本属性
            properties = memory.get('properties', {})
            page_id = memory.get('id', '').replace('-', '')
            
            # 获取页面详细内容
            content_blocks = self.get_memory_content(page_id)
            content = ""
            for block in content_blocks:
                if block.get('type') == 'paragraph':
                    paragraph = block.get('paragraph', {}).get('rich_text', [])
                    for text in paragraph:
                        content += text.get('plain_text', '') + "\n"
            
            # 提取事件标题
            event_title = properties.get('event', {}).get('title', [{}])[0].get('text', {}).get('content', '')
            
            # 提取记忆层级
            layer = properties.get('layer', {}).get('select', {}).get('name', 'SHORT')
            
            # 提取最后编辑时间
            last_edited_time = memory.get('last_edited_time', '')
            if last_edited_time:
                last_edited_time = datetime.fromisoformat(last_edited_time.replace('Z', '+00:00'))
                last_edited_time = last_edited_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            
            # 组合完整的事件内容
            full_event = f"{event_title}\n{content}" if content else event_title
            
            # 创建记忆对象
            memory_obj = {
                'event': full_event,
                'user_id': user_id,
                'layer': layer,
                'last_edited_time': last_edited_time
            }
            
            memory_list.append(memory_obj)
            
        # 将所有记忆打包成一个数组
        return f'`<|memory_START|>{json.dumps(memory_list)}<|memory_END|>`'
        
    def get_memories(self) -> str:
        """获取所有记忆，优先使用缓存"""
        if not self._should_refresh_cache():
            logger.debug("Using cached memories")
            return self._memories_cache

        try:
            memories = self.get_memories_from_db()
            logger.info(f"Loaded memories: {len(memories)}")
            formatted_memories = self.format_memory(memories)
            # 更新缓存
            self._memories_cache = formatted_memories
            self._last_cache_time = time.time()
            logger.info(f"Memory length: {len(formatted_memories)}")
            return formatted_memories
        except Exception as e:
            logger.error(f"Failed to get memories: {str(e)}")
            # 如果获取失败但有缓存，返回缓存的数据
            if self._memories_cache is not None:
                logger.warning("Failed to refresh memories, using cached data")
                return self._memories_cache
            return ""
    
    def manage_memory(self, event: dict, page_id: str, layer: str = 'SHORT', user_id: str = '1', action: str = 'SAME') -> bool:
        """记忆管理
        Args:
            event: 记忆事件内容，格式为 {'title': str, 'body': str}
            page_id: 页面ID，如果为'0'表示新建，否则为已存在的页面ID
            layer: 记忆层级 (PERMANENT|LONG|SHORT|COLD)
            user_id: 用户ID
            action: 动作 UPSERT|DELETE|SAME(记忆不变)
        Returns:
            bool: 操作是否成功
        """
        if action == 'UPSERT':
            try:
                notion_page_id = None
                
                # 检查是否为新建或更新
                is_new = page_id == '0'
                
                if is_new:
                    # 1. 创建新页面
                    create_page_data = {
                        "parent": {"database_id": self.memory_db_id},
                        "properties": {
                            "event": {
                                "title": [{"text": {"content": event['title']}}]
                            },
                            "page_id": {
                                "rich_text": [{"text": {"content": str(page_id)}}]
                            },
                            "layer": {
                                "select": {"name": layer}
                            },
                            "user_id": {
                                "rich_text": [{"text": {"content": str(user_id)}}]
                            }
                        }
                    }
                    
                    # 创建页面
                    response = self.session.post(f"{self.base_url}/pages", json=create_page_data)
                    response.raise_for_status()
                    notion_page_id = response.json()['id']
                    
                    # 2. 添加页面内容（新建用POST）
                    if event.get('body'):
                        blocks_data = {
                            "children": [
                                {
                                    "object": "block",
                                    "type": "paragraph",
                                    "paragraph": {
                                        "rich_text": [
                                            {
                                                "type": "text",
                                                "text": {
                                                    "content": event['body']
                                                }
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                        
                        # 新建内容块
                        content_response = self.session.post(
                            f"{self.base_url}/blocks/{notion_page_id}/children",
                            json=blocks_data
                        )
                        content_response.raise_for_status()
                else:
                    # 1. 更新页面标题和属性
                    update_page_data = {
                        "properties": {
                            "event": {
                                "title": [{"text": {"content": event['title']}}]
                            },
                            "layer": {
                                "select": {"name": layer}
                            }
                        }
                    }
                    
                    # 更新页面
                    response = self.session.patch(f"{self.base_url}/pages/{page_id}", json=update_page_data)
                    response.raise_for_status()
                    
                    # 2. 更新页面内容（更新用PATCH）
                    if event.get('body'):
                        blocks_data = {
                            "children": [
                                {
                                    "object": "block",
                                    "type": "paragraph",
                                    "paragraph": {
                                        "rich_text": [
                                            {
                                                "type": "text",
                                                "text": {
                                                    "content": event['body']
                                                }
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                        
                        # 更新内容块
                        content_response = self.session.patch(
                            f"{self.base_url}/blocks/{page_id}/children",
                            json=blocks_data
                        )
                        content_response.raise_for_status()
                
                return True
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Rate limit
                    logger.warning("Rate limit hit, retrying after delay...")
                    time.sleep(2)  # 等待2秒后重试
                    return self.manage_memory(event, page_id, layer, user_id, action)
                else:
                    logger.error(f"Failed to add memory: {str(e)}")
                    return False
            except Exception as e:
                logger.error(f"Error managing memory: {str(e)}")
                return False
                
        elif action == 'DELETE':
            # TODO: 实现删除功能
            return False
        elif action == 'SAME':
            return True
        else:
            logger.error(f"Unknown action: {action}")
            return False
        
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
                memory_evaluation = GeminiClient.query_with_content("", memory_prompt, messages)
                # print(json.dumps(memory_evaluation))
                if not memory_evaluation or "error" in json.dumps(memory_evaluation):
                    logger.error(f"Raw memory evaluation: {memory_evaluation}")
                    return
                try:
                    # 提取并解析 JSON
                    json_str = self._extract_json_from_text(memory_evaluation)
                    memory_updates = json.loads(json_str)
                    if not isinstance(memory_updates, list):
                        memory_updates = [memory_updates]
                        
                    # 处理每条记忆更新
                    for update in memory_updates:
                        if all(k in update for k in ['event', 'user_id', 'page_id', 'layer', 'action']):
                            # 调用manage_memory写入Notion数据库
                            self.manage_memory(
                                event=update['event'],
                                page_id=update['page_id'],
                                layer=update['layer'],
                                user_id=update['user_id'],
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


# Update Memory Title
import requests
import json

url = "https://api.notion.com/v1/pages/17830c2067b481d7aea4c6cb8e27ed45"

payload = json.dumps({
  "properties": {
    "event": {
      "title": [
        {
          "text": {
            "content": "A New Memory1"
          }
        }
      ]
    }
  }
})
headers = {
  'Authorization': 'Bearer $NOTION_API_KEY',
  'Content-Type': 'application/json',
  'Notion-Version': '2022-06-28'
}

response = requests.request("PATCH", url, headers=headers, data=payload)

print(response.text)

# Update Memory 

import requests
import json

url = "https://api.notion.com/v1/blocks/17830c2067b481d7aea4c6cb8e27ed45/children"

payload = json.dumps({
  "children": [
    {
      "object": "block",
      "type": "heading_2",
      "heading_2": {
        "rich_text": [
          {
            "type": "text",
            "text": {
              "content": "Lacinato kale"
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
              "content": "Lacinato kale is a variety of kale with a long tradition in Italian cuisine, especially that of Tuscany. It is also known as Tuscan kale, Italian kale, dinosaur kale, kale, flat back kale, palm tree kale, or black Tuscan palm.",
              "link": {
                "url": "https://en.wikipedia.org/wiki/Lacinato_kale"
              }
            }
          }
        ]
      }
    }
  ]
})
headers = {
  'Authorization': 'Bearer $NOTION_API_KEY',
  'Content-Type': 'application/json',
  'Notion-Version': '2022-06-28'
}

response = requests.request("PATCH", url, headers=headers, data=payload)

print(response.text)



#
if __name__ == "__main__":
    memory_service = NotionMemoryService()

    # 插入 OK
    # memory_service.manage_memory(event="test event", layer="SHORT", user_id="1", action="UPSERT")

    # 异步更新 OK
    thread = memory_service.update_memory_async("你好", "你好，我是GEMI")
    thread.join()  # 等待线程完成
    
    # 查询 OK
    memories = memory_service.get_memories()