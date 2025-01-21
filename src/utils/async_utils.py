import asyncio
import threading
from loguru import logger

def run_async_task(coroutine, error_msg: str = "异步任务执行失败"):
    """通用的异步任务处理函数
    Args:
        coroutine: 要执行的协程对象
        error_msg: 错误信息前缀
    """
    async def _run_save():
        try:
            await coroutine
        except Exception as e:
            logger.error(f"{error_msg}: {str(e)}")
    
    def _run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_run_save())
        finally:
            loop.close()
    
    # 启动后台线程运行异步任务
    thread = threading.Thread(target=_run_in_thread)
    thread.daemon = True  # 设置为守护线程，这样主程序退出时线程会自动结束
    thread.start()
