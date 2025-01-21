import os
import logging
from logging.handlers import RotatingFileHandler
from functools import wraps

# https://blog.csdn.net/Runner1st/article/details/96481954

# 常量
TIME_ZONE_ADDNUM = int(os.getenv("TIME_ZONE_ADDNUM", 8))  # 时区偏移量

# 向量相关
VECTOR_DB_ARTICLES = "news_reader_articles"
VECTOR_DB_CHATS = "news_reader_chats"
VECTOR_DB_NOTES = "news_reader_notes"
VECTOR_DB_MEMORIES = "news_reader_memories"

# 解析env列表
def _parse_env_list(env_value: str, default_list: list) -> list:
    """从环境变量解析列表
    Args:
        env_value: 环境变量值，逗号分隔的字符串
        default_list: 默认值
    Returns:
        解析后的列表
    """
    if not env_value:
        return default_list
    return [item.strip() for item in env_value.split(",")]
# Voyage-ai # 1024, 512, 1024维
VOYAGE_MODELS = _parse_env_list(os.getenv("VOYAGE_EMBED_MODELS"),["voyage-multilingual-2", "voyage-3", "voyage-3-lite"])
VOYAGE_RERANK_MODELS = _parse_env_list(os.getenv("VOYAGE_RERANK_MODELS"),["rerank-1", "rerank-lite-1"])
# Jina
JINA_MODELS = _parse_env_list(os.getenv("JINA_EMBED_MODELS"),["jina-embeddings-v3"])
# Google
GEMINI_MODELS = _parse_env_list(os.getenv("GEMINI_MODELS"),["gemini-2.0-flash-exp", "gemini-exp-1206", "gemini-2.0-flash-thinking-exp"])
# OpenAI
OPENAI_MODELS = _parse_env_list(os.getenv("OPENAI_MODELS"), ["gpt-4o-mini", "o3", "o1", "gpt-4o"])
# Minimax
MINIMAX_MODELS = _parse_env_list(os.getenv("MINIMAX_MODELS"), ["abab6.5s-chat", "minimax-text-01", "abab6.5t", "abab6.5g"])
# Deepseek
DEEPSEEK_MODELS = _parse_env_list(os.getenv("DEEPSEEK_MODELS"),["deepseek-chat", "deepseek-reasoner"])

EMBEDDING_BATCH_SIZE = 128  # voyager.py 文档向量化时的批处理大小 固定128
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIM", 1024))  # 向量维度
EMBEDDING_DIMENSION_COMPRESSED = int(os.getenv("EMBEDDING_DIM_ZIP", 128))  # 压缩后的向量维度

# RAG服务相关
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))  # 文本分块大小
CHUNK_OVERLAP = int(os.getenv("OVERLAP", 100))  # 文本分块重叠大小
MAX_TOKENS_LONG = int(os.getenv("LLM_MAX_TOKENS_LONG", 16000))  # 长文本最大token数
MAX_TOKENS_NORMAL = int(os.getenv("LLM_MAX_TOKENS_NORMAL", 8000))  # 普通文本最大token数
MAX_TOKENS_SHORT = int(os.getenv("LLM_MAX_TOKENS_SHORT", 4000))  # 短文本最大token数
MAX_CONTEXT_WINDOW = int(os.getenv("MAX_CONTEXT_WINDOW", 1000000))  # 上下文窗口大小
RAG_RECALL_NUM_DEFAULT = int(os.getenv("RECALL_TOP_K", 20))  # chat_routes.py rag默认的召回文档数量

# 聊天相关
CHAT_STORE_FILE = "chat_store.json"  # 聊天记录存储文件
KEEP_URLS_DEFAULT = 2  # jina.py 从消息中提取URL时默认保留的数量
CHAT_KEEP_URLS_DEFAULT = 5  # chat_routes.py 聊天时默认保留的URL数量

# 配置项目级别的日志
# 使用 RotatingFileHandler 按照大小自动分割日志文件，每个文件最大8MB，保留5个备份
log_file = 'newsreader.log'
file_handler = RotatingFileHandler(log_file, maxBytes=8*1024*1024, backupCount=5, encoding='utf-8')
file_handler.setLevel(level=logging.DEBUG)  # 文件分级别 DEBUG 且显示行号
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)-8s - %(filename)s[line:%(lineno)d] - %(message)s'))
# 控制台
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO) # 控制台分级别 仅INFO
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)-8s - %(filename)s[line:%(lineno)d] - %(message)s'))
# 设置日志
logging.basicConfig(
    level=logging.DEBUG, # 总级别
    handlers=[
        stream_handler,  # 输出到控制台
        file_handler # 输出到文件
    ]
    # format='%(asctime)s - %(filename)s - %(levelname)s - %(message)s',
    # format='%(asctime)s - %(levelname)-8s - [%(filename)s] - %(message)s',
    # format='%(asctime)s - %(levelname)-8s - %(name)s - [%(filename)s] - %(message)s',
    # handlers=[
    #     logging.StreamHandler(),  # 输出到控制台
    #     logging.FileHandler('newsreader.log')  # 同时输出到文件
    # ]
)

# 添加可在整个包中方便重用的自定义装饰器
def logy(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        args_str = str(args)[:100] + ("..." if len(args) > 100 else "")
        kwargs_str = str(kwargs)[:100] + ("..." if len(kwargs) > 100 else "")
        logging.info(f"LOG ASPECT START - Function: {func.__name__} - Args: {args_str} - Kwargs: {kwargs_str}")
        result = func(*args, **kwargs)
        logging.info(f"LOG ASPECT  END  - Function: {func.__name__}")
        # if result is not None:
        #     logging.debug(f"LOG ASPECT Return - Function: {func.__name__} - Return: {result}")
        return result
    return wrapper