import os
import logging
from functools import wraps

GEMINI_API_KEY= os.getenv("GEMINI_API_KEY", None)

# 设置包级别常量
GENIMI = "gemini-1.5-flash-latest" # DOC tests\GEMINI-DOC.md

# 配置项目级别的日志
# 文件
file_handler = logging.FileHandler('newsreader.log')
file_handler.setLevel(level=logging.DEBUG) # 文件分级别 DEBUG 且显示行号
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s'))
# 控制台
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO) # 控制台分级别 仅INFO
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)-8s - [%(filename)s] - %(message)s'))
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
        logging.info(f"LOG ASPECT START - Function: {func.__name__} - Args: {args}")
        result = func(*args, **kwargs)
        logging.info(f"LOG ASPECT  END  - Function: {func.__name__}")
        # if result is not None:
        #     logging.debug(f"LOG ASPECT Return - Function: {func.__name__} - Return: {result}")
        return result
    return wrapper