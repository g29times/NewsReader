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
  见SYSTEM-DESIGN
## BUG
	多余的方法
	数据库重构
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

## 优化
- 异步处理
- 异常库
- 代码改进
   1 sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))确认写法
   https://mp.weixin.qq.com/s/hHxmCeIwbDyxdKiMlR8auw
   2 多级init
   https://mp.weixin.qq.com/s/vGjgrod3A0cAjGUrLv52Sg

# 2 Daily Progress

## 2025.1.7
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
   - 使用`llama-index-vector-stores-milvus==0.5.0`作为Milvus集成
   - 通过环境变量和配置文件管理数据库连接信息
   - 保持了与原有代码的兼容性

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


# 3 DONE
## Integrate LLM/VLM
### Implementation Steps
1. Select Libraries and Tools: Choose libraries for LLM/VLM integration, such as Hugging Face Transformers, OpenAI API, or PyTorch for local model hosting.
- Decide on the specific LLMs/VLMs and APIs you want to use. - GEMINI
- Develop a prototype to test the integration of LLM/VLM capabilities.
- Create API Client Module: Implement a Python module to interact with the Gemini API.
- Secure API Key: Store the API key securely and update your application to retrieve it from a secure location.
- Develop Use Cases: Define specific use cases for Gemini, such as summarizing articles or generating new ideas.
- Test Integration: Develop test cases to ensure the integration works as expected.
2. Develop Input Handlers: Create modules to handle different input types (text, vision, audio) and preprocess them for LLM/VLM processing.
    - Develop Functions: Implement these tasks as functions or services.
    - Integrate with Database: Ensure that the results are stored and updated in the database.
    - Schedule Tasks: Use a scheduler to handle periodic idea generation.
3. Integrate Frameworks: Use frameworks like LangChain to build workflows that incorporate LLMs for complex tasks.
4. Implement RAG Techniques: Develop methods to retrieve relevant data from your database to augment LLM outputs.
5. *(TODO) Design Agents: Create agents that can autonomously perform tasks and interact with the system.
6. Frontend: HTML -> JS/CSS -> NextJs
7. windsurf工具 支持文件、联网
