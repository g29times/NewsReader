import os
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Union
import logging

# 创建一个日志记录器
logger = logging.getLogger(__name__)

class NotionMemoryService:
    """Notion based memory service for managing AI memories"""
    
    def __init__(self):
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
    
    # TODO
    def add_memory(self, event: str, layer: str = 'SHORT', user_id: str = '1') -> bool:
        """添加新的记忆
        
        Args:
            event: 记忆事件内容
            layer: 记忆层级 (PERMANENT|LONG|SHORT|COLD)
            user_id: 用户ID
            
        Returns:
            bool: 是否添加成功
        """
        url = f"https://api.notion.com/v1/pages"
        
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
                    "rich_text": [{"text": {"content": user_id}}]
                }
            }
        }
        
        response = requests.post(url, headers=self.headers, json=data)
        return response.status_code == 200

if __name__ == "__main__":
    # 测试代码
    memory_service = NotionMemoryService()
    memories = memory_service.get_memories()
    print("Formatted memories:")
    print(memories)
