import os
import logging
from functools import wraps
from .article import Base, Article
from .relation import Base, Relation
from .tag import Base, Tag
from .idea import Base, Idea

# 设置日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 添加可在整个包中方便重用的自定义装饰器
def logy(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.info(f"Calling function: {func.__name__}")
        result = func(*args, **kwargs)
        logging.info(f"Function {func.__name__} completed")
        return result
    return wrapper