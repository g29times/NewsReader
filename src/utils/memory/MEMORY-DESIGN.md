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
记忆读取：
    先读取DB，再循环读取SUBPAGE
    在Flash应用启动时即加载一次记忆，后续不再每次对话都拉取
    定时拉取新记忆
记忆写入：
    流程
    1 正常对话返回response并返回前端
    2 启动异步线程，使用提示词 MEMORY_UPDATE_PROMPT 调用LLM更新记忆
    3 接收并解析LLM的返回，正常情况下，LLM应该返回格式化的json内容，如：{'event': '...', 'user_id': '...', 'layer': '...', 'action': '...'} event-事件, user_id-用户id, layer-记忆层(PERMANENT|LONG|SHORT|COLD), action-动作(UPSERT|DELETE|SAME(记忆不变))
    4 根据LLM返回的动作，调用manage_memory接口，进行记忆的更新

SYSTEM_PROMPT：
    系统启动时，加载一次记忆，以及系统启动时间，SYSTEM_PROMPT不会变化。
每次对话：
    每个对话session携带时间和记忆，每次对话后，另起一个异步后台线程，进行记忆的更新

代码问题：
    目前RAGservice和GEMINIclient各自实现了client逻辑。
    RAGservice是llamaindex的gemini封装，GEMINIclient是gemini的原生封装。
    这两个现在不兼容，而且系统中已经混用。

TODO
    UPSERT 用语义相似度对比