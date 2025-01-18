# https://github.com/upstash/redis-py
# !pip install upstash-redis
# for async use
# from upstash_redis.asyncio import Redis
# async_redis = Redis.from_env()
import os, sys
import re
import json
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
    
    def get_string(self, key: str):
        try:
            value = self.redis.get(key)
            return value
        except Exception as e:
            logy.error(f"Error getting string: {str(e)}")
            return None

    def set_string(self, key: str, value: str):
        try:
            self.redis.set(key, value)
        except Exception as e:
            logy.error(f"Error setting string: {str(e)}")

    def get_hash(self, key: str):
        try:
            value = self.redis.hgetall(key)
            return value
        except Exception as e:
            logy.error(f"Error getting hash: {str(e)}")
            return None
    
    def get_hash_value(self, key: str, field: str):
        try:
            value = self.redis.hget(key, field)
            return value
        except Exception as e:
            logy.error(f"Error getting hash value: {str(e)}")
            return None
            
    def set_hash(self, key: str, data: dict):
        """
        def hset(
            self,
            key: str,
            field: Optional[str] = None,
            value: Optional[ValueT] = None,
            values: Optional[Mapping[str, ValueT]] = None,
        ) -> ResponseT:
        
        Sets the value of one or multiple fields in a hash.

        Returns the number of fields that were added.

        `hmset` can be used to set multiple fields at once too.

        Example:
        ```python

        # Set a single field
        assert redis.hset("myhash", "field1", "Hello") == 1

        # Set multiple fields
        assert redis.hset("myhash", values={
            "field1": "Hello",
            "field2": "World"
        }) == 2
        ```

        See https://redis.io/commands/hset
        """
        try:
            # self.redis.hset(key, data) # ERR wrong number of arguments for 'hset' command
            for field, value in data.items():
                self.redis.hset(key, field, value)
        except Exception as e:
            logy.error(f"Error setting hash: {str(e)}")

    def delete_hash_value(self, key: str, field: str):
        try:
            self.redis.hdel(key, field)
        except Exception as e:
            logy.error(f"Error deleting hash value: {str(e)}")

    async def batch_delete_hash_fields(self, key_pattern):
        """
        批量删除 Redis Hash 中符合指定模式的 key 的 field。

        Args:
            key_pattern: key 的模式，例如 "article_2_chunk_*"。
        """
        keys = []
        cursor = '0'
        while True:
            cursor, batch_keys = self.redis.scan(cursor=cursor, match=key_pattern)
            keys.extend(batch_keys)
            if cursor == '0':
                break
        print(f"匹配到的 keys: {keys}")

        for key in keys:
            key = key.decode("utf-8")
            fields = self.redis.hkeys(key)
            if fields:
                field_list = [field.decode("utf-8") for field in fields]
                print(f"key: {key}, 将删除 field: {field_list}")
                self.redis.hdel(key, *field_list) # 批量删除 field，注意*的使用
        print("批量删除完成")

    async def batch_delete_hash_fields_with_lua(self, key_pattern):
        """
        使用 Lua 脚本批量删除 Redis Hash 中符合指定模式的 key 的 field。

        Args:
            key_pattern: key 的模式，例如 "article_2_chunk_*"。
        """
        lua_script = """
        local keys = redis.call('KEYS', ARGV[1])
        if not keys then
           return {}
        end
        for _, key in ipairs(keys) do
            local fields = redis.call('HKEYS', key)
            if #fields > 0 then
                redis.call('HDEL', key, unpack(fields))
            end
        end
        return keys
        """
        keys = self.redis.eval(lua_script, 0, key_pattern) # 传入 key 的模式
        if isinstance(keys, list):
            print(f"匹配到的 keys: {keys}")
        else:
            print(f"没有匹配到keys: {keys}") # 新增提示
        print("批量删除完成 (使用 Lua 脚本)")

    def decode_unicode_escape(self, s: str) -> str:
        """解码Unicode转义序列"""
        try:
            return bytes(s, 'utf-8').decode('unicode_escape')
        except Exception as e:
            logy.error(f"Error decoding unicode escape: {str(e)}")
            return s

    # 使用Lua 在Redis服务器端搜索对话内容
    def search_conversation_content(self, user_id: int, query: str) -> List[str]:
        """
        在Redis服务器端搜索对话内容
        使用Lua脚本在服务器端执行搜索，只返回匹配的key
        """
        # 将搜索词转换为Unicode转义序列
        query_escaped = query.encode('unicode_escape').decode('ascii')
        if query_escaped.startswith('\\u'):
            query_escaped = query_escaped[2:]  # 移除开头的\u
        
        # Lua脚本：在服务器端执行搜索
        lua_script = '''
        local pattern = ARGV[1]
        local query = ARGV[2]
        local matched_keys = {}
        
        -- 获取所有匹配pattern的key
        local keys = redis.call('KEYS', pattern)
        
        -- 对每个key进行处理
        for i, key in ipairs(keys) do
            -- 获取list中的所有元素
            local messages = redis.call('LRANGE', key, 0, -1)
            -- 检查每条消息
            for j, msg in ipairs(messages) do
                -- 查找Unicode编码的query
                if string.find(msg, '\\\\u' .. query) then
                    table.insert(matched_keys, key)
                    break
                end
            end
        end
        
        return matched_keys
        '''
        
        try:
            # 执行Lua脚本
            pattern = f"user{user_id}_conv*"
            # upstash-redis的eval方法接受script, keys和args参数
            matched_keys = self.redis.eval(
                script=lua_script,
                keys=[pattern],  # pattern作为KEYS参数
                args=[pattern, query_escaped]  # 参数通过args传递
            )
            
            # 从返回的key中提取conv_id
            conv_ids = set()
            for key in matched_keys:
                match = re.search(r'conv([a-zA-Z0-9]+)$', str(key))
                if match:
                    conv_ids.add(match.group(1))
            
            return list(conv_ids)
        except Exception as e:
            logy.error(f"Error executing Redis Lua script: {str(e)}")
            return []

# 创建单例实例
redis_service = RedisService()

if __name__ == "__main__":
    # print(redis_service.decode_unicode_escape("\\u8c93")) # 成功 貓

    # print(redis_service.get_keys("user1_conv*")) # 成功

    # # helloworld 成功
    # script = 'return ARGV[1]'
    # result = redis_service.redis.eval(script, [], ["hello"])
    # print(result) # "hello"

    # # 用lua 获取所有keys 成功
    # script = '''
    # local pattern = ARGV[1]
    # local keys = redis.call('KEYS', pattern)
    # return keys
    # '''
    # result = redis_service.redis.eval(script, [], ["user1_conv*"])
    # print("All keys:", result)

    # # 用lua 获取一个list类型的key的所有元素 成功
    # script = '''
    # local key = ARGV[1]
    # local messages = redis.call('LRANGE', key, 0, -1)
    # return messages
    # '''
    # # 使用第一个key来测试
    # first_key = redis_service.get_keys("user1_conv1")[0]
    # result = redis_service.redis.eval(script, [], [first_key])
    # print("\nFirst key:", first_key)
    # print("List contents:", result)

    # # 用lua 搜索
    # print(redis_service.search_conversation_content(1, "トレンディドラマ")) # 成功
    
    # set string
    # redis_service.set_string("chunk:A", "这是第一段大段文本的内容...")
    # redis_service.set_string("chunk:B", "这是第二段大段文本的内容...")
    print(redis_service.get_string("chunk:A")) # b'world'

    # set hash
    # redis_service.set_hash("child_chunk_map", {"child_1": "A", "child_2": "B"}) # 成功
    print(redis_service.get_hash("child_chunk_map"))
