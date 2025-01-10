import os
import requests
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Union
import logging
import threading
import sys

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
    
    def __init__(self):
        """初始化Notion记忆服务"""
        self.api_key = os.getenv("NOTION_API_KEY")
        if not self.api_key:
            raise ValueError("NOTION_API_KEY not found in environment variables")
            
        self.headers = {
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        # Notion database ID for memories
        self.memory_db_id = "17630c2067b480619d63f2e7710058a9"  # 可以后续移到环境变量
        
    def get_memories_from_db(self, user_id: str = '1') -> List[Dict]:
        """获取数据库中的所有记忆条目"""
        url = f"https://api.notion.com/v1/databases/{self.memory_db_id}/query"
        response = requests.post(url, headers=self.headers, json={})
        
        if response.status_code != 200:
            raise Exception(f"Failed to get memories: {response.text}")
            
        return response.json().get('results', [])
    
    # 
    def get_memory_content(self, page_id: str, user_id: str = '1') -> List[Dict]:
        """获取特定页面的具体内容"""
        # full page link example: https://www.notion.so/novagen/17630c2067b480c18d9fc2b132575f6a?pvs=4
        # page_id = "17630c2067b480c18d9fc2b132575f6a"
        url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
        response = requests.get(url, headers=self.headers)
        
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
        """获取格式化后的所有记忆数据"""
        try:
            # TODO for all users
            memories = self.get_memories_from_db()
            logger.info(f"Loaded {len(memories)} memories")
            return self.format_memory(memories)
        except Exception as e:
            logger.error(f"Error getting memories: {e}")
            return ""  # 出错时返回空字符串，让系统可以继续运行
    
    def manage_memory(self, event: str, layer: str = 'SHORT', user_id: str = '1', action: str = 'SAME') -> bool:
        """记忆管理
        Args:
            event: 记忆事件内容
            layer: 记忆层级 (PERMANENT|LONG|SHORT|COLD)
            user_id: 用户ID
            action: 动作 UPSERT|DELETE|SAME(记忆不变)
        Returns:
            bool: 是否添加成功
        """
        url = f"https://api.notion.com/v1/pages"
        if action == 'UPSERT':
            data = {
                "parent": {"database_id": self.memory_db_id},
                "properties": {
                    "event": {
                        "title": [{"text": {"content": event}}]
                    },
                    "layer": {
                        "select": {"name": layer}
                    },
                    "user_id": {
                        "rich_text": [{"text": {"content": str(user_id)}}]
                    }
                }
            }
            response = requests.post(url, headers=self.headers, json=data)
            if response.status_code != 200:
                logger.error(f"Failed to add memory: {response.text}")
                return False
            else:
                logger.info("Memory added successfully")
                return True
        else: # DELETE|SAME 待实现
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
                memory_prompt = os.getenv("MEMORY_UPDATE_PROMPT", "GEMI评估更新记忆")
                # 构建对话历史
                messages = [
                    {"role": "user", "parts": [message]},
                    {"role": "model", "parts": [response]}
                ]
                # 调用LLM评估记忆
                memory_evaluation = GeminiClient.query_with_content("", memory_prompt, messages)
                logger.info(f"Raw memory evaluation: {memory_evaluation}")
                
                try:
                    # 提取并解析 JSON
                    json_str = self._extract_json_from_text(memory_evaluation)
                    memory_updates = json.loads(json_str)
                    if not isinstance(memory_updates, list):
                        memory_updates = [memory_updates]
                        
                    # 处理每条记忆更新
                    for update in memory_updates:
                        if all(k in update for k in ['event', 'user_id', 'layer', 'action']):
                            # 调用manage_memory写入Notion数据库
                            self.manage_memory(
                                event=update['event'],
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
    
if __name__ == "__main__":
    memory_service = NotionMemoryService()

    # 插入 OK 
    # memory_service.manage_memory(event="test event", layer="SHORT", user_id="1", action="UPSERT")

    # 异步更新
    thread = memory_service.update_memory_async("最新消息", "最新回应")
    thread.join()  # 等待线程完成
    
    # 查询 OK 
    memories = memory_service.get_memories()
    print("Formatted memories:")
    print(memories)