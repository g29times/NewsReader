# Main progress
- [x] Implement the Database Schema: Update the existing database model to include these new tables and fields.
- [x] Integrate LLM/VLM: Plan how to use LLMs to analyze articles and generate ideas.
- [x] Develop Collection Mechanism: Implement the mechanism for collecting articles from various sources, including manual input and APIs.
- [x] Design User Interface: Create a user-friendly interface for managing and exploring articles and ideas.

# 1 TODO
通用异常
通用返回
通用重定向

## 功能
紧急
	content移除
	仅URL
	垃圾箱 删除归档机制
	分类 筛选 聚合 归并
重要
	真伪需求辨别
		和笔记 课程 脑图打通
		源、记忆：我的笔记哪去了？
		写文章是真实需求吗？
		买相机 买无人机是真实需求吗？
		买课是真实需求吗？
		主观优先级是真实需求吗？
	反馈机制
	视觉激励机制 日历？点图？路径图？
	对话框
	系统设计参考discord
	各种信息源：微信 TODO 脑图 整合
已完成
	windsurf支持文件、联网

## Prompts/Few-shots
[问答集](Prompts.txt)

# 2 DOING
## Integrate LLM/VLM
### Implementation Steps
1. Select Libraries and Tools: Choose libraries for LLM/VLM integration, such as Hugging Face Transformers, OpenAI API, or PyTorch for local model hosting.
2. Develop Input Handlers: Create modules to handle different input types (text, vision, audio) and preprocess them for LLM/VLM processing.
    - Develop Functions: Implement these tasks as functions or services.
    - Integrate with Database: Ensure that the results are stored and updated in the database.
    - Schedule Tasks: Use a scheduler to handle periodic idea generation.
    3. *(Optional) Integrate Frameworks: Use frameworks like LangChain to build workflows that incorporate LLMs for complex tasks.
    4. *(Optional) Implement RAG Techniques: Develop methods to retrieve relevant data from your database to augment LLM outputs.
    5. *(Optional) Design Agents: Create agents that can autonomously perform tasks and interact with the system.
6. Frontend: HTML -> JS/CSS -> NextJs
    DONE: basic CURD
    TODO: 
        File support
        Relation
        Idea

# 3 DONE
- Decide on the specific LLMs/VLMs and APIs you want to use. - GEMINI
- Develop a prototype to test the integration of LLM/VLM capabilities. - DONE
- Create API Client Module: Implement a Python module to interact with the Gemini API.
- Secure API Key: Store the API key securely and update your application to retrieve it from a secure location.
- Develop Use Cases: Define specific use cases for Gemini, such as summarizing articles or generating new ideas.
- Test Integration: Develop test cases to ensure the integration works as expected.
- Develop Input Handlers: Implement handlers for different input types (text, vision, audio) to prepare data for processing by Gemini.
- Integrate with Database: Connect the API client to your database models to store generated ideas and insights.
