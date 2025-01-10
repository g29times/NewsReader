# https://github.com/upstash/redis-py
# !pip install upstash-redis
# for async use
# from upstash_redis.asyncio import Redis
# async_redis = Redis.from_env()
import os, sys
import re
from upstash_redis import Redis
from typing import List
# 添加项目根目录到 Python 路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from src import logy

class RedisService:
    def __init__(self):
        self.redis = Redis.from_env()

    def get_keys(self, pattern: str):
        try:
            keys = self.redis.keys(pattern)
            return keys
        except Exception as e:
            logy.error(f"Error getting keys: {str(e)}")
            return []

    def delete_keys(self, pattern: str):
        try:
            keys = self.redis.keys(pattern)
            for key in keys:
                self.redis.delete(key)
        except Exception as e:
            logy.error(f"Error deleting keys: {str(e)}")
    
    def decode_unicode_escape(self, s: str) -> str:
        """解码Unicode转义序列"""
        try:
            return bytes(s, 'utf-8').decode('unicode_escape')
        except Exception as e:
            logy.error(f"Error decoding unicode escape: {str(e)}")
            return s
    
    def search_conversation_content(self, user_id: int, query: str) -> List[str]:
        """
        在用户的所有对话内容中搜索，返回匹配的conversation_ids列表
        Args:
            user_id: 用户ID
            query: 搜索关键词
        Returns:
            List[str]: 匹配的conversation_ids列表
        """
        try:
            conv_ids = set()
            pattern = f"user{user_id}_conv*"
            keys = self.redis.keys(pattern)
            for key in keys:
                try:
                    # 获取List中的所有内容
                    messages = self.redis.lrange(key, 0, -1)
                    # 检查每条消息是否包含搜索词
                    for msg in messages:
                        # 解码Unicode转义序列
                        decoded_msg = self.decode_unicode_escape(str(msg))
                        if query.lower() in decoded_msg.lower():
                            # 从key中提取conv_id
                            match = re.search(r'conv([a-zA-Z0-9]+)$', key)
                            if match:
                                conv_ids.add(match.group(1))
                            break  # 找到一个匹配就可以跳出内层循环
                except Exception as e:
                    logy.error(f"Error searching in Redis key {key}: {str(e)}")
                    continue
            return list(conv_ids)
        except Exception as e:
            logy.error(f"Error searching in Redis: {str(e)}")
            return []


# 创建单例实例
redis_service = RedisService()

if __name__ == "__main__":
    print(redis_service.decode_unicode_escape("\\u8c93"))