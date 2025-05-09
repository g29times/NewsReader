# Main progress
- [x] Implement the Database Schema: Update the existing database model to include these new tables and fields.
- [x] Integrate LLM/VLM: Plan how to use LLMs to analyze articles and generate ideas.
- [x] Develop Collection Mechanism: Implement the mechanism for collecting articles from various sources, including manual input and APIs.
- [x] Design User Interface: Create a user-friendly interface for managing and exploring articles and ideas.
- [] RAG
- [] Agent
## Prompts/Few-shots
[问答集](Prompts.txt)

# 1 TODO
## 整体设计
  1 见SYSTEM-DESIGN
  2 文章向量声明统一，目前分散于milvus_client.build_data，rag_service.add_articles_to_vector_store，chat_routes.chat
	3 修改文章标题的功能
	4 RAG流程重构：先全文给到LLM，然后再将之作为RAG的上下文，效果更好
## BUG
	对话删多了之后会乱序 建议改用gemini
	文章列表详情 已录入向量库 还能显示按钮
	多个文件上传后，内容会挤在一起形成一篇文章
	
## 前端
	throw new Error 和 toast 的整合
	支持各种信息源：WEB 文件 音频 图片 脑图 微信社交
	通用异常封装
	通用返回封装
## 后端
  user 多用户租户 登录 支付 权限 管理
	点赞
	生成笔记
	全局统一异常 返回体
## LLM端
紧急 高优先级：
	简单
		LLM模型切换 向量库切换 embedding切换
		LLM先 生成 如何学习一篇文章 的 提示词模板
	复杂
		需自行处理上下文携带，查询转写
		1 聊天记录memory持久化
			https://ywctech.net/ml-ai/langchain-vs-llamaindex-rag-chat/
		2 评估 eval
			https://zhuanlan.zhihu.com/p/681532023 RAG Triad
			https://docs.llamaindex.ai/en/stable/module_guides/evaluating/
低优先级：
	简单
		用户意图识别 提示3个问题
		重复问题识别
		垃圾箱 删除归档机制
		重排 rerank
			cohere https://mp.weixin.qq.com/s/XKTvd1jW4Y0AH9w-s2NLVA
			https://docs.llamaindex.ai/en/stable/examples/workflow/rag/
	复杂
		基于聊天记录 后训练 DPO PPO RL
		Agent 人格设定 主动对话
			Autogen https://github.com/Chainlit/cookbook/tree/main/pyautogen
			https://docs.llamaindex.ai/en/stable/examples/chat_engine/chat_engine_personality/
	- 双层模型调用（待改进）：
     - 当前流程：
       1. 用户上传多媒体文件并提问
       2. 使用Gemini处理多媒体文件，生成文本描述
       3. 将文本描述作为上下文，连同用户问题传给LlamaIndex聊天引擎
       4. LlamaIndex调用最终的对话模型（OpenAI/Gemini）回答问题
     - 原因：
       - LlamaIndex的SimpleChatEngine目前不支持多媒体输入
       - 为了复用现有的对话历史和文档检索功能，暂时采用这种方案
     - 改进方向：
       - 等待LlamaIndex支持多模态输入
       - 或者直接使用支持多模态的模型（如Gemini）进行对话，绕过LlamaIndex
       - 需要权衡：直接对话vs文档检索增强的对话

## 优化
- 异步处理
- 异常库
- 代码改进
   1 sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))确认写法
   https://mp.weixin.qq.com/s/hHxmCeIwbDyxdKiMlR8auw
   2 多级init
   https://mp.weixin.qq.com/s/vGjgrod3A0cAjGUrLv52Sg

# 2 Daily Progress

## 1.24 
### 改进文件上传和预览功能
1. 优化了文件上传和预览的实现：
   - 实现了文字和图片的组合显示，支持用户同时发送文字和图片
   - 使用MIME类型替代文件扩展名，支持更全面的文件类型：
     - image/*: 所有图片格式
     - text/*: 所有文本文件
     - video/*: 所有视频文件
     - audio/*: 所有音频文件
     - application/*: 常用办公文档(PDF, Word, Excel等)
   - 支持多文件上传
2. 改进用户体验：
   - 上传后立即预览
   - 文字和图片在同一条消息中显示
   - 保持了与原有对话功能的兼容性
3. 后端文件处理流程：
   - 统一的文件处理入口`FileInputHandler.read_from_file`：
     - 支持多种文件类型（图片、文本）的批量处理
     - 自动处理临时文件的保存和清理
     - 使用MIME类型进行文件分类
   - 图片处理：
     - 使用Gemini的多模态能力解析图片内容
     - 生成图片描述文本，支持非视觉模型使用
   - 文本处理：
     - 支持多种文本格式（txt, md等）
     - 使用jina提取和处理URL信息
     - 异步保存为文章供后续使用
   - 多模态融合：
     - 预留了多模态混合embedding的接口
     - 将文字和图片内容组合发送给模型
   - 双层模型调用（待改进）

## 1.23 前端性能优化
1. 实现了通用缓存管理类 CacheManager：src\webapp\static\js\cache_manager.js
   - 支持多种数据类型（文本、二进制、JSON）
   - 实现 TTL 过期控制和 LRU 清理策略
   - 支持数据压缩（使用 pako）
   - 提供缓存统计功能
   - 默认缓存时间1小时，最大缓存100MB
   - 支持自定义缓存时间和类型
   - 实现缓存项删除功能，用于数据更新时失效缓存
   - 采用两级缓存机制：
     - 内存缓存：提供快速访问
     - localStorage持久化：提供数据持久性
2. 优化了对话加载性能：
   - 添加重复加载检查，避免相同对话重复请求
   - 实现对话内容的本地缓存（1小时）
   - 实现文章内容的本地缓存（30天）
   - 对话更新后自动使相关缓存失效
   - 添加缓存统计面板，方便监控缓存使用情况
   - 支持手动清空所有缓存

3. 优化了静态资源加载：src\webapp\__init__.py
   - app.py 需关闭debug=False
   - 实现细粒度的静态资源缓存控制
   - JS/CSS 文件缓存30天，使用 immutable 标记优先内存缓存
   - 图片/图标缓存1年，使用 must-revalidate 优先磁盘缓存
   - 其他文件缓存1天
   - 添加必要的缓存控制头（public, Vary: Accept-Encoding）
   - 支持 CDN 缓存和压缩
   - 修复了开发模式下静态文件缓存失效的问题

4. 将主要静态依赖迁移到本地：
   - Bootstrap 4.5.2
   - jQuery 3.5.1
   - Showdown 2.1.0
   - Pako 2.1.0
   - Font Awesome 5.15.4

## 1.22 统一配置管理
1. 统一了系统关键参数配置：.evn
   - Embedding相关：维度配置(EMBEDDING_DIM=1024, EMBEDDING_DIM_ZIP=128)
   - LLM相关：生成参数(MAX_TOKENS, TEMPERATURE, TOP_P, TOP_K)
   - RAG相关：检索参数(RECALL_TOP_K, CHUNK_SIZE, OVERLAP)
   - 上下文相关：窗口大小(MAX_CONTEXT_WINDOW)
   - 将所有配置项移至.env文件
   - 添加了配置项的说明文档
   - 实现了统一的配置加载机制
2. 模型配置的三层架构设计：
   - 配置层(.env)：最外层，通过环境变量统一管理所有模型列表
     - 使用逗号分隔的字符串配置多个模型，如：VOYAGE_EMBED_MODELS="model1,model2,model3"
     - 便于在不修改代码的情况下灵活调整可用模型
   - 解析层(__init__.py)：中间层，负责配置转换和默认值管理
     - 通过 _parse_env_list 函数将环境变量转换为Python列表
     - 为每类模型提供默认值，确保系统在环境变量未设置时也能正常运行
   - 使用层(各模型客户端)：最内层，负责具体模型的选择和使用
     - 各客户端根据自身需求从模型列表中选择合适的模型，默认使用第一个
     - 如：Gemini客户端区分普通对话、视觉任务使用不同模型
3. 新增 DeepSeek 模型支持：
   - 实现了 DeepseekClient 类，支持原生API和OpenAI格式的调用
   - 遵循统一的配置管理方式，使用模型列表配置
   - 提供了与其他模型一致的接口：query_with_history 和 query_openai_with_history
4. 聊天上下文增强
   - 实现了三层上下文增强机制：
     1. 文件内容处理：支持上传文件作为上下文，自动提取文件中的URL信息，并异步保存为文章
     2. 勾选文章：支持用户选择已有文章作为上下文，加入聊天信息
     3. 向量RAG：基于用户问题进行语义搜索，使用Milvus检索相关文章片段，通过Voyager进行重排序
   - 采用分层结构组织上下文，使用markdown格式区分不同来源的内容
   - 异步处理文件和URL保存，避免阻塞主流程
5. 优化了评估框架中的召回率计算逻辑
   - 将Jaccard相似度改为余弦相似度，以更好地捕捉文本语义相似性
   - 修复了召回率计算可能超过1的问题，现在对每个golden chunk只计算一次召回
   - 调整了相似度阈值从0.8降到0.6，使评估更合理
   - 重命名了ground_truths为reference_contexts，使命名更准确

## 1.21 优化Notion长文章支持
1. 重构了Notion SDK的长文章处理功能
   - 优化了文本分块逻辑，确保每块不超过2000字符限制
   - 实现了多页面自动分页功能，每页最多99个内容块
   - 添加了友好的页面导航，支持上一页/下一页链接

2. 改进了错误处理和边界情况
   - 修复了分页导航的索引越界问题
   - 优化了块数量的控制，为导航预留空间
   - 保持了原有的文章属性（来源、相关文章、对话等）

3. 集成到现有系统
   - 将新的长文章功能整合到note_routes中
   - 保持了与原有API的兼容性
   - 确保了大型文章的可靠存储和访问

## 1.20 聊天功能增强
1. 优化了聊天功能的上下文处理
   - 修复了文件上传功能，支持多文件上传
   - 改进了勾选文章的处理逻辑，支持多文章ID的传递和转换
   - 优化了问题URL的处理流程，避免重复问题
   
2. 改进了上下文格式
   - 使用markdown格式组织上下文内容
   - 分离了问题和参考内容的处理
   - 优化了各部分内容的标题和层级

3. 错误处理优化
   - 为每个处理环节添加独立的错误处理
   - 添加了详细的日志记录
   - 即使某个环节失败也不影响其他功能

## 1.15 ~ 19 记忆管理与错误处理优化

1. 记忆管理功能优化
   - 重构了记忆ID映射机制，使用类全局变量`page_id_dict`存储映射关系
   - 优化了`manage_memory`方法，支持根据简短ID查找完整page_id
   - 添加了详细的日志记录，便于调试和追踪

2. 错误处理改进
   - 优化了记忆管理相关的异常处理机制
   - 添加了更详细的日志输出，包括字典状态和ID查找过程
   - 改进了文件缓存的清理机制，避免并发问题

3. 代码结构优化
   - 保持了原有代码的主要逻辑，仅对必要部分进行优化
   - 遵循最小修改原则，确保系统稳定性
   - 添加了更多调试信息，便于问题定位

## 1.14 支持多模型选择 | 聊URL | 文件导入多文关联

## 1.12 13 集成 MINIMAX GEMINI出问题

## 1.11 记忆管理提示词

## 1.10 优化聊天搜索功能
- 使用Redis Lua脚本实现服务器端搜索，减少数据传输
- 解决中文Unicode编码的搜索问题
- 优化性能，减少网络调用次数
- 保持代码简洁性和可维护性

## 1.8 9 个性化

## 2025.1.7 Notion 笔记 个性化
### 1. 成功集成了Notion API作为笔记存储系统：
- 实现了note_routes.py中的create_note函数，完整支持Notion的API调用
- 支持笔记的基本属性：标题、内容、来源、类型等
- 支持关联属性：文章ID和对话ID的关联
### 2. 前端实现：
- 在聊天界面实现了"加入笔记"功能
- 自动收集当前对话内容作为笔记内容
- 支持关联当前选中的文章
- 添加了用户友好的反馈（成功/失败提示）
### 3. 架构改进：
- 采用了与现有模块（article、chat）一致的代码组织方式
- 通过Blueprint实现了模块化的路由管理
- 为后续功能扩展预留了接口（如笔记编辑功能）
### 4. 重要突破：
- 成功将本地存储迁移到云端Notion
- 利用了Notion强大的数据库功能，为后续功能扩展打下基础
- 实现了笔记与文章、对话的关联，为知识管理提供了更好的支持
### 总结
   这个集成为我们带来了很多好处：
   强大的数据组织能力：Notion的数据库功能可以让我们更灵活地管理笔记
   云端存储：不再需要维护本地数据库
   丰富的展示形式：可以利用Notion的界面来更好地展示和组织内容
   协作可能：未来如果需要，可以利用Notion的协作功能
### 接下来可以考虑的方向：
- 添加富文本编辑器支持
- 实现笔记编辑功能
- 添加更多的笔记模板
- 利用Notion的API实现更多高级功能

## 2025.1.6 大文件 开会

## 2025.1.5 提示词和对话功能优化
### 1. 调试提示词越狱

### 2. 对话功能优化
- 修复了对话的BUG
- 修复了改对话名显示undifined的BUG
- 文章列表，增加了文章数量显示（如"全选5篇"）

### 3. 系统维护
- 完成了Linux环境的部署和启动脚本
- 实现了数据同步

### 4. 遗留问题
- 线上运行一段时间后出现数据库无法写入，头一次出现
   解决方案：KIMI - 开启WAL模式 https://kimi.moonshot.cn/chat/cttar8r2ulb8o9av542g

## 2025.1.4 文件处理优化

### 1. 重构文件处理模块
- 统一了文件处理接口，使用 `FileInputHandler` 作为统一入口
- 将重复的 PDF 处理代码合并，删除了 `pdf_content_reader.py`
- 优化了临时文件的处理方式

### 2. 优化代码结构
- 修复了模块导入路径问题，统一使用项目根目录导入
- 改进了静态方法的调用方式，使用类名直接调用
- 统一了日志记录格式，限制了过长参数的输出

### 3. 文本处理改进
- 将 JINA 文本分割功能集成到 `TextInputHandler` 中
- 添加了同步/异步调用支持
- 优化了文本分块的日志输出

### 4. 代码质量改进
- 删除了重复的工具类，保持代码库整洁
- 统一了错误处理和日志记录方式
- 改进了代码的可维护性和可读性

### 5. 遗留问题
- 需要进一步优化文本分割的参数配置
- 考虑添加更多文件类型的支持（如 Office 文档）

## 2025.1.3 页面调整 移动端适配

### 1. 优化消息编辑功能
- **问题修复**：
  - 修复了编辑消息时 HTML 标签累积的问题
  - 修复了换行符处理导致的格式问题
  - 修复了编辑时回车键导致的多余换行问题

- **简化实现**：
  - 移除了复杂的 DOM 操作，改用直接的 `innerHTML` 更新
  - 统一了消息和标题的编辑处理逻辑
  - 移除了不必要的内容比较和格式转换

### 2. 优化标题编辑功能
- **问题修复**：
  - 修复了 `replaceWith` 导致的 DOM 异常
  - 修复了失焦和保存的竞争条件问题

- **改进**：
  - 添加了 `isSaving` 状态标记来处理保存过程
  - 使用 `innerHTML` 替代 `replaceWith` 来更新内容
  - 统一使用 `onkeydown` 处理回车事件

### 3. 代码质量改进
- 遵循奥卡姆剃刀原则，简化了代码实现
- 保持了代码的一致性，使用相同的模式处理编辑功能
- 改进了错误处理和状态管理

### 4. 遗留问题和待办事项
- 暂无遗留问题
- 所有编辑功能已经稳定工作

## 2025.1.2 对话功能完成（重大）

1. 优化了对话界面的布局:
   - 统一了所有面板的高度为`calc(100vh - 12px)`
   - 调整了右侧面板的宽度为300px，与左侧文章面板保持一致
   - 添加了面板展开/收起的过渡动画效果

2. 功能:
   - 数据库增加对话表chats
   - 聊天llamaindex的store从本地json方式改为redis云服务upstash
   - 对话完整功能（笔记区上方 增删改查）
   - 聊天管理（引用、复制）
   - 对话全部配置用户uid
   - 实现了文章和对话的搜索功能

3. 代码优化:
   - 优化了搜索相关的代码结构
   - 统一了错误处理和提示信息
   - 移除了重复的代码

4. UI/UX改进:
   - 适配手机端操作
   - 添加了笔记区域的搜索框
   - 优化了按钮的布局和样式
   - 改进了面板切换的交互体验

## 2025.1.1 增强聊天界面
1. 增强了聊天界面功能:
   - 为每条消息添加了操作按钮（转为笔记、复制、喜欢、不喜欢）
   - 实现了消息复制功能
   - 优化了消息显示样式，包括角色标识和Markdown渲染
2. 实现了聊天历史记录功能:
   - 添加了`/api/chat/history`后端API
   - 实现了前端历史记录加载
   - 预留了多用户支持（uid参数）
3. 优化了UI界面:
   - 调整了笔记区域的标题显示
   - 改进了消息内容的样式和布局

## 2024.12.31 异步处理优化

#### 问题描述
在向量数据库操作过程中，由于涉及大量IO操作，需要优化异步处理机制以提高性能。

#### 修改内容

1. **简化异步处理逻辑**
   - 将`RAGService.add_articles_to_vector_store_background`方法简化为使用单一后台线程执行异步任务
   - 移除了复杂的事件循环和回调处理机制
   - 添加了清晰的错误处理和日志记录

2. **路由层优化**
   - 将`article_routes.py`中的`add_article`和`update_article_route`改为同步函数
   - 保持API响应迅速，将耗时操作放在后台处理

3. **向量数据库客户端优化**
   - 将`MilvusClient`中的`encode_query`和`encode_documents`方法改为同步方法
   - 只保留真正需要异步的数据库操作（`upsert_data`和`upsert_docs`）

#### 影响范围
- `src/utils/rag/rag_service.py`
- `src/webapp/article/article_routes.py`
- `src/database/milvus_client.py`

## 2024.12.29 RAG评估系统优化（重大）

#### 问题描述
为了准确评估RAG系统的性能，需要建立一个标准化的评估流程，包括数据准备和评估指标计算。

#### 修改内容

1. **向量数据库切换**
   - 从ChromaDB切换到Milvus(Zilliz云服务），以获得更好的性能和可扩展性
   - 实现了基础版本和上下文增强版本的数据存储
   - 使用evaluation_set作为标准测试集

2. **评估数据准备**
   - 基础版本：直接使用golden_chunk作为文档内容
   - 上下文增强版本：使用answer作为上下文，golden_chunk作为主要内容
   - 统一了文档ID和元数据的处理方式

3. **相似度评估改进**
   - 使用文本语义相似度替代精确匹配
   - 实现了基于阈值的评分机制
   - 添加了详细的评估日志输出

#### 影响范围
- `src/utils/rag/evaluator.py`
- `src/database/milvus_client.py`

## 2024.12.27 向量数据库文章管理优化

#### 修改内容
1. **文章删除功能增强**
   - 实现了`delete_articles_from_vector_store`方法，支持从向量数据库中删除文章
   - 使用文章ID作为向量库中的文档ID，确保一致性
   - 添加了完整的错误处理和日志记录

2. **文章添加功能优化**
   - 修改了`add_articles_to_vector_store`方法，在添加文档时设置正确的文档ID
   - 保持文章ID和向量库文档ID的一致性，便于管理和维护
   - 优化了日志输出，提供更详细的操作信息

#### 影响范围
- `src/utils/rag/rag_service.py`
- `src/webapp/article/article_routes.py`

## 2024.12.26 优化
1. 界面优化
   - 使用原生title属性实现摘要悬停提示，遵循简单原则
   - 简化添加文章表单，去除冗余字段
   - 统一使用flex布局，实现搜索栏和添加表单的对齐
   - 优化标签显示，支持长文本自动换行
2. 代码精简
   - 移除未使用的chat相关代码
   - 统一中文界面文案
   - 保持CSS样式简洁统一
   
## 2024.12.25 重构与优化
1. 重构了RAG服务，增加了对Milvus向量数据库的支持：
   - 实现了`VectorDB`抽象接口，统一了向量数据库的操作
   - 添加了`MilvusDB`实现，支持Milvus作为向量存储
   - 保留了原有的`ChromaDB`实现，实现了无缝切换
2. 优化了混合检索功能：
   - 实现了密集向量（语义）检索和稀疏向量（BM25）检索的结合
   - 添加了基于Voyage的重排序功能
   - 改进了评估器，支持新的向量数据库接口
3. 技术细节：
   - 使用LlamaIndex 0.9.8及以上版本
   - 使用ChromaDB作为向量存储
   - 集成VoyageAI的embedding服务
   - 使用Gemini-1.5-flash作为对话模型

## 2024.12.22 聊天模块重构与优化

#### 修改内容
1. **聊天界面重构**
   - 重构了聊天页面布局，添加了文章列表、聊天区域和笔记区域三栏布局
   - 优化了文章选择和展示功能
   - 添加了文章搜索功能
   - 实现了文章详情的展开/收起功能

2. **Gemini客户端优化**
   - 改进了错误处理机制，增加了超时重试
   - 优化了API响应的解析逻辑
   - 重构了代码结构，将内部方法和业务方法分离
   - 增加了详细的日志记录

3. **系统配置优化**
   - 将系统提示词移至环境变量配置
   - 统一了提示词管理方式
   - 优化了配置文件结构

#### 影响范围
- `src/webapp/templates/chat/chat.html`
- [src/utils/llms/gemini_client.py](cci:7://file:///m:/WorkSpace/AI/NewsReader/src/utils/llms/gemini_client.py:0:0-0:0)
- [src/utils/rag/rag_service.py](cci:7://file:///m:/WorkSpace/AI/NewsReader/src/utils/rag/rag_service.py:0:0-0:0)
- [.env](cci:7://file:///m:/WorkSpace/AI/NewsReader/.env:0:0-0:0)

## 2024.12.21 RAG系统集成（重大）

#### 修改内容

1. **实现RAG服务类**
   - 创建了`RAGService`类，集成LlamaIndex与现有文章系统
   - 使用VoyageEmbedding进行文档嵌入
   - 使用Gemini作为LLM模型
   - 实现了基于Chroma的向量存储

2. **多文档对话功能**
   - 实现了基于多篇文章的RAG对话功能
   - 添加了文档源引用功能
   - 支持临时collection的自动清理
   - 优化了文档内容的格式化和元数据处理

3. **前端交互优化**
   - 更新了聊天界面支持多文档选择
   - 实现了实时对话响应
   - 添加了错误处理和加载状态显示

4. **API路由更新**
   - 添加了`/api/chat/with_articles`路由处理多文档RAG对话
   - 优化了现有的chat相关API接口
   - 改进了错误处理和响应格式

#### 技术细节
- 使用LlamaIndex 0.9.8及以上版本
- 使用ChromaDB作为向量存储
- 集成VoyageAI的embedding服务
- 使用Gemini-1.5-flash作为对话模型

## 2024.12.18 文章导航优化
1. **优化文章导航功能**
   - 添加了文章列表与详情的平滑切换效果
   - 实现了左侧面板的自动收缩/展开功能
   - 使用CSS Grid和transition实现了流畅的布局切换
   - 优化了文章列表和详情页面的显示逻辑
   - 改进了Source Guide的展示效果

主要技术细节：
- 使用 `grid-template-columns` 控制面板宽度
- 添加 `transition: all 0.3s ease` 实现平滑过渡
- 采用CSS类控制替代了直接的style操作
- 统一了文章列表和详情页的状态管理

## 2024.12.17 聊天界面重新设计

#### 修改内容
1. **创建新的聊天界面**
   - 实现了三栏布局（资源列表、聊天区域、笔记区域）
   - 设计了现代化的UI，包括消息气泡、引用源显示
   - 添加了快捷操作按钮（分析主题、生成摘要、提取关键点）

2. **交互功能优化**
   - 实现了消息发送和显示功能
   - 添加了语音输入接口（预留）
   - 支持侧边栏折叠/展开

3. **技术实现**
   - 使用HTML5 + CSS + JavaScript实现
   - 采用Bootstrap框架确保响应式设计
   - 保持了与现有系统的兼容性
   
## 2024.12.16 项目初始化，文章管理（重大）

#### 修改内容
1. **统一导入路径处理**
   - 实现了基于项目根目录的绝对导入
   - 移除了相对导入，改用 `src.` 前缀的绝对导入
   - 为每个模块添加了项目根目录到 Python 路径

2. **LLM任务模块重构**
   - 重命名 `GeminiResponse` 为 `LLMResponse`，为多LLM支持做准备
   - 改进了错误处理和日志记录机制
   - 添加了完整的类型提示和文档字符串

3. **测试改进**
   - 添加了单元测试用例
   - 实现了内存数据库测试
   - 增加了空内容处理测试

#### 影响范围
- `src/utils/llms/llm_tasks.py`
- `src/utils/llms/gemini_client.py`
- `tests/test_llm_tasks.py`

## 2024.12.10 基本功能优化
1. **国际化支持优化**
   - 实现了中英文切换功能
   - 为所有UI元素添加了语言切换支持，包括按钮文本、表格标题等
   - 优化了语言切换的实现方式，使用统一的 `changeLanguage` 函数处理

### 代码优化
1. **JavaScript代码结构优化**
   - 将 showdown.js 库的引入移出循环体，提高页面加载性能
   - 优化了按钮的事件处理逻辑，避免ID重复问题
   - 统一了语言切换相关的代码实现

### 遗留问题
1. 可能需要考虑添加更多语言的支持
2. 需要进一步测试语言切换功能在各种场景下的表现
