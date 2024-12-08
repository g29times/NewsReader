
import os
import logging

GEMINI_API_KEY= os.getenv("GEMINI_API_KEY", None)

# 设置包级别常量
GENIMI = "gemini-1.5-flash-latest" # DOC tests\GEMINI-DOC.md

# 设置日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 添加可在整个包中方便重用的自定义装饰器
def foo(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.info(f"Calling function: {func.__name__}")
        result = func(*args, **kwargs)
        logging.info(f"Function {func.__name__} completed")
        return result
    return wrapper