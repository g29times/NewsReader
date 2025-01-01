# 开发细节手册

# 后端部分
# Python
关注classmethod实例方法和静态（类）方法staticmethod(tool)
在try catch的catch部分，遇到local variable 'response' referenced before assignment
，需要再次try catch

# LLM部分
- 变量
    问题 question 
    内容 content=input_text=text
    上下文（可选） context

- 基本参数设置 top-k 等，导致召回不正常，见
https://blog.csdn.net/u012856866/article/details/140308083

- 调用超时或不够时间
    对于大段文本，如果本地超时时间太短requests.post(timeout=60)，LLM还没返回

- LLM返回的异常码：
    Google
        错误的Key 4xx 403 账号权限
        地区禁止  
        服务端繁忙 5xx

# 前端部分
## API调试
文章详情
http://localhost:5000/chat/api/articles/87