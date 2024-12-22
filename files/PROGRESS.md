# Main progress
- [x] Implement the Database Schema: Update the existing database model to include these new tables and fields.
- [x] Integrate LLM/VLM: Plan how to use LLMs to analyze articles and generate ideas.
- [x] Develop Collection Mechanism: Implement the mechanism for collecting articles from various sources, including manual input and APIs.
- [x] Design User Interface: Create a user-friendly interface for managing and exploring articles and ideas.

# 1 DEGISN/TODO
    File - Relation - Note - Idea
## 前端
	通用异常
	通用返回
	通用重定向
	浏览器端验证（如数量）
## 后端
    user 多用户 租户 登录 支付 权限 API
    cache
    memory
	点赞 复制 生成笔记
## LLM端
紧急 高优先级：
	简单
		回答太简短
		模型切换
		shift回车发送
	复杂
		合并解决：多轮次对话 聊天记录memory 用户意图
			https://ywctech.net/ml-ai/langchain-vs-llamaindex-rag-chat/
		重排 rerank
			https://mp.weixin.qq.com/s/XKTvd1jW4Y0AH9w-s2NLVA
			https://docs.llamaindex.ai/en/stable/examples/workflow/rag/
		评估 eval
			https://zhuanlan.zhihu.com/p/681532023 RAG Triad
			https://docs.llamaindex.ai/en/stable/module_guides/evaluating/
紧急 低优先级：
	简单
		提示3个问题
		重复问题识别
		垃圾箱 删除归档机制
		对话保存（持久化）
	复杂
		聊天记录后训练 DPO PPO RL
		Agent 人格设定 主动对话
			Autogen https://github.com/Chainlit/cookbook/tree/main/pyautogen
			https://docs.llamaindex.ai/en/stable/examples/chat_engine/chat_engine_personality/
重要
	需求辨别
		和笔记 课程 脑图打通
		源、记忆：我的笔记哪去了？
		写文章是真实需求吗？
		买相机 买无人机是真实需求吗？
		买课是真实需求吗？
		主观优先级是真实需求吗？
	用户反馈机制
	用户激励机制 视觉 日历？点图？路径图？
	系统设计参考discord
	各种信息源：微信 TODO 脑图 整合
	内容分类 筛选 聚合 归并
	第四格 - 生成笔记博客 灵感来源 - https://ywctech.net/ml-ai/langchain-vs-llamaindex-rag-chat/
	
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