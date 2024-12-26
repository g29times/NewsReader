# Main progress
- [x] Implement the Database Schema: Update the existing database model to include these new tables and fields.
- [x] Integrate LLM/VLM: Plan how to use LLMs to analyze articles and generate ideas.
- [x] Develop Collection Mechanism: Implement the mechanism for collecting articles from various sources, including manual input and APIs.
- [x] Design User Interface: Create a user-friendly interface for managing and exploring articles and ideas.

# 1 DEGISN/TODO
- 产品驱动流程 File(Input) -> Summary -> Relation -> Note -> Idea -> Blog(Output)
- 核心原则：少即是多，简单原则，哪些东西是会被LLM大厂逐渐取代的？（已取代：CoT框架、提示词框架）
	flomo - 真正学会的含义
	复杂性案例：https://blog.csdn.net/juan9872/article/details/137658555
		1. 层出不穷的设计模式：CoT、ReACT等框架，最初是因为LLM不具备（LLM厂商精力不在此），但是随着LLM的发展，这些模式逐渐被集成在了LLM内部（o1，gemini-thinking），框架变得臃肿多余。
		2. Agent是否也会被取代？
		3. 跨聊天记忆和跨文档记忆，哪个优先？
- 需求辨别
		场景：遗忘资料源：我的笔记哪去了？
		写文章是真实需求吗？
			买相机 买无人机是真实需求吗？
			买课是真实需求吗？
		主观优先级是真实需求吗？
- 系统设计
	内容分类 筛选 聚合 归并 和笔记 课程 脑图打通
	系统设计参考discord
	第四格 - 生成笔记博客 灵感来源 - https://ywctech.net/ml-ai/langchain-vs-llamaindex-rag-chat/
	LLM先 生成如何学习一篇文章 的 提示词模板
	灵感：LLM自动维护知识词典 - 凝萃知识库 + 代码实训库
		亟需提示词模板存放处：
			1 帮我把这篇文章里面的专业术语（如token...）提取出来，如果文章内已经解释，则引用原文，如果没有，则加以简要的一句话解释，以 “· 概念A：A是指...” 的形式输出
			2 （如果词典里已有）我们可以回顾下...，与新概念的联系 - *生图
	思想实验：
		灵感：New Yorker - 一图胜千言
		1 吐槽小助手
		2 多LLM 分布式共识
		3 更了解用户 自身也更个性化
			人类心理学 + 数据飞轮（新学） + SLM训练（灵感） + 论文（TODO）
			了解用户笔记、划线习惯（具体小点研究）
		用户反馈机制
		用户激励机制 视觉 日历？点图？路径图？

## BUG
	多余的方法
	数据库重构
	日志 切面 行号
	页面精简 摘要 关键点
		详情页多展示
	用户
		记忆
	RAG
		什么时候不需要
## 前端
	支持各种信息源：WEB 文件 音频 图片 脑图 微信社交
	通用异常封装
	通用返回封装
	浏览器端验证（如数量）
	shift回车发送
	[x] 远程css
	[x] 通用重定向 redirect问题
## 后端
    user 多用户租户 登录 支付 权限 管理
    memory
	点赞 复制 生成笔记
	cache
## LLM端
紧急 高优先级：
	简单
		1 检查目前代码里上下文的记忆窗口 不要太长
		2 带有多篇文档时，query模式下回答太简短，chat模式尚未测试
			top-2导致 2024-12-22 17:06:47,537 - base.py[line:395] - DEBUG: > Top 2 nodes:
		3 模型切换
		4 LLM先 生成如何学习一篇文章 的 提示词模板

	复杂
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

## Prompts/Few-shots
[问答集](Prompts.txt)



# 2 DONE
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