# 记忆
## 记忆理念
记忆是帮助LLM具有个性化的前提条件

## 记忆设计
### 个性化设计
见SYSTEM_PROMPT

### 存储设计
存储于Notion
结构：HOMEPAGE > 
        MEMORY DB > 
            SUBPAGE as a row in db
                title
                content

读取：
    先读取DB，再循环读取SUBPAGE
    在Flash应用启动时即加载一次记忆，后续不再每次对话都拉取
    定时拉取新记忆
写入：
    每次对话后，另起一个异步后台线程，进行记忆的更新