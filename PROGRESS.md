# Main progress
- [x] Implement the Database Schema: Update the existing database model to include these new tables and fields.
- [x] Integrate LLM/VLM: Plan how to use LLMs to analyze articles and generate ideas.
- [x] Develop Collection Mechanism: Implement the mechanism for collecting articles from various sources, including manual input and APIs.
- [x] Design User Interface: Create a user-friendly interface for managing and exploring articles and ideas.

# DONE
- Decide on the specific LLMs/VLMs and APIs you want to use. - GEMINI
- Develop a prototype to test the integration of LLM/VLM capabilities. - DONE
- Create API Client Module: Implement a Python module to interact with the Gemini API.
- Secure API Key: Store the API key securely and update your application to retrieve it from a secure location.
- Develop Use Cases: Define specific use cases for Gemini, such as summarizing articles or generating new ideas.
- Test Integration: Develop test cases to ensure the integration works as expected.
- Develop Input Handlers: Implement handlers for different input types (text, vision, audio) to prepare data for processing by Gemini.
- Integrate with Database: Connect the API client to your database models to store generated ideas and insights.

# Current progress
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

# TODO
## 功能
UI整合 todo 对话
系统设计参考discord
开发时支持copliot联网
## Prompts/Few-shots
- [ ] 问题：我想把室内设计的生成图片的质量粒度优化一下，有什么建议吗？ - 答：可以看看《ICML24 | VLM细粒度图文对齐：局部区域匹配优于整体图像》
- [ ] 问题：我想快速调用多个不同厂商的LLM，有什么办法吗？ - 答：可以看看《吴恩达开源大模型套件》
- [ ] 问题：业界有哪些产学研联动的成功案例？ - 答：可以看看《美团AutoConsis：UI内容一致性智能检测》
- [ ] 问题：我想做个电力系统的AI辅助文件勘误系统 - 答：可以看看《美团AutoConsis：UI内容一致性智能检测》
- [ ] 问题：大模型能为生产系统做哪些有实际商业价值的事？ - 答：可以看看《基于向量模型的文本水印技术》
